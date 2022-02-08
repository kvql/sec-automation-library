import json
import os
import time
import glob
from copy import deepcopy
import sec_automation.configmanager as cm
from google.cloud import storage
from sys import exit


import logging
logger= logging.getLogger(__name__)

dataformat={
    "datatype":"",
    "page":0,
    "totalpages":0,
    "data":{}
}

config_key="environment"

'''
DataManage Class. The purpose of this is to abstract some of the low level code related to interacting with the environment away from the other packages in the app.
Therefore if you needed to modify the app to run in Azure, you can just add a new Class to this package 
but the DataManager class and all other packages in the app would not need to be changed
'''
class DataManager():

    def __init__(self):
        
        env=cm.load_config(config_key)

        if env == "local":
            self.client=LocalClient()
        elif env == "gcp":
            self.client=GcpClient()
        else:
            logger.error("invalid environment")
            raise Exception("Invalid environment")
        
        # load data types to allow for data format validation
        self.options=cm.data_options()
        logger.debug("data manager instantiation complete")

    
    ######
    # Functions used by orchestrator class
    ######
    def loadfile(self,filename):
        data = self.client.loadfile(filename)
        logger.debug("[DataManager.loadfile]file loaded {}".format(filename))
        if type(data) == str:
            try:
                data = json.loads(data)
            except:
                logger.error("data not valid json")
        elif type(data) == dict:
            logger.debug("data already in dict type")
        else:
            raise Exception("Data in unknown type")
        self.validate_data(data)
        logger.debug("[DataManager.loadfile] file validated")
        return data
    
    def storefile(self,data: dict,datatype):
        filedata=deepcopy(dataformat)
        logger.debug("[DataManager.storefile] data validated")
        filedata['datatype'] = datatype
        filedata['data'] = data
        self.validate_data(filedata)
        filename="sa_datafile_"+str(int(time.time())) + ".json"
        self.client.storefile(json.dumps(filedata),filename)
        logger.debug("[DataManager.storefile] data written to file")
    
    def cachefile(self,data: dict,datatype):
        '''
        Method to return the data as if it was read from a file but without ever storing it. 

        used when data is being directly actions and not written to disk or another storage location
        '''
        filedata=deepcopy(dataformat)
        logger.debug("[DataManager.storefile] data validated")
        filedata['datatype'] = datatype
        filedata['data'] = data
        self.validate_data(filedata)
        return filedata
        
    #####
    # Supporting functions for data validation
    #####
    def validate_data(self,data:dict):
        '''
        Method to validate the data structure used when saving or loading to file. 
        This method does uses the datatype method to validate the acutal data being saved. 
        '''
        valid = True
        if sorted(dataformat.keys()) != sorted(data.keys()):
            valid = False
            logger.error("invalid data structure")
            raise Exception("invalid data structure")
        if not self.validate_datatype(data['data'],data['datatype']):
            valid = False
            logger.error("Invalid data type, {} or structure".format(data["datatype"]))
            logger.debug("datatype keys {}".format(data['data'].keys()))
            raise Exception("invalid data type structure")
        return valid

    def validate_datatype(self,data: dict,datatype: str):
        '''
        Method to validate the datatype is a valid type and that
        the data format is correct when a specified format has been given in the options file
        '''
        try:
            if datatype not in self.options['datatypes'].keys():
                return False
            else:
                # Check if datatype has a dataformat defined
                options_datatype = self.options['datatypes'][datatype]
                if type(options_datatype['dataformat']) == str:
                    if options_datatype['dataformat'] == "None":
                        return True
                    else:
                        dataformat = self.options["dataformats"][options_datatype['dataformat']]
                        if sorted(data.keys()) == sorted(dataformat.keys()):
                            #TODO Validate the key values types. eg. if we expect a string validate you get a string
                            return True
                        else:
                            return False
                elif sorted(data.keys()) == sorted(options_datatype['dataformat'].keys()):
                    #TODO Validate the key values types. eg. if we expect a string validate you get a string
                    return True
                else:
                    return False
        except:
            logger.error("[DataManager.validate_datatype] Issue with datatype validation")
            raise Exception("Issue with datatype validation")
        
####################
# Environment specific Client - Local
####################
'''
Client for loading and saving files locally on endpoing or server where the code is run
'''
class LocalClient:
    def __init__(self):
        self.path = cm.load_config("datapath")
        
        if not os.path.exists(self.path):
            raise Exception("Path doesn't exist")
            
        # # make local data folder
        self.path = self.path + "/sa_data/"
        if os.path.isdir(self.path) == False:
            os.mkdir(self.path)
            logger.info("Local Data folder created")
        
    
    def latestfile(self):
        list_of_files = glob.glob(self.path+"*")  # You may use iglob in Python3
        logger.debug("list of files: {}".format(str(list_of_files)))
        if not list_of_files:
            logger.error("No data files")              
            raise Exception("No data files") 
        
        latest_file = max(list_of_files, key=os.path.getctime)
        logger.info("Latest file: {}".format(os.path.basename(latest_file)))
        return os.path.basename(latest_file)
    
    def loadfile(self,file):
        list_of_files = glob.glob(self.path)  # You may use iglob in Python3
        if not list_of_files:               
            raise Exception("No data files")                      
        #latest_file = max(list_of_files, key=os.path.getctime)
        file_path = self.path +'/'+ file
        data = None
        with open(file_path, 'r') as f:
            try:
                data = json.loads(f.read())
            except Exception as e:
                logger.error("Unexpected error")
                logger.error(e, exc_info=True)
        #os.remove(file_path)
        
        return data
         
    def storefile(self,data,filename):
        try:
            filepath=self.path+"/"+filename
            if os.path.isfile(filepath):
                os.remove(filepath)
                logger.info("existing data file deleted")
            with open(filepath, 'w') as outfile:
                json.dump(data, outfile)
                logger.info("File written {}".format(filename))
        except Exception as e:
            logger.error("Unexpected error")
            logger.error(e, exc_info=True)

####################
# Environment specific Client - GCP
####################
'''
Client for loading and saving files in a GCP bucket
'''



class GcpClient:
    def __init__(self):
        self.config = cm.load_config("gcp")
        self.storage_client = storage.Client(project=self.config['project_id'])
        try:
            self.bucket = self.storage_client.get_bucket(self.config['bucket_id'])
            logger.debug("initiated client for bucket: {}".format(self.config['bucket_id']))
        except Exception as e:
            logger.error("GCP Bucket not found or error in code")
            logger.debug(e, exc_info=True)

    def storefile(self,data:str,filename:str):
        """Uploads a file to the bucket."""
        # bucket_name = "your-bucket-name"
        # source_file_name = "local/path/to/file"
        # destination_blob_name = "storage-object-name"

        blob = self.bucket.blob(filename)
        blob.upload_from_string(data)
        #blob.upload_from_filename(filename)
            #self.tmp_filenames_to_clean_up.append(filename)
    
    def loadfile(self, filename):
        logger.info('Reading file: {}'.format(filename))
        
        blob = self.bucket.blob(filename)
        
        content = blob.download_as_bytes().decode("utf-8")
        return content

        #self.response.write(contents)





