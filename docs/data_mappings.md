# Data mappings file

This file has two purposes:

1. Mapping datatypes functions to action functions
2. Mapping datatypes to example data structures

## Base file structure and location 

The default location for this file is `config_data/data_actions_mapping.json` where this is a relative path from where the script or main.py is located.

custom path can be specified an environment variable `sa_confmap`

e.g. `export sa_confmap=/tmp/data_map.json`

The file has an expected file structure as shown below:

in the app definition,the folder is represented as a .  
e.g. use app.getData for a package called "getData" in folder "app"

```json
{
    "commands": {
        "<function name within package>": {
            "app": "<Path to package>",
            "datatypes": ["<list of datatypes you want to run this command against>"]
        }
    },
    "datatypes": { 
        "<function Name>":{
            "app": "<Path to package>",
            "dataformat": "<name of dataformat you expect this function to return>"
        }
    },
    "dataformats": {
        "<dataformat name>": "<Exaple json structrue>"
    }
}

```

## Datatypes
Data types are defined as shown below:

```json
"datatypes": { 
        "<function Name>":{
            "app": "<package/file name in .app/data directory",
            "dataformat": "<name of dataformat you expect this function to return>"
        }
    },
```

### Example

```json
"datatypes": { 
        "gcp_exposure_data": {
            "app": "app.data.gcp_data",
            "dataformat": "public_exposure"
        },
        "azure_exposure_data": {
            "app": "app.data.azure_data",
            "dataformat": "public_exposure"
        },
        "vuln_scanner_asset_data": {
            "app": "vuln_scanner_data",
            "dataformat": "None"
        }
    },
```

## Dataformats

currently only json is supported as a format and only the first level keys are validated 

The structure of the json can be defined in  dataformat de

To expand support to other formats the validation functions will need to be modified

### Example

```json
"dataformats": {
        "public_exposure": {
            "location": "",
            "lb_profiles":[
                {
                    "ports":[],
                    "protocol":"",
                    "addresses": [],
                    "dns":{}
                }
            ],
            "full_scan_profile":{
                "addresses":[],
                "dns":{}
            },
            "unknown":{
                "addresses": [],
                "dns":{}
            },
            "app_profile":{
                "ports":[],
                "protocol":"",
                "addresses": [],
                "dns":{}
            }
        }
    }
```