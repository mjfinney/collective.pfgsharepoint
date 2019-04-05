from datetime import datetime
import logging
import re
from urllib import quote_plus

import requests

from AccessControl import ClassSecurityInfo
from Products.ATContentTypes.content.base import registerATCT
from Products.Archetypes import atapi
from Products.Archetypes.utils import shasattr
from Products.CMFCore.permissions import ModifyPortalContent
from Products.PloneFormGen.config import FORM_ERROR_MARKER, EDIT_TALES_PERMISSION
from Products.PloneFormGen.content.actionAdapter import FormActionAdapter
from Products.PloneFormGen.content.actionAdapter import FormAdapterSchema
from Products.TALESField import TALESString
from Products.DataGridField.DataGridField import DataGridField
from Products.DataGridField.DataGridWidget import DataGridWidget
from Products.DataGridField.Column import Column
from Products.DataGridField.SelectColumn import SelectColumn
from plone.api.portal import get_registry_record
from zope.annotation.interfaces import IAnnotations

from msgraph.client import Client
from msgraph.sharepoint import (Sharepoint,
                                SharepointDateTimeColumn,
                                SharepointChoiceColumn,)
from msgraph.drives import Drive

from collective.pfgsharepoint import _
from collective.pfgsharepoint import PROJECTNAME
from collective.pfgsharepoint.interfaces import IPFGSharePointConfig

logger = logging.getLogger('collective.pfgsharepoint')

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
    atapi.StringField('sharepoint_drive',
                      required=False,
                      write_permission=ModifyPortalContent,
                      read_permission=ModifyPortalContent,
                      vocabulary='getDrives',
                      widget=atapi.SelectionWidget(
                          label=u'SharePoint Document Library AKA Drive ID',
                          description=u'This is where an XML document will be uploaded using the XML Form Template.',
                      )),
    atapi.StringField('filename_string',
                      required=False,
                      write_permission=ModifyPortalContent,
                      read_permission=ModifyPortalContent,
                      widget=atapi.StringWidget(
                          label=u'Filename Format String',
                          description=u'The name the xml fromt template will be uploaded as. \
                                        The form fields are available using the python string format e.g. {field-id} \
                                        Use {now} for the submission datetime.',
                      )),
    atapi.TextField('xml_template',
                      required=False,
                      write_permission=ModifyPortalContent,
                      read_permission=ModifyPortalContent,
                      widget=atapi.TextAreaWidget(
                          label=u'XML Form Template',
                          description=u'This is only used with the Document Library.',
                      )),
    TALESString('formatScript',
        schemata='overrides',
        searchable=0,
        required=0,
        validators=('talesvalidator', ),
        write_permission=EDIT_TALES_PERMISSION,
        default='',
        isMetadata=True,
        languageIndependent=1,
        widget=atapi.StringWidget(label=_(u'label_BeforeAdapterOverride_text',
                                    default=u"Before Adapter Script"),
            description=_(u'help_BeforeAdapterOverride_text', default=\
                u"A TALES expression that will be called before this adapter runs. "
                "Form input will be in the request.form dictionary. "
                "Leave empty if unneeded. "
                "The most common use of this field is to call a python script "
                "to clean up form input. "
                "If the return value is None then the adapter will use request.form "
                "If the return value is a dictionary then the adapter will use the "
                "returned dictionary. "
                "PLEASE NOTE: errors in the evaluation of this expression will "
                "cause an error on form display."),
            size=70,
            ),
        ),
    DataGridField(
        name='field_map',
        widget=DataGridWidget(
            label=u'Field Map',
            description=u"Map the PFG field to the Sharepoint list column.",
            columns={
                'pfg_field': SelectColumn(u'PFG Field',
                                          vocabulary='fgFieldsDisplayList',),
                'sharepoint_column': SelectColumn(u'Sharepoint Column',
                                                  vocabulary='getColumnsVocab'),
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

    def __bobo_traverse__(self, REQUEST, name):
        # prevent traversal to attributes we want to protect
        if name == 'formatScript':
            raise AttributeError
        return super(SharePointAdapter, self).__bobo_traverse__(REQUEST, name)

    def getCacheKey(self, key):
        key = "sharepoint-" + key + self.UID()

        cache = IAnnotations(self.REQUEST)
        return (cache, key, cache.get(key, None))

    def getSharepoint(self):
        cache, key, data = self.getCacheKey('sharepoint')
        if not data:
            clientid = get_registry_record(interface=IPFGSharePointConfig,
                                           name='clientid')
            clientsecret = get_registry_record(interface=IPFGSharePointConfig,
                                               name='clientsecret')
            tenantid = self.getSharepoint_tenant()
            if tenantid:
                client = Client(clientid, tenantid, clientsecret)
                data = Sharepoint(client)
            else:
                data = None
            cache[key] = data
        return data

    def getSharepointSite(self):
        cache, key, data = self.getCacheKey('site')
        if not data:
            sharepoint = self.getSharepoint()
            if not sharepoint:
                return None

            data = sharepoint.getSiteById(self.getSharepoint_site())
            cache[key] = data
        return data

    def getSharepointList(self):
        cache, key, data = self.getCacheKey('list')
        if not data:
            site = self.getSharepointSite()
            sharepoint_list = self.getSharepoint_list()
            if not sharepoint_list or not site:
                return None
            data = site.getListById((sharepoint_list))
            cache[key] = data
        return data

    def getSites(self):
        """return List of sites"""
        cache, key, data = self.getCacheKey('site-list')
        if not data:
            sitelist = []

            sharepoint = self.getSharepoint()
            if sharepoint:
                for site in sharepoint.getSitesList():
                    sitelist.append((site.siteId, site.displayName + ' ' + site.webUrl))

            sitelist.sort(key=lambda x: x[1])
            data = atapi.DisplayList(sitelist)
            cache[key] = data
        return data

    def getLists(self):
        """return List of Lists"""
        cache, key, data = self.getCacheKey('list-list')
        if not data:
            sharepoint = self.getSharepoint()
            list_o_lists = [('', 'None'),]
            if sharepoint:
                site = self.getSharepointSite()
                if site:
                    for l in site.getLists():
                        list_o_lists.append((l.id, l.displayName + ' ' + l.webUrl ))
            data = atapi.DisplayList(list_o_lists)
            cache[key] = data
        return data

    def getDrives(self):
        """return List of Drives"""
        cache, key, data = self.getCacheKey('drive-list')
        if not data:
            sharepoint = self.getSharepoint()
            list_o_drives = [('', 'None'),]
            if sharepoint:
                site = self.getSharepointSite()
                if site:
                    for d in site.getDrives():
                        list_o_drives.append((d.id, d.name + ' ' + d.webUrl ))
            data = atapi.DisplayList(list_o_drives)
            cache[key] = data
        return data

    def getColumns(self):
        """Return list of columns"""
        cache, key, data = self.getCacheKey('column-list')
        if not data:
            target_list = self.getSharepointList()
            if target_list:
                data = target_list.getColumns()

            cache[key] = data
        return data

    def getColumnsVocab(self):
        """Return list of columns"""
        cache, key, data = self.getCacheKey('column-vocab')
        if not data:
            columns_list = self.getColumns()
            columns = [('', 'None'),]
            if columns_list:
                for col in columns_list:
                    columns.append((col.id, col.displayName))
            data = atapi.DisplayList(columns)
            cache[key] = data
        return data

    def getXMLVariables(self):
        """Return list of XML Template Variables"""
        cache, key, data = self.getCacheKey('xml-vars')
        if not data:
            variables = [('', 'None'),]
            if self.xml_template:
                matches = re.findall(r'\{(.*)\}', self.getXml_template())
                matches = [(x, x) for x in matches]
                variables = variables + matches

            data = atapi.DisplayList(variables)
            cache[key] = data
        return data

    def getSharepointColFromMap(self, pfg_field):
        """return the sharepoint column id
           from the pfg id
        """

        for x in self.field_map:
            if x.get('pfg_field') == pfg_field:
                return x.get('sharepoint_column')



    security = ClassSecurityInfo()

    security.declarePrivate('onSuccess')
    def onSuccess(self, fields, REQUEST=None):
        if REQUEST is None:
            REQUEST = self.REQUEST

        if shasattr(self, 'formatScript') and self.getRawFormatScript():
            # formatScript has a TALES override
            form = self.getFormatScript()
        else:
            form = REQUEST.form

        field_map = self.getField_map()
        #template = self.getRawXml_template()
        #drive = self.getSharepoint_drive()
        sharepoint = self.getSharepoint()

        #if template and drive:
        #    xml_vars = {}
        #    for x in field_map:
        #        wrapper = x.get('xml_wrapper')
        #        if wrapper:
        #            to_wrap = form.get(x['pfg_field'])
        #            wrapped = ''
        #            for value in to_wrap:
        #                wrapped += '<{wrapper}>{value}</{wrapper}>'.format(wrapper=wrapper, value=value)
        #            xml_vars[x['xml_variable']] = wrapped
        #        else:
        #            xml_vars[x['xml_variable']] = form.get(x['pfg_field'])

        #    formatted = template.format(**xml_vars)
        #    drive = Drive(id=drive, client=sharepoint.client)
        #    now = datetime.now().strftime('%y-%m-%d-%H-%M-%S-%f')
        #    filename = self.getFilename_string().format(now=now, **form)
        #    filename = filename.replace(':', '-')
        #    filename = quote_plus(filename)
        #    response = drive.upload(filename, formatted)
        #    if not response.ok:
        #        return {FORM_ERROR_MARKER: 'Something went wrong. You will need to try to submit again or correct any errors below.'}


        target_list = self.getSharepointList()

        if target_list:
            columns = self.getColumns()
            columns = dict(zip(map(lambda x: x.id,columns),columns))
            col_lookup = dict(zip(map(lambda x: x.get('pfg_field'),field_map),field_map))
            cols = {}
            now = datetime.now().strftime('%y-%m-%d-%H-%M-%S-%f')
            cols['Title'] = self.getFilename_string().format(now=now, **form)
            for x in fields:
                col = col_lookup.get(x.id)
                if col:
                    sharepoint_column = columns.get(col.get('sharepoint_column'))
                    if isinstance(sharepoint_column, SharepointChoiceColumn):
                        form_value = form.get(x.id)
                        cols[sharepoint_column.name + '@odata.type'] = 'Collection(Edm.String)'
                    elif isinstance(sharepoint_column, SharepointDateTimeColumn):
                        form_value = form.get(x.id)
                        formats = ['%Y-%m-%d %H:%M',
                                   '%m/%d/%Y',
                                   '%m/%d/%Y %I:%M %p',
                                   ]
                        if form_value:
                            for f in formats:
                                try:
                                    form_value = datetime.strptime(form_value, f)
                                except ValueError:
                                    pass
                                else:
                                    break
                            try:
                                form_value = form_value.isoformat()
                            except AttributeError:
                                logger.error("Attribute error with field: %s with value: %s", x, form_value)
                                raise
                    else:
                        form_value = x.htmlValue(REQUEST)
                    if form_value:
                        cols[sharepoint_column.name] = form_value
            response = target_list.createItem(fields=cols)


registerATCT(SharePointAdapter, PROJECTNAME)
