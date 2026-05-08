# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from collective.contact.core.content.organization import IOrganization
from collective.contact.plonegroup.utils import get_own_organization
from collective.contact.widget.source import ContactSource
from collective.contact.widget.source import ContactSourceBinder
from plone.app.layout.navigation.interfaces import INavigationQueryBuilder
from plone.base.navigationroot import get_navigation_root
from plone.formwidget.contenttree.interfaces import IContentSource
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer
from zope.lifecycleevent.interfaces import IObjectMovedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent


@adapter(Interface, IContentSource)
@implementer(INavigationQueryBuilder)
class Plone6NavigationQueryBuilder(object):
    """Plone 6-compatible INavigationQueryBuilder for ContentSource.

    plone.formwidget.contenttree's QueryBuilder uses portal_properties
    which was removed in Plone 6. This minimal replacement just builds
    a path query from the navigation root.
    """

    def __init__(self, context, source):
        self.context = context
        self.source = source

    def __call__(self):
        root_path = get_navigation_root(self.context)
        return {'path': {'query': root_path, 'depth': 1}}


@adapter(IOrganization, IObjectMovedEvent)
def fix_organization_object_provides(org, event):
    """Fix object_provides catalog index for organizations on add/move.

    collective.contact.plonegroup's mark_organization calls
    reindexObject(idxs='object_provides') — a string, not a list — so
    set('object_provides') expands to individual characters and the index
    is never actually updated.  This subscriber fires after mark_organization
    (registration order) and does the proper reindex.
    """
    if IObjectRemovedEvent.providedBy(event):
        return
    org.reindexObject(idxs=['object_provides'])


class PMContactSource(ContactSource):
    """Returns organizations, except ones stored in PLONEGROUP_ORG."""

    def search(self, query, relations=None, limit=50):
        """Base selectable_filter do the job but do not query own_org,
           we append it at the beginning of the vocabulary."""
        if not query:
            # ContactSource.search passes SearchableText='' to the catalog when
            # query is empty.  ZCTextIndex treats empty SearchableText as "no
            # results" (not "all results"), so the catalog returns nothing.
            # Bypass super().search() for empty queries and hit the catalog
            # directly with just the selectable_filter criteria.
            catalog_query = self.selectable_filter.criteria.copy()
            catalog_query['sort_limit'] = limit
            results = [self.getTermByBrain(brain, real_value=False)
                       for brain in self.catalog(**catalog_query)[:limit]]
        else:
            results = [term for term in super(PMContactSource, self).search(query, relations, limit)]
        brains = self.catalog(UID=get_own_organization().UID())
        results.insert(0, self.getTermByBrain(brains[0], real_value=False))
        return results


class PMContactSourceBinder(ContactSourceBinder):
    """Returns organizations, except ones stored in PLONEGROUP_ORG."""
    path_source = PMContactSource

    def __init__(self, navigation_tree_query=None, default=None, defaultFactory=None, **kw):
        super(PMContactSourceBinder, self).__init__(navigation_tree_query, default, defaultFactory, **kw)
        self.selectable_filter.criteria = {
            'portal_type': ('organization', ),
            'object_provides': ['collective.contact.plonegroup.interfaces.INotPloneGroupContact']}
