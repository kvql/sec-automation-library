import pytest
import os
import sec_automation.configmanager as cm
import sec_automation.functions as functions

home = os.path.expanduser("~")
os.environ['sa_confpath']=os.getcwd()+"/tests/testdata/sample_config.json"
os.environ['sa_confmap']=os.getcwd()+"/tests/testdata/data_actions_mapping.json"
# Set proxy variables
cm.load_config('proxy')

# Create loggers
log_level = cm.load_config('log_level')
logger = functions.create_logger("secops_automation", log_level)

@pytest.mark.unit_test
def test_configmanager():
    try:
        
        os.environ['sa_vuln_scanner_pass'] = "dsfs"
        x = cm.load_basic_config()
        if "environment" not in x or x['vuln_scanner2']['secret'] !="dsfs":
            assert False
        assert True
    except:
        assert False
    del os.environ['sa_vuln_scanner_pass']

@pytest.mark.unit_test
def test_configmanager_directpath():
    try:
        os.environ['sa_vuln_scanner_username'] = "dsfs"
        x = cm.load_basic_config("vuln_scanner.username")
        if "environment" in x or x !="dsfs":
            assert False
        assert True
    except:
        assert False
    del os.environ['sa_vuln_scanner_username']

@pytest.mark.unit_test
def test_configmanager_section_defaults():
    try:
        os.environ['sa_vuln_scanner_proxy'] = "dsfs"
        x = cm.load_basic_config("vuln_scanner")
        if "environment" in x:
            assert False
        assert True
    except:
        assert False
    del os.environ['sa_vuln_scanner_proxy']


@pytest.mark.unit_test
def test_dm_wrongpath():
    try:
        os.environ['sa_confpath']="ssfsdfs/config.txt"
        cm.load_basic_config()
        assert False
    except:
        assert True
    os.environ['sa_confpath']=os.getcwd()+"/tests/testdata/sample_config.json"




@pytest.mark.unit_test
def test_options():
    try:
        options = cm.data_options()
        if "commands" in options.keys():
            assert True
        else:
            assert False
    except:
        assert False

@pytest.mark.unit_test
def test_relatedcommands():
    commands = cm.related_commands("gcp_exposure_data")
    if type(commands) == list and len(commands) > 0:
        assert True
    else:
        assert False

test_config = {
    "secret_manager":"local",
    "env_var": "test_secret"
}

@pytest.mark.unit_test
def test_secret_request():
    os.environ["test_secret"] = "sssss"
    try:
        x = cm.SecretManager.request_secret(test_config)
        if x != "sssss":
            assert False
        assert True

    except:
        assert False

@pytest.mark.unit_test
def test_secret_request_basic():
    os.environ["test_secret"] = "sssss"
    try:
        x = cm.SecretManager.request_basic_secret(test_config)
        if x != "sssss":
            assert False
        assert True

    except:
        assert False

@pytest.mark.integration_test
def test_th_secret():
    thycotic_format = {
        "secret_manager": "thycotic",
        "config_header": "thycotic",
        "secret_id":"4852",
        "secret_type": "password"
        }

    try:
        x = cm.SecretManager.request_secret(thycotic_format)
        if type(x) == str or type(x) == dict:
            assert True
        else:
            assert False
    except:
        assert False

@pytest.mark.integration_test
def test_th_secret_key_file():
    thycotic_format = {
        "secret_manager": "thycotic",
        "config_header": "thycotic",
        "secret_id":"5039",
        "secret_type": "gcp-key"
        }

    try:
        x = cm.SecretManager.request_secret(thycotic_format)
        if type(x) == str  or type(x) == dict:
            assert True
        else:
            assert False
    except:
        assert False

@pytest.mark.integration_test
def test_configmanager():
    try:
        os.environ['sa_vuln_scanner_pass'] = "dsfs"
        x = cm.load_config()
        if "environment" not in x or x['vuln_scanner2']['secret'] !="dsfs":
            assert False
        assert True
    except:
        assert False
    del os.environ['sa_vuln_scanner_pass']