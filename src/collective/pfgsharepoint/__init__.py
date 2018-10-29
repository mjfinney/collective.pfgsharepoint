# -*- coding: utf-8 -*-
"""Init and utils."""
from zope.i18nmessageid import MessageFactory

from Products.Archetypes import atapi
from Products.CMFCore import utils as cmf_utils
from Products.CMFCore.permissions import AddPortalContent
from Products.PloneFormGen.config import ADD_CONTENT_PERMISSION


_ = MessageFactory('collective.pfgsharepoint')

PROJECTNAME = 'collective.pfgsharepoint'

def initialize(context):
    import content.sharepoint_adapter
    listOfTypes = atapi.listTypes(PROJECTNAME)
    content_types, constructors, ftis = atapi.process_types(listOfTypes, PROJECTNAME)
    for atype, constructor in zip(content_types, constructors):
        if atype.portal_type == 'SharePointAdapter':
            permission = ADD_CONTENT_PERMISSION
        else:
            permission = AddPortalContent
        cmf_utils.ContentInit(
            '%s: %s' % (PROJECTNAME, atype.portal_type),
            content_types=(atype,),
            permission=permission,
            extra_constructors=(constructor,)
        ).initialize(context)
