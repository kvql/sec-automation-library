import pytest
import os
import sec_automation.integrations.azure as gd
from sec_automation.datamanager import DataManager 
import sec_automation.configmanager as cm
import sec_automation.functions as functions

home = os.path.expanduser("~")
os.environ['sa_confpath']=os.getcwd()+"/tests/testdata/sample_config.json"
os.environ['sa_confmap']=os.getcwd()+"/tests/testdata/data_actions_mapping.json"
# Set proxy variables
cm.load_config('proxy')

# Create loggers
log_level = cm.load_config('log_level')
logger = functions.create_logger("app", log_level)
functions.create_logger("secops_automation", log_level)

@pytest.mark.unit_test
def test_load():
    pass




@pytest.mark.integration_test
def test_list_addresses():
    try:
        gd.setauth(config_header="azure-1")
        config = cm.load_config("azure-address")
        subscription_id = config["subscription_id"]
        x = gd.list_ip_addresses(subscription_id )
        
        assert True
    except:
        assert False

@pytest.mark.integration_test
def test_list_loadbalancers():
    try:
        config = cm.load_config("azure-lb")
        subscription_id = config["subscription_id"]
        gd.setauth(config_header="azure-1")
        x = gd.list_loadbalancers(subscription_id )
        assert True
    except:
        assert False

@pytest.mark.integration_test
def test_list_loadbalancers_nat():
    try:
        gd.setauth(config_header="azure-1")
        config = cm.load_config("azure-nat")
        subscription_id = config["subscription_id"]
        x = gd.list_loadbalancers(subscription_id )
        assert True
    except:
        assert False

@pytest.mark.integration_test
def test_list_subs():
    try:
        gd.setauth(config_header="azure-1")
        x = gd.list_subscriptions()
        assert True
    except:
        assert False
