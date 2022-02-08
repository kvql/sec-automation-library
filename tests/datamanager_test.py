import pytest
import os
from sec_automation.datamanager import DataManager as dm

import json
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

good_filedata={
    "datatype":"gcp_exposure_data",
    "page":0,
    "totalpages":0,
    "data":{
        "location": "",
        "lb_profiles":[
            
        ],
        "full_scan_profile":{
            "addresses":[],
            "dns":{}
        },
        "unknown":{
            "addresses":[],
            "dns":{}
        },
        "app_profile":{
                "ports":["80","443"],
                "protocol":"TCP",
                "addresses": [],
                "dns":{}
            }
    }
}

good_data = {
        "location": "",
        "lb_profiles":[],
        "full_scan_profile":{
            "addresses":[],
            "dns":{}
        },
        "unknown":{
            "addresses":[],
            "dns":{}
        },
        "app_profile":{
            "ports":["80","443"],
            "protocol":"TCP",
            "addresses": [],
            "dns":{}
        }
    }
    
    
bad_filedata={
    "datatype":1,
    "page":"sdfsdfs",
    "totalpages":0,
    "data":{
        "LB_Prdsdalkhglashofile":[],
        "IP_addresses":[]
    },
    "sdfsdf":"sdfsdf"
}

@pytest.mark.unit_test
def test_datamanager():
    os.environ['sa_environment']="local"
    assert dm()
    os.environ['sa_environment']="gcp"
    assert dm()
    del os.environ['sa_environment']

@pytest.mark.unit_test
def test_dm_input():
    try:
        os.environ['sa_environment']="gcsfs"
        dm()
        assert False
    except:
        assert True
    del os.environ['sa_environment']

@pytest.mark.unit_test
def test_wrongpath():
    os.environ['sa_datapath'] = "/tmp/3434444df"
    os.environ['sa_environment']="local"
    try:
        dm()
        assert False
    except:
        assert True
    del os.environ['sa_environment']
    del os.environ['sa_datapath']
    
@pytest.mark.unit_test
def test_loaddata():
    os.environ['sa_datapath'] = os.getcwd()+"/tests/testdata/"
    try:
        datam = dm()
        datam.client.storefile(good_filedata,"good_data.json")
        datam.loadfile("good_data.json")
        assert True
    except:
        assert False
    del os.environ['sa_datapath']



# def test_storefile():
#     datam.client.storefile(good_data,"gcp_exposure_data")

@pytest.mark.unit_test
def test_load_bad_data():
    os.environ['sa_datapath'] = os.getcwd()+"/tests/testdata/"
    try:
        datam = dm()
        datam.client.storefile(bad_data,"bad_data.json")
        datam.loadfile("bad_data.json")
        assert False
    except:
        assert True
    del os.environ['sa_datapath']

@pytest.mark.local_test
def test_latestfilename():
    os.environ['sa_environment']="local"
    os.environ['sa_datapath'] = os.getcwd()+"/tests/testdata/"
    try:
        datam = dm()
        datam.client.storefile(bad_filedata,"bad_data.json")
        datam.client.storefile(good_filedata,"good_data.json")
        filename = datam.client.latestfile()
        if filename != "good_data.json":
            logger.info("filename: {}".format(filename))
            assert False
        assert True
    except:
        assert False
    del os.environ['sa_datapath']
    del os.environ['sa_environment']

# Above test isn't working in ci/cd pipeline. 

@pytest.mark.local_test
def test_loaddata_gcp():
    os.environ['sa_environment']="gcp"
    try:
        datam = dm()
        datam.client.storefile(json.dumps(good_filedata),"good_data.json")
        datam.loadfile("good_data.json")
        assert True
    except:
        assert False
    del os.environ['sa_environment']
