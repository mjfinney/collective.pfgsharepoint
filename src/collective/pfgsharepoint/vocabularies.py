""" Catalog specific vocabularies
"""
import operator
from binascii import b2a_qp
from eea.faceted.vocabularies.utils import compare
from eea.faceted.vocabularies.utils import IVocabularyFactory
from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from zope.site.hooks import getSite
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from plone.api.portal import get_registry_record

import datetime

from collective.pfgsharepoint.interfaces import IPFGSharePointConfig

from msgraph.client import Client


class SharepointTenantVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context, query=None):
        tenants = get_registry_record(interface=IPFGSharePointConfig, name="tenants")
        tenants = [SimpleTerm(t, t, props.get('displayName', t)) for t,props in tenants.items()]
        return SimpleVocabulary(tenants)

SharepointTenantVocabularyFactory = SharepointTenantVocabulary()
