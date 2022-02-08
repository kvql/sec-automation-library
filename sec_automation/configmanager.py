import os
import json
import logging
from sys import exit
#import app.common.secretsmanager as sm

from google.cloud import secretmanager as gcp_secretmanager

from thycotic.secrets.server import (
    SecretServerAccessError,
    SecretServerCloud,
    SecretServerError,
)

logger = logging.getLogger(__name__)

defaults={
    "vuln_scanner":{
        "hostname": "vuln_scannerapi.vuln_scanner.eu",
        "username": "",
        "password": ""
    },
    "gcp":{
        "bucket_id":"",
        "project_id":"",
        "org_id":""
    },
    "thycotic": {
        "tenant": "",
        "username": "",
        "password": "",
        "tld": "eu"
    },
    "environment":"local",
    "datapath": "/tmp",
    "log_level": "INFO",
    "proxy": "",
    "dry_run": "False"
}



def load_config(input_key=""):
    keygiven=False
    
    ###########################
    # Checking Input Key
    ###########################
    # Key must be in the following format: (json dot notation)
    # key = ""
    # key = "key1"
    # key = "key1.key2"
    if input_key != "":
        keys = input_key.split('.')
        keygiven = True
    else:
        keys = []

    if len(keys) > 2:
        logger.error("key too long check config format guide")
        raise Exception("key too long check config format guide")
    
    # Using load_basic_config to load the config into a variable and perform basic checks
    config = load_basic_config(input_key)
    if config == None:
        raise Exception("Empty config value returned from load_basic_config")
    try:
        ####################
        # Set proxy
        ####################
        if type(config) == dict and "proxy" in config:
            os.environ['http_proxy']=config["proxy"]
            os.environ['https_proxy']=config["proxy"]
            logger.info("Proxy set to {}".format(config["proxy"]))
        elif type(config) == str and input_key == "proxy":
            os.environ['http_proxy']=config
            os.environ['https_proxy']=config
            logger.info("Proxy set to {}".format(config))
        
        ###########################
        # Code to request advanced secrets
        ###########################
        '''
        Code to review loaded config and request secrets not covered by basic secret requests
        '''
        #~~~~~~~
        # Input key is path to specific config value. Also covers key len =2
        #~~~~~~~
        if type(config) == str or type(config) == list:
            return config
        # Check if config value is secret config
        # Handle scenario where the exact key is requested but its a secret       
        elif type(config) == dict and "secret_manager" in config:
            logger.debug("requesting secret to replace config value")
            config = SecretManager.request_secret(config)
            return config
        #~~~~~~~
        # No input key provided or input key is path to a config section
        #~~~~~~~
        elif len(keys) == 0:
            # Checking if first level of the config object contains all default key value pairs
            if config.keys() != defaults.keys():
                for item in defaults:
                    if item not in defaults.keys():
                        config = {**config, item: defaults[item]}
            # check if a secret needs to be requested
            for key in config:
                if type(config[key]) == dict:
                    config[key] = check_section_secrets(key,config[key])
            return config
        #~~~~~~~
        # Input key is path to a config section
        #~~~~~~~
        elif len(keys) == 1:
            # check if a secret needs to be requested
            for key in config:
                if type(config[key]) == dict and "secret_manager" in config[key]:
                    config[key] = SecretManager.request_secret(config[key])
            return config
        else:
            raise Exception("Unknown key path. Issue loading config")
            # Not checking for len(keys)== 2 as this would be direct path to key value pair and is already covered
        return None
    except Exception as e:
        logger.error("Unknown exception while loading config")
        logger.error(e, exc_info=True)
        raise Exception



def load_basic_config(input_key=""):
    keygiven=False
    try:
        ###########################
        # Checking Input Key
        ###########################
        # Key must be in the following format: (json dot notation)
        # key = ""
        # key = "key1"
        # key = "key1.key2"
        if input_key != "":
            keys = input_key.split('.')
            keygiven = True
        else:
            keys = []

        if len(keys) > 2:
            logger.error("key too long check config format guide")
            raise Exception("key too long check config format guide")
        
        ###########################
        # Loading config file
        ###########################
        configfile = None
        # Default config path
        path=os.getcwd()+"/config_data/config.json"
        
        # Checking if config path is set in the environment
        if "sa_confpath" in os.environ:
            # load config file from disk
            path = os.environ["sa_confpath"]
            logger.debug("Config path is: {}".format(path))
        try:
            with open(path) as f:
                configfile = json.loads(f.read())
                logger.debug("config file is open")
        except Exception as e:
            logger.error("Failed to open config file. Path: {}".format(path))
            logger.error(e, exc_info=True)
            raise Exception("Failed to open config file. Path: {}".format(path))

        # Config file not found, setting config file var to the default
        if configfile is None:
                configfile = defaults
                logger.debug("Setting config to defaults in package")
        
        ###########################
        # Extracting specific config values as specified with input key
        ###########################

        # Config when no key is provided
        if len(keys) == 0: 
            logger.debug("parsing config file for Input key lenght = 0")
            # set config variable to configfile variable
            config = configfile
        # Config when single level key is passed
        elif len(keys) == 1:
            logger.debug("parsing config file for Input key lenght = 1")
            if keys[0] not in configfile:
                # If key not in config file use default value
                if keys[0] in defaults:
                    config = defaults[keys[0]]
                else:
                    logger.error("Invalid key: {}".format(input_key))
                    raise Exception("Invalid key: {}".format(input_key))
            else:
                config = configfile[keys[0]]
        # Config when 2 level key is passed 
        else:
            logger.debug("parsing config file for Input key lenght = 2")
            if keys[0] not in configfile and keys[1] not in configfile[keys[0]]:
                # If key not in config file use default value
                if keys[0] in defaults and keys[1] in defaults[keys[0]]:
                    config = defaults[keys[0]][keys[1]]
                else:
                    logger.error("Invalid key: {}".format(input_key))
                    raise Exception("Invalid key: {}".format(input_key))
            else:
                config = configfile[keys[0]][keys[1]]
        
        ###########################
        # Code to validate config
        ###########################
        ''' 
        This section will do the following actions:
        # input key is to direct value path
        1. Replace secret configs with the secret value
        2. Check for default keys missing from the config dict object
        3. Check for config values set in the environment and replace 
            their value with the environment value

        Note: In this code, a section is refered to as json object with config values specific to a 1 technology
        '''
        logger.debug("Validating config")
        #~~~~~~~
        # Input key is path to specific config value 
        #~~~~~~~
        if type(config) == str or type(config) == list:
            if keygiven and check_env(input_key) != None:
                config = check_env(input_key)
        # Check if config value is secret config
        # Handle scenario where the exact key is requested but its a secret       
        elif type(config) == dict and "secret_manager" in config:
            if keygiven and check_env(input_key) != None:
                config = check_env(input_key)
                return config
            else:
                logger.debug("requesting secret to replace config value")
                config = SecretManager.request_basic_secret(config)
                return config
        #~~~~~~~
        # No input key provided or input key is path to a config section
        #~~~~~~~
        elif len(keys) == 0:
            # Checking if first level of the config object contains all default key value pairs
            if config.keys() != defaults.keys():
                for item in defaults:
                    if item not in defaults.keys():
                        config = {**config, item: defaults[item]}
            # check each value to see if a corresponding env is set or
            #  if a secret needs to be requested
            for key in config:
                if type(config[key]) != dict:
                    if check_env(key) != None:
                        config[key] = check_env(key)
                else:
                    config[key] = check_section(key,config[key])
            return config
        #~~~~~~~
        # Input key is path to a config section
        #~~~~~~~
        elif len(keys) == 1:
            # Checking if section contains all default key value pairs
            try:
                if config.keys() != defaults[input_key].keys():
                    for item in defaults[input_key]:
                        if item not in config.keys():
                            logger.debug("Adding missing config key: {}".format(item))
                            config = {**config, item: defaults[input_key][item]}
            except:
                logger.debug("Failed to add defaults for key: {}".format(input_key))
            # check each value to see if a corresponding env is set or
            #  if a secret needs to be requested
            for key in config:
                env_key = input_key+"."+key
                if type(config[key]) != dict:
                    if check_env(env_key) != None:
                        config[key] = check_env(env_key)
                elif "secret_manager" in config[key]:
                    config[key] = SecretManager.request_basic_secret(config[key])
                else:
                    logger.error("invalid config format, json at depth of 3 can only be a secret config")
                    raise Exception("invalid config format, json at depth of 3 can only be a secret config")
        else:
            raise Exception("Unknown key path. Issue loading config")
            # Not checking for len(keys)== 2 as this would be direct path to key value pair and is already covered
        return config
    except Exception as e:
        logger.error("[load_basic_config]Unknown exception while loading config")
        logger.error(e, exc_info=True)
        raise Exception


def check_section(key:str,section: dict):
    '''
    Function to check default values, env vars and secrets
    for a specific section
    '''
    
    # Try add default values and missing keys
    try:
        logger.debug("checking section: key= {} & section = {}".format(key,section.keys()))
        if key == "":
            return None
        if section.keys() != defaults[key].keys():
            for item in defaults[key]:
                if item not in section.keys():
                    # append default keys missing from the section to the section loaded from the config file
                    section = {**section, item: defaults[key][item]}
    except:
        logger.debug("failed to add default key{}".format(key))
    # check for environment vars and secrets
    for item in section:
        env_key = key + "." + item
        if check_env(env_key) != None:
            section[item] = check_env(env_key)
        elif "secret_manager" in section[item]:
            section[item] = SecretManager.request_basic_secret(section[item])
    return section

def check_section_secrets(key:str,section: dict):
    '''
    Function to check dict for advanced secret types
    '''
    # check for environment vars and secrets
    for item in section:
        env_key = key + "." + item
        if check_env(env_key) != None:
            section[item] = check_env(env_key)
        elif "secret_manager" in section[item]:
            section[item] = SecretManager.request_secret(section[item])
    return section
    

def check_env(key:str):
    '''
    Function to check if key is set as an env variable
    '''
    logger.debug("Checking environment Var for Config overrides, key: {}".format(key))
    if key == "":
        return None
    keys = key.split('.')
    name="sa"
    value = None
    for key in keys:
        name = name + '_' + key
    if name in os.environ:
        value = os.environ[name]
    return value


    
##############################
# Functions to load the mapping file for datatypes and commmands
##############################

def data_options():
    try:
        path = os.getcwd() + "/config_data/data_actions_mapping.json"
        # Checking if config path is set in the environment
        if "sa_confmap" in os.environ:
            # load config file from disk
            path = os.environ["sa_confmap"]
            logger.debug("Config path is: {}".format(path))
        with open(path) as f:
            options = json.loads(f.read())
        
        # validate content and format of options file
        datatypes=options['datatypes'].keys()
        
        ## Validate that the commands reference defined datatypes
        commands=options['commands'].keys()
        for command in commands:
            for datatype in options['commands'][command]['datatypes']:
                if datatype not in datatypes:
                    logger.error("{} is not a defined datatype in options file".format(command_dt))
                    raise Exception("{} is not a defined datatype in options file".format(command_dt))

        return options
    except Exception as e:
        logger.error("Failed to open config file. Path: {}".format("data_actions_mapping.json"))
        logger.error(e, exc_info=True)

def related_commands(datatype):
    '''
    Function to return list of commands that use the given datatype
    '''
    options = data_options()
    commands=[]
    for command in options['commands']:
        command_options =options['commands'][command]
        if datatype in command_options['datatypes']:
            commands.append(command)
            logger.debug("related command found: {}".format(command))
    return commands





supported_basic_managers=["local","gcp"]
supported_managers=["local", "thycotic", "gcp"]
###########
# Basic secret manager types
###########
'''
These are basic as they do not have a dependancy on the config manager functions. All information required to request the secret is 
stored in the secret format
These can be used to store secrets for the more advance secret manager functions as they have a dependancy on the config load function
'''
local_format = {
            "secret_manager": "local",
            "env_var": "sa_vuln_scanner_user"
        }
    
gcp_format = {
    "secret_manager": "gcp",
    "project_id": "",
    "secret_id": "",
    "version_id": "latest"
    }

###########
# Advanced secret manager types
###########
thycotic_format = {
    "secret_manager": "thycotic",
    "config_header": "thycotic",
    "secret_id":"",
    "secret_type": "password"
}
supported_tychotic_secrets = ["username","password","gcp-key"]
'''
config_header refers to the top level section in the options
file that specifies the secret server instance details
This is provided as an example of how to handle situations where you could have multiple instances
'''

class SecretManager:
    def request_basic_secret(secret_config):
        # check if the listed secret manager is supported 
        try:
            if secret_config['secret_manager'] not in supported_managers:
                logger.error("Unsupported Secrets Manager: {} supported options: {}".format(secret_config['secret_manager'],str(supported_managers)))
                raise Exception("Unsupported Secrets Manager: {}".format(secret_config['secret_manager']))
            elif secret_config['secret_manager'] not in supported_basic_managers:
                logger.debug("Secret not a basic Secrets : {} supported options: {}".format(secret_config['secret_manager'],str(supported_basic_managers)))
                return secret_config
            secret = None
            if secret_config['secret_manager'] == "local":
                secret = SecretManager.local_secret_request(secret_config)
            
            elif secret_config['secret_manager'] == "gcp":
                secret = SecretManager.gcp_secret_request(secret_config)
            
            # Validate an actual value has been returned
            if secret is None:
                logger.error("Invalid secret, None type returned")
                
            if '\n' in secret or '\r' in secret:
                logger.warning("[request_basic_secret] Warning Stripping newline character from secret. if secret legitamately contains \\n or \\r this will cause a loggin error")
                secret = secret.strip('\n')
                secret = secret.strip('\n')
            return secret
        except:
            logger.warning("Exception while requesting basic secret")
    
    def request_secret(secret_config):
        # check if the listed secret manager is supported 
        if secret_config['secret_manager'] not in supported_managers:
            logger.error("Unsupported Secrets Manager: {} supported options: {}".format(secret_config['secret_manager'],str(supported_managers)))
            raise Exception("Unsupported Secrets Manager: {}".format(secret_config['secret_manager']))
        
        secret = None
        if secret_config['secret_manager'] == "local":
            secret = SecretManager.local_secret_request(secret_config)

        elif secret_config['secret_manager'] == "thycotic":
            secret = SecretManager.thycotic_secret_request(secret_config)
        
        elif secret_config['secret_manager'] == "gcp":
            secret = SecretManager.gcp_secret_request(secret_config)

        # Validate an actual value has been returned
        if secret is None:
            logger.error("Invalid secret, None type returned")
            raise Exception("Invalid secret, None type returned")

        if type(secret) == str:
            if '\n' in secret or '\r' in secret:
                logger.warning("[request_basic_secret] Warning Stripping newline character from secret. if secret legitamately contains \\n or \\r this will cause a loggin error")
                secret = secret.strip('\n')
                secret = secret.strip('\n')
        return secret

    def local_secret_request(secret_config):
        if secret_config.keys() != local_format.keys():
            logger.error("secret config format error")
            raise Exception("secret config format issue")
        secret = None
        if secret_config['env_var'] in os.environ:
            secret = os.environ[secret_config['env_var']]
        else:
            logger.error("[secretManager.LocalClient] ENV not set on system: {}".format(secret_config['env_var']))
            #raise Exception("ENV not set")
        return secret
        

    def gcp_secret_request(secret_config):

        # reference: https://googleapis.dev/python/secretmanager/latest/secretmanager_v1/services.html
        if secret_config.keys() != gcp_format.keys():
                logger.error("secret config format error")
                raise Exception("secret config format issue")
        value = None
        logger.info("[gcp_secret_request] requesting secret {}".format(secret_config['secret_id']))
        # Create the Secret Manager client.
        client = gcp_secretmanager.SecretManagerServiceClient()

        # Build the resource name of the secret version.
        name = f"projects/{secret_config['project_id']}/secrets/{secret_config['secret_id']}/versions/{secret_config['version_id']}"

        # Access the secret version.
        try:
            response = client.access_secret_version(request={"name": name})
        except:
            logger.error("[GCP secret manager] Failed to load secret {}".format(name))
            raise Exception("[GCP secret manager] Failed to load secret {}".format(name))
        # Decode and return secret
        value = response.payload.data.decode("UTF-8")
        return value


        
    def thycotic_secret_request(secret_config):
        # Validate json format
        if secret_config.keys() != thycotic_format.keys():
            logger.error("secret config format error")
            raise Exception("invalid thycotic secret format")
        if secret_config['secret_type'] not in supported_tychotic_secrets:
                logger.error("Unsupported thycotic secret type:{}".format(secret_config['secret_type']))
                raise Exception("invalid thycotic secret type")

        # Load config for secret server instance
        # basic config load needs to be used as load_config function has a dependancy on SecretManager class
        logger.info("[thycotic_secret_request] loading thycotic config")
        config = load_basic_config(secret_config["config_header"])

        # instantiate client 
        secret_server = SecretServerCloud(**config)

        try:
            secret = secret_server.get_secret(secret_config['secret_id'])
            value = None
            for item in secret['items']:
                if item['slug'] == "username" and secret_config['secret_type'] == "username":
                    value = item['itemValue']
                    break
                elif item['isPassword'] and secret_config['secret_type'] == "password":
                    value = item['itemValue']
                    break
                elif item['fieldName'] == "JSON Private Key" and secret_config['secret_type'] == "gcp-key":
                    value = json.loads(item['itemValue'].content)
                    break
            return value
            
        except SecretServerAccessError as error:
            logger.error(error.message)
        except SecretServerError as error:
            logger.error(error.response.text)

    def azure_secret_request():
        # https://pypi.org/project/azure-keyvault-secrets/
        pass
