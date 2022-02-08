
# Security Automation package

## Table of contents

- [Configmananger docs](docs/configmanager.md)
- [Data Manager docs](docs/datamanager.md)
- [Orchestrator Class](docs/orchestrator.md)
- [Common functions docs](docs/functions.md)
- [Data mappings](docs/data_mappings.md)
- [Using config file & Setting secrets](docs/config_file.md)
- Integration libraries
  - [Azure docs](docs/integrations/azure.md)
  - [GCP docs](docs/integrations/gcp.md)

### Note on Integrations
While there are specific packages for integrations, configmanager and datamanger can have specific functions for interacting with third party APIs. An example of this is config manager package has a function for pulling secrets from thycotic.

## Purpose
The purpose of this package is to provide an easily installable package of commonly used python code used in secops. One of the major objective with this library is to create an abstraction between the different cloud apis and secret management methods to allow the user to focus on writting functional code. 

This package is made up of few main components and was designed to be run in different environments. The functions called by your code are generic and offer an abstraction from the enviroment the code is run in. 

This is primarily seen in the config and data manager packages.

# Installation


## Virtual environment

when intalling python packages it is best practice to use a virtual environment so that you don't install the package for the whole system. Another benfit is you can delete the venv if it gets corrupted without reinstalling python.


```bash
python3 -m venv .venv
source .venv/bin/activate
```

## package installation

```bash
pip install sec_automation
# upgrade already installed package
pip install --upgrade sec_automation
```

# packages

The main packages in this are:

- configmanager
- datamanager
- orchestrator
- functions
- integrations


## configmanager
This package contains a number of functions which are used for reading config vaules and pulling secrets. 

The intention with this was to create a repeatable way to manage configurations inputs and secrets.

See below for more details  
[Configmananger docs](docs/configmanager.md)

## data manager
The idea behind this class is to abstact the actual code for reading the data from the environment from the function called in your code. This means you can run the same code on your laptop or in gcp and only change a config variable.

The other primary purpose of this class is to perform data validation. As the different datatypes have a format defined in the mappings file. As data is saved or read, the format is validated.

This currently only supports writing json files as it was intended for machine to machine comunications (eg. on prem server to gcp cloud function), not exporting to csv or other human friendly formats.  
[Data Manager docs](docs/datamanager.md)

For information on data types and formats and how these are used see below.  
[Data Mappings docs](docs/data_mappings.md)

## Orchestrator

This function is designed to allow you to configure the functionality of your code with a config file rather than having to rewrite code.  

See below for full instructions  
[Orchestrator Class](docs/orchestrator.md)

To see more information on the configuration file see below.  
[Data Mappings docs](docs/data_mappings.md)

# Example Uses


See "Examples" directory or look at external scan automation code
