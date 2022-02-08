import pytest
import os
import sec_automation.orchestrator as orch
import sec_automation.datamanager as DataManager
import logging
import sec_automation.functions as functions
import sec_automation.configmanager as cm

home = os.path.expanduser("~")
os.environ['sa_confpath']=os.getcwd()+"/tests/testdata/sample_config.json"
os.environ['sa_confmap']=os.getcwd()+"/tests/testdata/data_actions_mapping.json"
# Set proxy variables
cm.load_config('proxy')

# Create loggers
log_level = cm.load_config('log_level')
logger = functions.create_logger("secops_automation", log_level)

@pytest.mark.unit_test
def test_load_orchestrator():
    assert orch.Orchestrator()


@pytest.mark.unit_test
def test_validate_command():
    try:
        orches = orch.Orchestrator()
        orches.validate_command("update_public_exposure")
        assert True
    except:
        assert False

@pytest.mark.unit_test
def test_validate_datatype():
    try:
        orches = orch.Orchestrator()
        orches.validate_datatype("gcp_exposure_data")
        assert True
    except:
        assert False
# @pytest.mark.integration_test
# def test_local_test_run():
   
#     try:
#         dm = DataManager()
#         filename = dm.client.latestfile()
#         orches = orch.Orchestrator()
#         orches.dataaction(file_name=filename)
#         assert True
#     except:
#         assert False

# @pytest.mark.integration_test
# def test_data_request():
#     try:
#         orches = orch.Orchestrator()
#         orches.getdata(datatype="gcp_exposure_data")
#         assert True
#     except:
#         assert False
#     del os.environ['sa_confpath']