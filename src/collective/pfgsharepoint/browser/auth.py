from Products.Five import BrowserView
from plone.api import portal

from collective.pfgsharepoint.interfaces import IPFGSharePointConfig


class SharePointAuthView(BrowserView):

    def __call__(self):
        tenant = self.request.form.get('tenant')
        tenant = unicode(tenant)
        consent = self.request.form.get('admin_consent')
        if tenant and consent and consent.lower() == "true":
            #tenant is GUID
            tenants = portal.get_registry_record(interface=IPFGSharePointConfig, name='tenants')
            if not tenants:
                tenants = {}
            if tenant not in tenants:
                tenants[tenant] = {}
                tenants[tenant][u'token'] = u''
                portal.set_registry_record(interface=IPFGSharePointConfig, name='tenants', value=tenants)
        return self.index()


    def getAuthUrl(self):
        portal_url = portal.get().absolute_url()
        clientid = portal.get_registry_record(interface=IPFGSharePointConfig, name='clientid')
        auth_url = "https://login.microsoftonline.com/common"
        auth_url += '/adminconsent?client_id=' + clientid
        auth_url += '&redirect_uri=' + portal_url + '/@@sharepoint-permissions'
        return auth_url
