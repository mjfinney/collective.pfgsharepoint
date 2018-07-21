from Products.Five.browser import BrowserView
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
from plone.app.registry.browser import controlpanel

from collective.pfgsharepoint.interfaces import IPFGSharePointConfig
from collective.pfgsharepoint import _

#try:
    # only in z3c.form 2.0
#    from z3c.form.browser.textlines import TextLinesFieldWidget
#except ImportError:
#    from plone.z3cform.textlines import TextLinesFieldWidget

class PFGSharePointConfigForm(controlpanel.RegistryEditForm):
    schema = IPFGSharePointConfig
    label = _(u"PFG SharePoint Settings")
    description = _(u"Use the settings below to configure the PFG SharePoint Adapter")

    def updateFields(self):
        super(PFGSharePointConfigForm, self).updateFields()

class PFGSharePointConfigControlPanel(controlpanel.ControlPanelFormWrapper):
    form = PFGSharePointConfigForm
