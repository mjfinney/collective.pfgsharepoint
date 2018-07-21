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

    domain = schema.TextLine(title=_(u"SharePoint Domain"),
                         description=_(u'This is something like "company.sharepoint.com"'),
                         required=False,
                         )

    token = schema.TextLine(title=_(u"Microsoft Graph API Token"),
                        description=_(u'This is created once the app is allowed access to SharePoint.'),
                        required=False,
                        )
