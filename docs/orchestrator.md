# Orchestrator

This function allows you to have a generic script and control it with a config file. To add a new command to the script just add a function to a file and update the config file.

## Benefits
The benfits of using this class are:

- functionality can be added without modifying existing code
- format of data is validated before being actioned, useful if you are reading data from a file.
- You can remove functions from the script by just modifying the config file

# Requirements

The below requirements:
- standard file structure
- main.py file (doesn't need to be called main unless running in cloud function)
- requirements file
- config file and data map file
## File structure

```
script directory
| main.py  
| requirements.txt  
|___config_data  
|   |   config.json  
|   |   data_actions_mapping.json
|
|___app
    |   <python file>
    |   ...
```


The orchestrator class is designed to 



# Example use

