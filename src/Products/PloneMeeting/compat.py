# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from operator import itemgetter


class DisplayList(object):
    """Lightweight replacement for Products.Archetypes.utils.DisplayList.

    Stores an ordered list of (key, value) pairs with dict-like lookup
    and sorting helpers.  Used throughout MeetingConfig vocabulary methods.
    """

    def __init__(self, data=()):
        self._keys = []
        self._values = []
        self._lookup = {}
        for k, v in data:
            self._keys.append(k)
            self._values.append(v)
            self._lookup[k] = v

    def add(self, key, value):
        self._keys.append(key)
        self._values.append(value)
        self._lookup[key] = value

    def getValue(self, key, default=None):
        return self._lookup.get(key, default)

    def keys(self):
        return list(self._keys)

    def values(self):
        return list(self._values)

    def items(self):
        return list(zip(self._keys, self._values))

    def sortedByValue(self):
        return DisplayList(sorted(zip(self._keys, self._values), key=itemgetter(1)))

    def sortedByKey(self):
        return DisplayList(sorted(zip(self._keys, self._values), key=itemgetter(0)))

    def __add__(self, other):
        return DisplayList(self.items() + other.items())

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return len(self._keys)

    def __contains__(self, key):
        return key in self._lookup

    def __repr__(self):
        return 'DisplayList({!r})'.format(self.items())


class IntDisplayList(DisplayList):
    """DisplayList variant with integer keys."""
    pass
