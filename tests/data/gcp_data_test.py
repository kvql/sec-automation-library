import pytest
import os
import sec_automation.integrations.gcp as gd
from sec_automation.datamanager import DataManager 
import sec_automation.configmanager as cm
from google.cloud import securitycenter
import sec_automation.functions as functions

home = os.path.expanduser("~")
os.environ['sa_confpath']=os.getcwd()+"/tests/testdata/sample_config.json"
os.environ['sa_confmap']=os.getcwd()+"/tests/testdata/data_actions_mapping.json"
# Set proxy variables
cm.load_config('proxy')

# Create loggers
log_level = cm.load_config('log_level')
logger = functions.create_logger("app", log_level)
functions.create_logger("sec_automation", log_level)

@pytest.mark.unit_test
def test_load():
    pass

@pytest.mark.integration_test
def test_list_addresses():
    dm = DataManager()
    cm.load_config('proxy')
    try:
        gd.set_auth("gcp")
        client = securitycenter.SecurityCenterClient()
        config = cm.load_config("gcp")
        org_name = "organizations/{}".format(config['org_id'])
        data = gd.list_addresses(client,org_name)
        
        assert True
    except Exception as e:
        logger.error("Unknown error")
        logger.debug(e, exc_info=True)
        assert False

@pytest.mark.integration_test
def test_list_projects():
    dm = DataManager()
    try:
        gd.set_auth("gcp")
        data = gd.list_projects()
        
        assert True
    except Exception as e:
        logger.error("Unknown error")
        logger.debug(e, exc_info=True)
        assert False

@pytest.mark.integration_test
def test_list_dns():
    dm = DataManager()
    try:
        gd.set_auth("gcp")
        data = gd.export_project_dns_zone("")
        
        assert True
    except Exception as e:
        logger.error("Unknown error")
        logger.debug(e, exc_info=True)
        assert False

@pytest.mark.integration_test
def test_combine():
    try:
        gd.set_auth("gcp")        
        projects = gd.list_projects()
        data = []
        count = 0
        for project in projects:
            data.append(gd.export_project_dns_zone(project))
            count+=1
            if count>10:
                break
        master = gd.combine_dns_exports(data)
        
        assert True
    except Exception as e:
        logger.error("Unknown error")
        logger.debug(e, exc_info=True)
        assert False
