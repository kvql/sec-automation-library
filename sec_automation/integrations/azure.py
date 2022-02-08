
import json
import time
import logging
import sec_automation.configmanager as cm
import sec_automation.functions as common
from sec_automation.functions import is_ipv4, validate_dns
import os
from copy import deepcopy
from sys import exit
from azure.mgmt.network import NetworkManagementClient
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient

logger= logging.getLogger(__name__)
config_prefix="azure-"

def setauth(config_header):
    # Ref https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity?view=azure-python
    config = cm.load_config(config_header)
    if "client_id" in config and "client_secret" in config and "tenant_id" in config:
        os.environ["AZURE_TENANT_ID"] = config['tenant_id']
        os.environ["AZURE_CLIENT_ID"] = config['client_id']
        os.environ["AZURE_CLIENT_SECRET"] = config['client_secret']
    else:
        logger.info("Azure client details not in config. attempting with other default auth options")
        if "AZURE_TENANT_ID" in os.environ:
            del os.environ["AZURE_TENANT_ID"]
        if "AZURE_CLIENT_ID" in os.environ:
            del os.environ["AZURE_CLIENT_ID"]
        if "AZURE_CLIENT_SECRET" in os.environ:
            del os.environ["AZURE_CLIENT_SECRET"]



def list_ip_addresses(subscription_id):
    '''
    Function to list all public ip addresses for this subscription and record associated DNS entry for that IP address
    '''
    # Setup credentials object
    credentials = DefaultAzureCredential()

    # Create network client. This is an object from the Azure sdk
    network_client = NetworkManagementClient(
            credentials,
            subscription_id
        )

    # Create public ip address page object. This doesn't contain any data but allows you to iterate through it and get the data
    # https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2018_02_01.operations.publicipaddressesoperations?view=azure-python
    public_ip_address = network_client.public_ip_addresses.list_all()
    addresses = { "addresses": [],
                "ip_list":[],
                "dns_ip_list": [],
                "dns_list": []}
    # Iterate through page object
    for ip in public_ip_address:
        try:
            # Extract data when IP is present but not DNS entry
            if ip.ip_address is not None and ip.dns_settings is None:
                addresses["addresses"].append({"ip": ip.ip_address,
                        "tags": ip.tags,
                        "allocation_method": ip.public_ip_allocation_method,
                        "name": ip.name,
                        "state": ip.provisioning_state,
                        "dns": None
                        }
                    )
                addresses["ip_list"].append(ip.ip_address)
            # Extract data when IP and DNS is present
            elif ip.ip_address is not None and ip.dns_settings is not None:
                addresses["addresses"].append({"ip": ip.ip_address,
                        "tags": ip.tags,
                        "allocation_method": ip.public_ip_allocation_method,
                        "name": ip.name,
                        "state": ip.provisioning_state,
                        "dns": ip.dns_settings.fqdn
                        }
                    )
                addresses["dns_ip_list"].append(ip.ip_address)
                addresses["dns_list"].append(ip.dns_settings.fqdn)
        except:
            logger.error("failed to parse IP")
    # TODO replace dynamic ip addresses with DNS name
    return addresses

def list_subscriptions(config_header=None):
    '''
    Function to list all subscription accessible with credentials and remove excluded subscription names as described in
    the config file
    '''
    try:
        #credentials = DefaultAzureCredential()
        credentials = CredentialWrapper()

        # https://docs.microsoft.com/en-us/python/api/azure-mgmt-subscription/azure.mgmt.subscription.subscriptionclient?view=azure-python
        sub_client = SubscriptionClient(credentials)

        subs = sub_client.subscriptions.list()
        subscriptions = []

        # possibly need to exclude provider namespace or you will get below response when listing ip addresses:
        # (DisallowedOperation) The current subscription type is not permitted to perform operations on any provider namespace. Please use a different subscription
        try: 
            if config_header != None:
                sub_exclusions = cm.load_config(config_header)
            else:
                # By default check for exclusions under azure header
                sub_exclusions = cm.load_config("azure.subscription_exclusions")
        except:
            # if checking config fails function runs without exclusions
            logger.warning("Failed to load subscription exclusions")
            sub_exclusions = []
        # Iterate through subscriptions and check if any should be excluded. 
        for sub in subs:
            if sub.display_name not in sub_exclusions:
                subscriptions.append({"name": sub.display_name,"id": sub.subscription_id})
        return subscriptions

    except Exception as e:
        logger.error("Issue listing subscriptions")
        logger.debug(e, exc_info=True)
        exit(1)



def list_loadbalancers(subscription_id):
    '''
    List load balancer details for this subscription
    Following items need to be gathered for each load balancer
    - inbound NAT rules
    - load balancer rules
    - forwarding IP configurations
    '''
    # create credential object
    credentials = DefaultAzureCredential()

    # create network client object
    network_client = NetworkManagementClient(
            credentials,
            subscription_id
        )
    # catch all for unexpected exceptions
    try:
        # ~~~~~~
        # List load balancers in this subscriptions
        # ~~~~~~
        # Ref: https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2017_10_01.operations.loadbalancersoperations?view=azure-python
        load_balancers = network_client.load_balancers.list_all()

        # Data format expected by other functions for load balancer profile
        dataformat= {
                        "ports":[],
                        "protocol":"",
                        "addresses": [],
                        "dns":{}
                    }
        data = []

        # https://docs.microsoft.com/en-us/azure/load-balancer/components
        ##############
        # Iterate through load balancers and get frontend IP addresses
        ##############
        for lb in load_balancers:
            # blank dict object for storing front end IP configurations
            front_ends = {}
            
            # Extracting details form load balancer ID string
            lb_id =lb.id.split('/')
            rg = lb_id[lb_id.index("resourceGroups")+1]
            
            # ~~~~~~~~~
            # Iterate through frontend IP configurations
            # ~~~~~~~~~
            # Create pager object for frontend IP configurations
            # Ref https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2017_10_01.operations.loadbalancerfrontendipconfigurationsoperations?view=azure-python
            lb_ips = network_client.load_balancer_frontend_ip_configurations.list(rg,lb.name)
            # Ref https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2017_10_01.models.frontendipconfiguration?view=azure-python
            count = 0
            for ip in lb_ips:
                # Skip objects that do not have a public IP, we do not care about internal load balanacers
                if ip.public_ip_address != None:
                    ip_id =ip.public_ip_address.id.split('/')
                    ip_rg = ip_id[ip_id.index("resourceGroups")+1]
                    ip_name = ip_id[ip_id.index("publicIPAddresses")+1]

                    # Now that we have the public IP name, we can request the details on this IP, similar to when we listed all public addresses
                    # Ref https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2020_06_01.operations.publicipaddressesoperations?view=azure-python
                    pub_ip = network_client.public_ip_addresses.get(ip_rg,ip_name)
                    if pub_ip is None:
                        raise Exception("public IP address not returned, unknown error")
                    
                    # Checking if DNS entry is present
                    dns = None
                    if pub_ip.dns_settings != None:
                        dns = pub_ip.dns_settings.fqdn
                    
                    # Appending new details to front end dictionary object
                    front_ends = {**front_ends, ip.id: {
                            "address": pub_ip.ip_address,
                            "dns": dns
                            }
                        }
                count += 1
            # if permissions aren't correct, the pager item will just return no results and not through an exception. Therefore to catch 
            # permission issues we need to compare a count of frontends in the load balancer object against the list returned by the pager object
            if len(lb.frontend_ip_configurations) != count:
                    logger.error("load balancer rules do not match count from load balancer. Expected rules: {}, rules returned: {}".format(len(lb.load_balancing_rules), count))
                    exit(1)
            
            ip=None
            dns=None
            ###########
            #check inbount nat rules
            ###########
            # checking the load balancer object to presence of nat rules
            if len(lb.inbound_nat_rules) >0:
                # Creating the nat rule pager object
                # Ref https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2017_10_01.operations.inboundnatrulesoperations?view=azure-python
                lb_nat = network_client.inbound_nat_rules.list(rg,lb.name)
                # Ref https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2017_10_01.models.inboundnatrule?view=azure-python
                count = 0

                for rule in lb_nat:
                    # Ref https://moonbooks.org/Articles/How-to-copy-a-dictionary-in-python-/
                    # how to avoid creating a pointer with deepcopy
                    tmp_rule = deepcopy(dataformat)
                    # dict front_ends only contains frontend ips configured with a public IP address
                    if rule.frontend_ip_configuration.id in front_ends:
                        # using the frontend IP ID in the nat rule object to get the IP details from the previously collected frontend IP addresses
                        ip = front_ends[rule.frontend_ip_configuration.id]
                        # handling IP addresses without DNS entry
                        if ip['dns'] == None:
                            tmp_rule['addresses'].append(ip['address'])
                        else:
                            tmp_rule['dns'] = {**tmp_rule['dns'], ip['dns']:ip['address']}
                        # Handling situation where protocal is not "TCP" or "UDP", in this situation we scan both
                        if type(rule.protocol) != str or rule.protocol == "All":
                            # add rule for UPD and TCP
                            tmp_rule['protocol'] = "UDP"
                            tmp_rule['ports'].append(rule.frontend_port)
                            data.append(deepcopy(tmp_rule))
                            # Adding second rule for TCP
                            tmp_rule['protocol'] = "TCP"
                            data.append(deepcopy(tmp_rule))
                        else:
                            # Adding details as described in the rule
                            tmp_rule['protocol'] = rule.protocol
                            tmp_rule['ports'].append(rule.frontend_port)
                            data.append(deepcopy(tmp_rule))
                    else:
                        logger.debug("Rule has no public IP")
                    count += 1
                # Same permission check as for frontend IPs
                if len(lb.inbound_nat_rules) != count:
                    logger.error("inbound_nat_rules do not match count from load balancer. Expected rules: {}, rules returned: {}".format(len(lb.inbound_nat_rules), count))
                    exit(1)

            ###########
            #check load balancer rules
            ###########
            if len(lb.load_balancing_rules)>0:
                # Ref https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2020_06_01.operations.loadbalancerloadbalancingrulesoperations?view=azure-python#list-resource-group-name--load-balancer-name----kwargs-
                lb_rules = network_client.load_balancer_load_balancing_rules.list(rg,lb.name)
                # Ref https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2020_06_01.models.loadbalancingrule?view=azure-python
                count = 0
                for rule in lb_rules:
                    # check for HA port load balancer which essentially load balances all ports, skipping these rules will mean they get scanned 
                    # as full scan profile. This is because all IPs are collected seperately and by default are scanned as full profile unless found in lb rules
                    if rule.frontend_port != 0: # int value 0 = any port in the config
                        # Avoid creating pointer
                        tmp_rule = deepcopy(dataformat)
                        # Getting IP address info from frontend details
                        if rule.frontend_ip_configuration.id in front_ends:
                            ip = front_ends[rule.frontend_ip_configuration.id]
                            if ip['dns'] == None:
                                tmp_rule['addresses'].append(ip['address'])
                            else:
                                tmp_rule['dns'] = {**tmp_rule['dns'], ip['dns']:ip['address']}
                            
                            # Same as nat rule logic
                            if type(rule.protocol) != str or rule.protocol == "All":
                                # add rule for UPD and TCP
                                tmp_rule['protocol'] = "UDP"
                                tmp_rule['ports'].append(rule.frontend_port)
                                data.append(deepcopy(tmp_rule))
                                # Adding second rule for TCP
                                tmp_rule['protocol'] = "TCP"
                                data.append(deepcopy(tmp_rule))
                            else:
                                tmp_rule['protocol'] = rule.protocol
                                tmp_rule['ports'].append(rule.frontend_port)
                                data.append(deepcopy(tmp_rule))
                    else:
                        logger.debug("Rule has no public IP")
                    count += 1
                # Same permission check, see frontend comment about this
                if len(lb.load_balancing_rules) != count:
                    logger.error("load balancer rules do not match count from load balancer. Expected rules: {}, rules returned: {}".format(len(lb.load_balancing_rules), count))
                    exit(1)
        #########    
        # consolidate rule per IP/dns address, into lb profiles
        # ############# 
        # As you can have different lb/nat rule on the same IP address. we need to consolidate this into one
        i = 0
        # While required as data array is changing during loop
        while i <len(data):
            # var definition
            pop_list = []
            # Firt point of data array to check is current position in the array + 1
            start = i+1
            y = start
            finish = len(data) # stops at finish -1 hence why len is used
            # loop through remaining data to find rules matching current IP and protocol in data[i], 
            for rule in data[start:finish]:
                if rule['protocol'] == data[i]['protocol'] and \
                    (common.compare_list(rule['addresses'], data[i]['addresses']) or \
                    common.compare_dict(rule['dns'], data[i]['dns'])):
                    # append to existing rule for same host and protocol
                    data[i]['ports'] = data[i]['ports'] + rule['ports']
                    # create list of rule to remove from data as their ports have been added to data[i]
                    pop_list.append(y)
                                      
                y+=1
            # remove rules from data as their ports have been added to data[i]
            # removing highest index first as otherwise you will change the array indexing and will remove the wrong rules
            pop_list.sort(reverse=True)
            for j in pop_list:
                data.pop(j)
            i +=1
        # Return data 
        return data
            
    except Exception as e:
        logger.error("Issue pulling load balancer rules")
        logger.debug(e, exc_info=True)
        exit(1)



###################
# supporting function due to api issues
# https://gist.github.com/lmazuel/cc683d82ea1d7b40208de7c9fc8de59d
# https://stackoverflow.com/questions/63384092/exception-attributeerror-defaultazurecredential-object-has-no-attribute-sig
##################

from msrest.authentication import BasicTokenAuthentication
from azure.core.pipeline.policies import BearerTokenCredentialPolicy
from azure.core.pipeline import PipelineRequest, PipelineContext
from azure.core.pipeline.transport import HttpRequest

from azure.identity import DefaultAzureCredential

class CredentialWrapper(BasicTokenAuthentication):
    def __init__(self, credential=None, resource_id="https://management.azure.com/.default", **kwargs):
        """Wrap any azure-identity credential to work with SDK that needs azure.common.credentials/msrestazure.
        Default resource is ARM (syntax of endpoint v2)
        :param credential: Any azure-identity credential (DefaultAzureCredential by default)
        :param str resource_id: The scope to use to get the token (default ARM)
        """
        super(CredentialWrapper, self).__init__(None)
        if credential is None:
            credential = DefaultAzureCredential()
        self._policy = BearerTokenCredentialPolicy(credential, resource_id, **kwargs)

    def _make_request(self):
        return PipelineRequest(
            HttpRequest(
                "CredentialWrapper",
                "https://fakeurl"
            ),
            PipelineContext(None)
        )

    def set_token(self):
        """Ask the azure-core BearerTokenCredentialPolicy policy to get a token.
        Using the policy gives us for free the caching system of azure-core.
        We could make this code simpler by using private method, but by definition
        I can't assure they will be there forever, so mocking a fake call to the policy
        to extract the token, using 100% public API."""
        request = self._make_request()
        self._policy.on_request(request)
        # Read Authorization, and get the second part after Bearer
        token = request.http_request.headers["Authorization"].split(" ", 1)[1]
        self.token = {"access_token": token}

    def signed_session(self, session=None):
        self.set_token()
        return super(CredentialWrapper, self).signed_session(session)

