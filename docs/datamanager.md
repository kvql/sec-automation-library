# Data Manager

This package provides one primary Class. The purpose of this is to abstract where you are writing and reading file away from your code.

***NB: while the data is written to file in json, the python variable type you interact with is "dict"***

This class currently supports the following storage locations:

1. local disk (environment: local)
2. GCP bucket (environment: gcp)

Where the data is written is configured in the config file


## Data format

This class currently only supports one format, json

files are written in a standard format shown below:

```json
{
    "datatype":"",
    "page":0,
    "totalpages":0,
    "data":{}
}
```

The page fields aren't currently used for anything but were added in case paging was needed for large datasets

The datatype field essentially specifies the source and structure of the data stored in the data field.

The datamanager class performs validation of the data being saved by looking up the data structure for the specified datatype in the data_mappings file.

### Data types and data mapings file

**None**  
if the structure of the data is not known then 



## Local 
