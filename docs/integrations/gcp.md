

# Configuration requirements
Below configuration is required in the config file to use certain 
Data manager not used

```json
"gcp":{
        "org_id":"",
        "key_path": {
            "secret_manager": "thycotic",
            "config_header": "thycotic",
            "secret_id":"5039",
            "secret_type": "gcp-key"
            }
    }
```

or 

```json
"gcp":{
        "org_id":"",
        "key_path": "/home/username/gcp_key.json"
    }
```


## Data Manager

Data manager does not support setting the key path. It will check the os for a key file.  If running in gcp this will be the service account the cloud func or server is running as.

```json
"gcp":{
        "bucket_id":"",
        "project_id":"",
        "org_id":""
    }
```