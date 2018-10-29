# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from collective.pfgsharepoint import _


class ICollectivePfgsharepointLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""

class IPFGSharePointConfig(Interface):
    """Interface to configure the collective.pfgsharepoint
    """

    clientid = schema.TextLine(title=_(u"Microsoft App Client ID"),
                           description=_(u'Register app with Microsoft and get a Client ID here: https://apps.dev.microsoft.com/.'),
                           required=False,
                           )

    clientsecret = schema.Password(title=_(u"Microsoft App Client Secret"),
                           description=_(u'You can generate a new password here: https://apps.dev.microsoft.com/.'),
                           required=False,
                           )

    tenants = schema.Dict(title=_(u"SharePoint Tenants"),
                          description=_(u"This setting should only be modified by visiting the @@sharepoint-permissions page"),
                          required=False,
                          key_type=schema.TextLine(title=_(u"Tenant GUID")),
                          value_type=schema.Dict(title=_("Tenant Properties"),
                                                 key_type=schema.TextLine(title=_(u"Tenant Property")),
                                                 value_type=schema.TextLine(title=_(u"Tenant Property Value"), required=False),
                                                 ),
                          )
