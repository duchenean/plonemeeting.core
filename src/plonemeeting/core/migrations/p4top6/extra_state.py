# -*- coding: utf-8 -*-
"""JSON codec for the PloneMeeting state that lives outside the schemas.

collective.exportimport serializes schema fields, workflow history and
a few standard extras. PloneMeeting also keeps state in plain persistent
attributes (adviceIndex, attendees, votes, imio.history histories...)
and in annotations (ftw.labels, "sent to other config" markers). This
module dumps that state to a JSON-safe structure on the Plone 4.3 side
and loads it back on the Plone 6.1 side.

The module runs on Python 2.7 (export, copied next to export_p43.py)
and on Python 3.12 (import). Keep it free of any PloneMeeting import.
"""

from __future__ import absolute_import
from __future__ import print_function

import datetime
import decimal
import logging

from collections import OrderedDict

from Acquisition import aq_base
from DateTime import DateTime
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from zope.annotation.interfaces import IAnnotations

logger = logging.getLogger("plonemeeting.core: p4top6 extra state")

try:
    text_type = unicode  # noqa: F821
    binary_type = str
except NameError:
    text_type = str
    binary_type = bytes

# Key of the extra state inside the collective.exportimport item dict.
EXTRA_STATE_KEY = "pm_extra_state"
TYPE_KEY = "__pm_type__"

# Persistent attributes that are not schema fields, per content family.
# Caches are left out: _labels_access_cache, _insert_order_cache and
# categorized_elements are rebuilt on the Plone 6.1 side.
ITEM_ATTRS = (
    "adviceIndex",
    "takenOverByInfos",
    "itemHistory",
    "autoCopyGroups",
    "autoRestrictedCopyGroups",
    "emergency_changes_history",
    "completeness_changes_history",
    "linked_predecessor_uid",
    "linked_successor_uids",
)

# Mirror of plonemeeting.core.config.MEETING_ATTENDEES_ATTRS, hardcoded
# so the export side has no PloneMeeting dependency.
MEETING_ATTRS = (
    "item_absents",
    "item_excused",
    "item_non_attendees",
    "item_signatories",
    "item_attendees_positions",
    "item_attendees_order",
    "item_votes",
    "ordered_contacts",
    "_number_of_items",
)

ADVICE_ATTRS = (
    "advice_row_id",
    "advice_given_history",
    "advice_hide_during_redaction_history",
)

# Annotation keys carried over: exact keys and key prefixes.
ANNOTATION_KEYS = (
    "ftw.labels:labeling",
)
ANNOTATION_KEY_PREFIXES = (
    "PloneMeeting-sent_to_other_meetingconfig_",
)


def attrs_for_portal_type(portal_type):
    """Return the extra attribute names for p_portal_type.
       Per-config types are cloned FTIs: MeetingItemPma, MeetingPma,
       meetingadvicefinances..."""
    if portal_type.startswith("MeetingItem"):
        return ITEM_ATTRS
    if portal_type.startswith("meetingadvice"):
        return ADVICE_ATTRS
    if portal_type.startswith("Meeting") and portal_type != "MeetingConfig":
        return MEETING_ATTRS
    return ()


def _is_exported_annotation(key):
    if key in ANNOTATION_KEYS:
        return True
    for prefix in ANNOTATION_KEY_PREFIXES:
        if key.startswith(prefix):
            return True
    return False


def _tagged(type_name, **kwargs):
    res = {TYPE_KEY: type_name}
    res.update(kwargs)
    return res


def _text(value):
    if isinstance(value, binary_type):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            logger.warning("Non UTF-8 bytes replaced: %r", value[:40])
            return value.decode("utf-8", "replace")
    return value


def encode(value):
    """Turn p_value into a JSON-safe structure that records the
       container and date types so decode() can restore them."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, (text_type, binary_type)):
        return _text(value)
    if isinstance(value, DateTime):
        return _tagged("DateTime",
                       value=value.ISO8601(),
                       ts=value.timeTime(),
                       tz=value.timezone())
    if isinstance(value, datetime.datetime):
        return _tagged("datetime", value=value.isoformat())
    if isinstance(value, datetime.date):
        return _tagged("date", value=value.isoformat())
    if isinstance(value, (PersistentMapping, OrderedDict, dict)):
        if isinstance(value, PersistentMapping):
            type_name = "PersistentMapping"
        elif isinstance(value, OrderedDict):
            type_name = "OrderedDict"
        else:
            type_name = "dict"
        return _tagged(type_name,
                       items=[[encode(k), encode(v)] for k, v in value.items()])
    if isinstance(value, (PersistentList, list)):
        res = [encode(v) for v in value]
        if isinstance(value, PersistentList):
            return _tagged("PersistentList", items=res)
        return res
    if isinstance(value, tuple):
        return _tagged("tuple", items=[encode(v) for v in value])
    if isinstance(value, (set, frozenset)):
        return _tagged("set", items=[encode(v) for v in value])
    logger.warning("Unsupported value of type %s not exported: %r",
                   type(value).__name__, value)
    return _tagged("unsupported", repr=repr(value))


def _parse_datetime(text):
    if hasattr(datetime.datetime, "fromisoformat"):
        return datetime.datetime.fromisoformat(text)
    if "." in text:
        return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%f")
    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%S")


def decode(value):
    """Inverse of encode()."""
    if isinstance(value, decimal.Decimal):
        # the JSON reader of collective.exportimport is simplejson, it
        # reads every JSON float as a Decimal
        return float(value)
    if isinstance(value, list):
        return [decode(v) for v in value]
    if not isinstance(value, dict):
        return value
    type_name = value.get(TYPE_KEY)
    if type_name is None:
        # a plain JSON object never comes out of encode(); keep it
        return dict((k, decode(v)) for k, v in value.items())
    if type_name == "DateTime":
        if "ts" in value:
            return DateTime(float(value["ts"])).toZone(value["tz"])
        return DateTime(value["value"])
    if type_name == "datetime":
        return _parse_datetime(value["value"])
    if type_name == "date":
        return datetime.datetime.strptime(value["value"], "%Y-%m-%d").date()
    if type_name in ("PersistentMapping", "OrderedDict", "dict"):
        pairs = [(decode(k), decode(v)) for k, v in value["items"]]
        if type_name == "PersistentMapping":
            res = PersistentMapping()
            for k, v in pairs:
                res[k] = v
            return res
        if type_name == "OrderedDict":
            return OrderedDict(pairs)
        return dict(pairs)
    if type_name == "PersistentList":
        return PersistentList([decode(v) for v in value["items"]])
    if type_name == "tuple":
        return tuple(decode(v) for v in value["items"])
    if type_name == "set":
        return set(decode(v) for v in value["items"])
    if type_name == "unsupported":
        logger.warning("Unsupported exported value skipped: %s", value.get("repr"))
        return None
    raise ValueError("Unknown extra state type %r" % type_name)


def dump_extra_state(obj):
    """Return the extra state of p_obj as a JSON-safe dict:
       {"attributes": {name: encoded}, "annotations": {key: encoded}}.
       Only attributes stored on the object itself are exported."""
    base = aq_base(obj)
    attributes = {}
    for name in attrs_for_portal_type(getattr(base, "portal_type", "")):
        if name in base.__dict__:
            attributes[name] = encode(base.__dict__[name])
    annotations = {}
    try:
        ann = IAnnotations(obj)
    except TypeError:
        ann = {}
    for key in list(ann.keys()):
        if _is_exported_annotation(key):
            annotations[_text(key)] = encode(ann[key])
    return {"attributes": attributes, "annotations": annotations}


def load_extra_state(obj, state):
    """Restore on p_obj the state produced by dump_extra_state()."""
    if not state:
        return
    for name, value in state.get("attributes", {}).items():
        setattr(obj, str(name), decode(value))
    annotations = state.get("annotations", {})
    if annotations:
        ann = IAnnotations(obj)
        for key, value in annotations.items():
            ann[str(key)] = decode(value)
