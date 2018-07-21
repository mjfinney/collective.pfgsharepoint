from Products.Five import BrowserView
from plone.api import portal

from collective.pfgsharepoint.interfaces import IPFGSharePointConfig


class SharePointAuthView(BrowserView):

    def getAuthUrl():
        portal_url = portal.get().absolute_url()
        tenant = get_registry_record(interface=IPFGSharePointConfig, name='domain')
        clientid = get_registry_record(interface=IPFGSharePointConfig, name='clientid')
        auth_url = "https://login.microsoftonline.com/"
        auth_url +=  tenant
        auth_url += '/adminconsent?client_id=' + clientid
        auth_url += '&redirect_uri=' + portal_url + '/@@sharepoint-auth'
        return auth_url

    def getAuthToken():
        portal.set_registry_record(value='', interface=IPFGSharePointConfig, name="domain")
        return ''
