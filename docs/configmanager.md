# Config Manager


# Primary functions

Below are the primary functions available for use in this package:

- loading config - configmanager.load_config
- setting proxy - configmanager.load_config(input_key=proxy)

## Supporting functions

Most other functions in the package should not be called directly as they are just to support loading the config file. Details on the these can be found in the code comments

The two functions which could be called are `related_commands` and `data_options` these are used by the orchestrator functions to read the data_mappings file.

##  Example uses

### setting proxy
The below code will read the proxy variable from the config file and set the OS environment variables "https_proxy" and "http_proxy"

```python
import secops_automation.configmanager as cm

# Set proxy variables on the system
cm.load_config('proxy')

```

### Loading the whole config file

```python
import secops_automation.configmanager as cm

# load whole config file and return as dict object
config = cm.load_config()

```

# Secrets



## basic secrets

local or gcp

## other secrets

