from plone.api.portal import get_registry_record

from plone.memoize import ram
from time import time

from msgraph.client import Client

from collective.pfgsharepoint.interfaces import IPFGSharePointConfig

@ram.cache(lambda func, tenantid: tenantid + str(time() // (60 * 30)))
def getClient(tenantid):
        clientid = get_registry_record(interface=IPFGSharePointConfig,
                                       name='clientid')
        clientsecret = get_registry_record(interface=IPFGSharePointConfig,
                                           name='clientsecret')
        return Client(clientid, tenantid, clientsecret)
