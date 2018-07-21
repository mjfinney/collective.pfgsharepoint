import requests
from AccessControl import ClassSecurityInfo
from Products.ATContentTypes.content.base import registerATCT
from Products.Archetypes import atapi
from Products.CMFCore import utils as cmf_utils
from Products.CMFCore.permissions import ModifyPortalContent
from Products.PloneFormGen.content.actionAdapter import FormActionAdapter
from Products.PloneFormGen.content.actionAdapter import FormAdapterSchema

from plone.api.portal import get_registry_record
from collective.pfgsharepoint.interfaces import IPFGSharePointConfig

SharePointAdapterSchema = FormAdapterSchema.copy() + atapi.Schema((
    atapi.StringField('sharepoint_site',
                      required=True,
                      write_permission=ModifyPortalContent,
                      read_permission=ModifyPortalContent,
                      widget=atapi.LinesWidget(
                          label=u'SharePoint Site ID',
                          description=(u'You can use the graph api explorer to get the id. Go to https://developer.microsoft.com/en-us/graph/graph-explorer'
                              u' and run this query and replace {HOST} and {PATH TO SITE} with the path to the sharepoint site: https://graph.microsoft.com/v1.0/sites/{HOST}:/sites/{PATH TO SITE}/?$select=id')
                      )),
    atapi.StringField('sharepoint_list',
                      required=True,
                      write_permission=ModifyPortalContent,
                      read_permission=ModifyPortalContent,
                      widget=atapi.LinesWidget(
                          label=u'SharePoint List ID',
                          description=(u'Use the graph api to get the ID of the list using {ID} of the site. https://graph.microsoft.com/v1.0/sites/{ID}/lists/'
                                       u'Only use this in a form that is specifically for signing up to an email list.')
                      )),

))


class SharePointAdapter(FormActionAdapter):
    """ """

    schema = SharePointAdapterSchema
    portal_type = meta_type = 'SharePointAdapter'
    archetype_name = 'SharePoint Adapter'

    security = ClassSecurityInfo()

    security.declarePrivate('onSuccess')
    def onSuccess(self, fields, REQUEST=None):
        domain = get_registry_record(interface=IPFGSharePointConfig, name='domain')
        token = get_registry_record(interface=IPFGSharePointConfig, name='token')
        if REQUEST is None:
            REQUEST = self.REQUEST
        email = REQUEST.form.get(self.email_field, '')
        if self.sharepoint_list:
            newsletters = self.subscriptions
        else:
            newsletters = REQUEST.form.get(self.newsletters_field, '')
        api_key = pprops.tpwd_properties.govdelivery_api_key
        if not token:
            raise ValueError('The SharePoint token is not set.')
        if not self.sharepoint_list:
            raise ValueError('The SharePoint list is not set.')
        if not self.sharepoint_site:
            raise ValueError('The SharePoint site is not set.')

        api_version = 'v1.0'
        base_url = 'https://graph.microsoft.com/' + api_version + '/sites/'
        url = '%s?k=%s&e=%s' % (base_url, api_key, email)
        headers={'Authorization': 'Bearer ' + token}
        resp = requests.get(url, headers=headers, timeout=2)
        resp.raise_for_status()

registerATCT(SharePointAdapter, 'collective.pfgsharepoint')
