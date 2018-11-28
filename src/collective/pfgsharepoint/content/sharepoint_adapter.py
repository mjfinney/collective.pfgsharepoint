import requests
from AccessControl import ClassSecurityInfo
from Products.ATContentTypes.content.base import registerATCT
from Products.Archetypes import atapi
from Products.CMFCore import utils as cmf_utils
from Products.CMFCore.permissions import ModifyPortalContent
from Products.PloneFormGen.content.actionAdapter import FormActionAdapter
from Products.PloneFormGen.content.actionAdapter import FormAdapterSchema
from collective.pfgsharepoint import PROJECTNAME

from Products.DataGridField.DataGridField import DataGridField
from Products.DataGridField.DataGridWidget import DataGridWidget
from Products.DataGridField.Column import Column
from Products.DataGridField.SelectColumn import SelectColumn

from plone.api.portal import get_registry_record
from collective.pfgsharepoint.interfaces import IPFGSharePointConfig

from msgraph.client import Client
from msgraph.sharepoint import Sharepoint

SharePointAdapterSchema = FormAdapterSchema.copy() + atapi.Schema((
    atapi.StringField('sharepoint_tenant',
                      required=True,
                      write_permission=ModifyPortalContent,
                      read_permission=ModifyPortalContent,
                      vocabulary_factory="collective.pfgsharepoint.vocabularies.SharepointTenants",
                      widget=atapi.SelectionWidget(
                          label=u'SharePoint Tenant',
                      )),
    atapi.StringField('sharepoint_site',
                      required=False,
                      write_permission=ModifyPortalContent,
                      read_permission=ModifyPortalContent,
                      vocabulary='getSites',
                      widget=atapi.SelectionWidget(
                          label=u'SharePoint Site ID',
                      )),
    atapi.StringField('sharepoint_list',
                      required=False,
                      write_permission=ModifyPortalContent,
                      read_permission=ModifyPortalContent,
                      vocabulary='getLists',
                      widget=atapi.SelectionWidget(
                          label=u'SharePoint List ID',
                      )),
    DataGridField(
        name='field_map',
        widget=DataGridWidget(
            label=u'Field Map',
            description=u"Map the PFG field to the Sharepoint list column.",
            columns={
                'pfg_field': SelectColumn(u'PFG Field',
                                          vocabulary='fgFieldsDisplayList',),
                'sharepoint_column': SelectColumn(u'Sharepoint Column',
                                                  vocabulary='getColumns'),
                },
            ),
        allow_empty_rows=False,
        required=False,
        columns=('pfg_field', 'sharepoint_column'),
    ),

))


class SharePointAdapter(FormActionAdapter):
    """ """

    schema = SharePointAdapterSchema
    portal_type = meta_type = 'SharePointAdapter'
    archetype_name = 'SharePoint Adapter'

    def getSharepoint(self):
        clientid = get_registry_record(interface=IPFGSharePointConfig,
                                       name='clientid')
        clientsecret = get_registry_record(interface=IPFGSharePointConfig,
                                           name='clientsecret')
        tenantid = self.getSharepoint_tenant()
        if tenantid:
            client = Client(clientid, tenantid, clientsecret)
            return Sharepoint(client)
        else:
            return None

    def getSharepointSite(self):
        sharepoint = self.getSharepoint()
        if not sharepoint:
            return None
        return sharepoint.getSiteById(self.getSharepoint_site())

    def getSharepointList(self):
        site = self.getSharepointSite()
        sharepoint_list = self.getSharepoint_list()
        if not sharepoint_list or not site:
            return None
        return site.getListById((sharepoint_list))


    def getSites(self):
        """return List of sites"""
        sitelist = []

        sharepoint = self.getSharepoint()
        if sharepoint:
            for site in sharepoint.getSitesList():
                sitelist.append((site.siteId, site.displayName + ' ' + site.webUrl))

        sitelist.sort(key=lambda x: x[1])
        return atapi.DisplayList(sitelist)

    def getLists(self):
        """return List of Lists"""
        sharepoint = self.getSharepoint()
        list_o_lists = []
        if sharepoint:
            site = self.getSharepointSite()
            for l in site.getLists():
                list_o_lists.append((l.id, l.displayName + ' ' + l.webUrl ))
        return atapi.DisplayList(list_o_lists)

    def getColumns(self):
        """Return list of columns"""
        target_list = self.getSharepointList()
        columns = []
        if not target_list:
            return []
        for col in target_list.getColumns():
            columns.append((col.id, col.displayName))
        return atapi.DisplayList(columns)



    security = ClassSecurityInfo()

    security.declarePrivate('onSuccess')
    def onSuccess(self, fields, REQUEST=None):
        clientid = get_registry_record(interface=IPFGSharePointConfig, name='clientid')
        clientsecret = get_registry_record(interface=IPFGSharePointConfig, name='clientsecret')
        tenants = get_registry_record(interface=IPFGSharePointConfig, name='tenants')
        client = Client(clientid, teanantid, clientsecret)
        if REQUEST is None:
            REQUEST = self.REQUEST
        email = REQUEST.form.get(self.email_field, '')
        if self.sharepoint_list:
            newsletters = self.subscriptions
        else:
            newsletters = REQUEST.form.get(self.newsletters_field, '')
        #api_key = pprops.tpwd_properties.govdelivery_api_key
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

registerATCT(SharePointAdapter, PROJECTNAME)
