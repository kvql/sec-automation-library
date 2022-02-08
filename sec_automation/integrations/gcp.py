from google.cloud import securitycenter
import json
import time
import logging
import os
from google.cloud import dns
from google.protobuf.json_format import MessageToDict
from google.cloud import resource_manager
from sec_automation.functions import is_ipv4, validate_dns
# reference: https://github.com/googleapis/google-cloud-python/issues/3485
import sec_automation.configmanager as cm
import logging
from sys import exit
import ipaddress 
from copy import deepcopy

logger= logging.getLogger(__name__)
config_header="gcp"


#######################
# Supporting Functions
#######################

def set_auth(config_header):
    config = cm.load_config(config_header)
    home = os.path.expanduser("~")
    keyset = False
    if "key_path" in config:
        if config["key_path"] != "" and type(config["key_path"]) != dict:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config['key_path']
            logger.info("key path set in environment")
            keyset = True
        if type(config["key_path"]) == dict:
            directory = home+"/.gcp/"
            path = home+"/.gcp/gcp-key.json"
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
            try:
                os.makedirs(directory)
            except:
                logger.debug("key directory exists: {}".format(directory))
            with open(path, "w") as f:
                json.dump(config['key_path'],f)

            logger.info("key path set in environment and key written to file")
            keyset = True
    if keyset is not True:
        logger.warning("GCP key path not set in config, trying with defualt creds on host")
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

def list_addresses(client, org_name):
    """
    Demonstrate listing assets with a filter.
    dataformat: 
    {
        "addresses": [{
            "address":"",
            "dev": false,
            "project_name": ""
        }]
    }
    """
    logger.info("[list_addresses] listing IP addresses from security center")
    i = 0
    # cloud NAT does not allow incoming connections 
    # https://cloud.google.com/nat/docs/troubleshooting#unsolicited-incoming-connections

    
    # https://googleapis.dev/python/securitycenter/latest/gapic/v1/api.html#
    
    # types reference documentation 
    # NB this can change without warning and break the code
    # https://googleapis.dev/python/securitycenter/latest/securitycenter_v1/types.html

    # https://cloud.google.com/security-command-center/docs/how-to-api-list-assets#python_1
    project_filter = (
        'security_center_properties.resource_type="google.compute.Address" AND \
            resource_properties.addressType="EXTERNAL" AND \
            resource_properties.status="IN_USE"  AND\
            -resource_properties.purpose="NAT_AUTO" AND\
            -resource_properties.users:"routers"')
    # Call the API and print results.
    try:
        # Log information on credentials
        try:
            logger.info("[list_addresses] Service account used: {}".format(client._transport._credentials.service_account_email))
        except:
            logger.warning("[list_addresses] Default account in Environment used")
        gcp_request = securitycenter.ListAssetsRequest(parent=org_name, filter=project_filter)
        logger.debug("[list_addresses] list assets request object generated")
        asset_iterator = client.list_assets(gcp_request)
        logger.debug("[list_addresses] Asset iterator created")
    except Exception as e:
        logger.error("[list_addresses] Error requesting the data from gcp api")
        logger.error(e, exc_info=True)
        exit(1)

    addresses={"addresses": []}
    #assets = list(asset_iterator)
    for asset_result in enumerate(asset_iterator):
        address=""
        inUse=False
        dev=False
        try:
            asset=MessageToDict(asset_result[1]._pb.asset)
        except Exception as e:
            logger.error("[list_addresses] Error parsing data from API")
            logger.error(e, exc_info=True)
            exit(1)

        if "dev" in asset['securityCenterProperties']['resourceProjectDisplayName']:
            dev=True 
        address = {
            'address': asset['resourceProperties']['address'],
            'dev': dev,
            "project_name": asset['securityCenterProperties']['resourceProjectDisplayName']
        }
        addresses['addresses'].append(address)
    logger.info("[list_addresses] Finished listing addresses")
    return addresses

def list_forwarding_rules(client, org_name):
    """Demonstrate listing assets with a filter."""
    i = 0
    logger.info("[list_forwarding_rules] listing forwarding rules from security center")
    # https://googleapis.dev/python/securitycenter/latest/gapic/v1/api.html#
    project_filter = ('(security_center_properties.resource_type="google.compute.GlobalForwardingRule" OR \
            security_center_properties.resource_type="google.compute.ForwardingRule") AND \
            resource_properties.loadBalancingScheme="EXTERNAL"')
    # Call the API and print results.
    
    try:
        gcp_request = securitycenter.ListAssetsRequest(parent=org_name, filter=project_filter)
        asset_iterator = client.list_assets(gcp_request)
    except Exception as e:
        logger.error("[list_addresses] Error requesting the data from gcp api")
        logger.error(e, exc_info=True)
        exit(1)

    forwardingRules={"rules": []}
    #assets = list(asset_iterator)
    for asset_result in enumerate(asset_iterator):
        address=""
        protocol=""
        dev=False
        try:
            try:
                asset=MessageToDict(asset_result[1]._pb.asset)
            except Exception as e:
                logger.error("[list_forwarding_rules] Error parsing data from API")
                logger.error(e, exc_info=True)
                exit(1)

            if "dev" in asset['securityCenterProperties']['resourceProjectDisplayName']:
                dev=True 
            address = str(asset['resourceProperties']['IPAddress'])
            protocol = str(asset['resourceProperties']['IPProtocol'])

            # Addresses with forwarding on other protocols will be treated as standard IP address
            if protocol=="UDP" or protocol=="TCP":
                portRange = asset['resourceProperties']['portRange'].split('-')
                ports = []
                if portRange[0] == portRange[1]:
                    ports.append(portRange[0])
                else:
                    ports = list(range(int(portRange[0]),int(portRange[1])+1))

                i=0
                found=False
                for tmpRule in forwardingRules['rules']:
                    if address == tmpRule['address'] and tmpRule['protocol']==protocol:
                        forwardingRules['rules'][i]['ports'] = forwardingRules['rules'][i]['ports'] + ports
                        found=True
                        break
                    i=i+1
                if not found:
                    forwardingRules['rules'].append(\
                        {'address': address,\
                            'dev':dev,\
                            'ports': ports,\
                            'protocol':protocol}\
                            )
        except Exception as e:
            logger.warning("Issue with getting IP address from load balancer")
            logger.debug(e, exc_info=True)
            logger.debug(str(asset))
                
    #sort port arrays
    i=0
    while i <len(forwardingRules['rules']):
        forwardingRules['rules'][i]['ports'].sort()
        i=i+1
    return forwardingRules


def list_projects():
    logger.info("Listing GCP projects")

    # https://googleapis.dev/python/cloudresourcemanager/latest/index.html
    client = resource_manager.Client()
    project_ids = []
    # List all projects you have access to
    for project in client.list_projects():
        if project.status == "ACTIVE":
            project_ids.append(project.project_id)
    
    return project_ids

def export_project_dns_zone(project: str):
    logger.debug("Listing dns for project {}".format(project))
    # https://googleapis.dev/python/dns/latest/index.html
    # https://googleapis.dev/python/dns/latest/resource-record-set.html#google.cloud.dns.resource_record_set.ResourceRecordSet
    data = {}
    '''
    zone_format = {
        "<record_type>": [
            "<name>": value
        ]
    }
    '''
    try:
        client = dns.Client(project=project)
        zones = client.list_zones()  # API request
        for zone in zones:
            if zone.name not in data:
                data = {**data,zone.name:{}}
            
            records = zone.list_resource_record_sets()
            for record in records:
                if record.record_type in data[zone.name]:
                    data[zone.name][record.record_type] = {**data[zone.name][record.record_type],record.name: record.rrdatas}
                else:
                    data[zone.name][record.record_type] = {record.name: record.rrdatas}
        return data
    except Exception as e:
        if "Cloud DNS API has not been used in project" in str(e):
            logger.debug("DNS zone API not enabled in project: {}".format(project))
        else:
            logger.error("Issue listing DNS records - project: {}".format(project))
            logger.debug(e, exc_info=True)


def combine_dns_exports(data: list,public_only=True):
    masterexport = {}
    '''
    {
        "<record type>":{
            "<dns name>": ["<cname/IP address>", "<cname/IP address>"]
        }
    }

    '''
    try:
        for export in data:
            if export != None and export !={}:
                for zone in export:
                    for record_type in export[zone]:
                        if record_type in masterexport:
                            masterexport[record_type] = {**masterexport[record_type], **export[zone][record_type]}
                        else:
                            masterexport[record_type] = export[zone][record_type]
        if public_only:
            logger.info("Removing duplicate & internal CNAME records that point to A records")
            cname_names =  list(masterexport['CNAME'].keys())
            for name in cname_names:
                try:
                    value = masterexport['CNAME'][name][0]
                    # Google hosted is app engines ghs.googlehosted.com
                    # This needs to be kept for processing later. 
                    if (value in masterexport['A'] or value.endswith(".internal.")) and "googlehosted.com" not in value :
                        masterexport['CNAME'].pop(name)
                except:
                    logger.debug("issue checking cname: {}".format(name))
            logger.info("removing A records that point to a private IP address")
            a_record_names = list(masterexport['A'].keys())
            for name in a_record_names:
                try:
                    value = masterexport['A'][name][0]
                    IP = ipaddress.IPv4Address(value)
                    if IP.is_private:
                        masterexport['A'].pop(name)
                except Exception as e:
                    logger.debug("issue checking A record: {}".format(name))
                    logger.debug(e, exc_info=True)
    except Exception as e:
        logger.error("Error combining data")
        logger.debug(e, exc_info=True)
        masterexport = None
    return masterexport