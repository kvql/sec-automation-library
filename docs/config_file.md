# Config File


## options

The below table shows the default config values

| key           | Used by function | Default value         |  Other options    | Purpose           |
| :---          | :---                  | :---                  | :---          | :---          |
| environment   | Data Manager | local                 | gcp           | Defines where data is stored by DataManager |
| proxy         |Config manager | ""                    | Free form    | Proxy value which will be set in environment proxy vaues |
| dry_run | Any | False| True | Some functions use this to prevent unit tests from runing production actions. Example vulnerabiltiy management unit tests. 
| approved_dns | GCP | None | list of domain strings| Used by gcp functions to validate if a domain is owned. If a domain is not on the list it will not be parsed |
| datapath | Data Manager | /tmp | any local path | Directory where data is stored if environment is set to "local"|
|azure.subscription_exclusions | Azure | None | List of subsciption names| Azure has built in subscriptions which are not used by our tenant. These should be excluded as there is nothing in them that we control. Any subscription in this list will be excluded when subs are listed |


Above are the main config keys however other function could require their own config item. The config for those functions will be documented with the function. 



## Environment Variable overide

you can overide the config file by setting an environment variable. 

The environment variable name is the json key prefixed with "sa_"
For example: 

```json
{
    "vuln_scanner": {
        "password": "abc"
    }
}
```
If you set an environment variable as shown below the load_config function will prioritise the environment value

```bash
export sa_vuln_scanner_password="cba"
```

## limitations

### config file depth

key can only be 1 or 2 levels deep

NB the only exception to this is if the third level json object is a secret definition

**Allowed:**  
key values:  
vuln_scanner  
vuln_scanner.password  

Example config:

```json
{
    "vuln_scanner": {
        "password": "abc"
    },
    "environment": "local"
}
```

**Not allowed**
key values:  
gfh.vuln_scanner.password 

Example config:

```json
{
    "gfh": {
        "vuln_scanner": {
                "password": "abc"
        }
    },
    "environment": "local"
}
```

---

## Defining Secrets

There are two type of secrets manager clients, basic and advanced.
This is due to advanced secret manager clients requiring a secret to access them. 

basic clients do not need a secret configured in the config file. 


To define a secret you just replace the secret value in the config file with the json object describing how to retrieve the secret. 

Supported clients

- Basic clients
  - local
  - GCP secrets manager
- Advanced clients
  - thycotic secret server

## local

Supported secret types:

- string

### Usage in config file

You can leave the value as a plain string and set the environment overide (see section above) or set the environment variable name as shown below

Worst practice - hard coded password:

```json
{
    "password": "password123"
} 
```

Better Practice:

```json
{
    "password": {
        "secret_manager": "local",
        "env_var": "vuln_scanner_pass"
        },
```

or

```json
{
    "password":""
} 
```

## GCP client

Supported secret types:

- string

### Usage in config file

```json
{
    "password":{
            "secret_manager": "gcp",
            "project_id": "",
            "secret_id": "",
            "version_id": "latest"
},
```

## thycotic

Supported secret types:

- string
- gcp key

### Usage in config file

secret_type referes to the field in thycotic secret which will be returned. 
The client in this package supports the following values
- username
- password
- gcp-key

config_header referes the to the key where the settings for accessing the secret server api are stored in the config file.

NB if you are having issues
1. ensure the account you are using to access the api with has access to the secret you are pulling
2. ensure the account isn't locked. failing unit tests can easily lock the account if a password is wrong.

```json
{
    "client_id": {
        "secret_manager": "thycotic",
        "secret_id":"1234",
        "secret_type": "username",
        "config_header": "thycotic"
    },
    "client_secret": {
        "secret_manager": "thycotic",
        "secret_id":"1234",
        "secret_type": "password",
        "config_header": "thycotic"
    },
    "key_path": {
        "secret_manager": "thycotic",
        "config_header": "thycotic",
        "secret_id":"1234",
        "secret_type": "gcp-key"
    },
    "thycotic": {
        "tenant": "",
        "username": "",
        "password": "",
        "tld": "eu"
    },
}