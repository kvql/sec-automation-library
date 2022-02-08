import os
import json
from sec_automation.datamanager import DataManager 
import sec_automation.configmanager as cm
import importlib
from sys import exit
from copy import deepcopy
#from app.data.gcp_data import gcp_data


import logging
logger = logging.getLogger(__name__)
# ch = logging.StreamHandler() # console handler
# ch.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(levelname)s - %(name)s -  %(message)s') 
# ch.setFormatter(formatter) # add formatter

# # add ch & fh to logger
# logger.addHandler(ch)

class Orchestrator():
    def __init__(self):
        self.options=cm.data_options()
        self.dm = DataManager()
        logger.debug("orchestrator instantiation complete")

    def getdata(self,command=None, datatype=None):
        logger.debug("start of Orchestrator getData function")
        data_array = []
        if command==None and datatype==None:
            logger.error("You must specify either a Command or Datatype")
            raise Exception("You must specify either a Command or Datatype")
        try:
            if command != None and self.validate_command(command):
                # pull list of required datatypes for this command
                datatypes=self.options['commands'][command]['datatypes']
                logger.debug("datatypes loaded for command: {}, datatypes: {}".format(command,datatypes))
                # Iterate through datatypes to pull the data
                for dt in datatypes:
                    #function to take datatype map it to a package and functiona and call this functions
                    data = self.trigger_datatype_request(dt)
                    logger.debug("data retrieved for datatype: {}".format(dt))
                    # some functions return an array of data. e.g. azure as we have multiple tenants
                    if type(data) == dict:
                        data_array.append(deepcopy(self.dm.storefile(data,dt)))
                        logger.debug("data stored")
                    elif type(data) == list:
                        logger.info("Multiple data sets returned for datatype {}".format)
                        for data_object in data:
                            data_array.append(deepcopy(self.dm.storefile(data_object,dt)))
                            logger.debug("data stored")
                    else:
                        logger.error("unknown type for returned data. type: {}".format(type(data)))
                        exit(1)
            elif datatype != None and self.validate_datatype(datatype):
                    data = self.trigger_datatype_request(datatype)
                    # some functions return an array of data. e.g. azure as we have multiple tenants
                    if type(data) == dict:
                        data_array.append(deepcopy(self.dm.storefile(data,datatype)))
                        logger.debug("data stored")
                    elif type(data) == list:
                        logger.info("Multiple data sets returned for datatype {}".format)
                        for data_object in data:
                            data_array.append(deepcopy(self.dm.storefile(data_object,datatype)))
                            logger.debug("data stored")
                    else:
                        logger.error("unknown type for returned data. type: {}".format(type(data)))
                        exit(1)
            logger.info("[Orchestrator.getData] Data Request Complete")
        except Exception as e:
            logger.error("Unknown Error")
            logger.error(e, exc_info=True)
            exit(1)

    def command(self, command=None):
        '''
        Function to gather data related to command and then run the command action without writing to disk
        '''
        logger.debug("start of Orchestrator command function")
        data_array = []
        if command==None :
            logger.error("You must specify either a Command")
            raise Exception("You must specify either a Command")
        try:
            if command != None and self.validate_command(command):
                # pull list of required datatypes for this command
                datatypes=self.options['commands'][command]['datatypes']
                logger.debug("datatypes loaded for command: {}, datatypes: {}".format(command,datatypes))
                # Iterate through datatypes to pull the data
                if len(datatypes)>0:
                    for dt in datatypes:
                        #function to take datatype map it to a package and functiona and call this functions
                        data = self.trigger_datatype_request(dt)
                        logger.debug("data retrieved for datatype: {}".format(dt))
                        # using deepcopy to ensure a pointer isn't returned
                        if type(data) == dict:
                            data_array.append(deepcopy(self.dm.cachefile(data,dt)))
                            logger.debug("data stored")
                        elif type(data) == list:
                            logger.info("Multiple data sets returned for datatype {}".format)
                            for data_object in data:
                                data_array.append(deepcopy(self.dm.cachefile(data_object,dt)))
                                logger.debug("data stored")
                        else:
                            logger.error("unknown type for returned data. type: {}".format(type(data)))
                            exit(1)
                        
                    logger.info("[Orchestrator.command] Data Request Complete")
                    ###
                    # Executing the command now that the data is gathered
                    logger.info("[Orchestrator.command] Starting to action data")
                    
                    for data in data_array:
                        datatype = data['datatype']
                        logger.info("[Orchestrator.dataaction] Actioning datatype {}".format(datatype))
                        app = self.options['commands'][command]['app']
                        module = importlib.import_module(app)
                        try:
                            method = getattr(module, command)
                        except AttributeError:
                            raise NotImplementedError("Class `{}` does not implement `{}`".format(option['app'], datatype))
                        method(data)
                    logger.info("[Orchestrator.dataaction] Data Actions Complete")
                else:
                    # Action command that takes no data input
                    logger.info("[Orchestrator.dataaction] Actioning command {} without any data".format(command))
                    app = self.options['commands'][command]['app']
                    module = importlib.import_module(app)
                    try:
                        method = getattr(module, command)
                    except AttributeError:
                        raise NotImplementedError("Class `{}` does not implement `{}`".format(option['app'], datatype))
                    method()
                    logger.info("[Orchestrator.dataaction] Data Actions Complete")
        except Exception as e:
            logger.error("Unknown Error")
            logger.error(e, exc_info=True)
            exit(1)


    def dataaction(self,file_name=None, build_queue=False):
        'Top level function which will be called by main package'
        if file_name==None and build_queue==False:
            logger.error("You must specify either file name or Build Queue")
            raise Exception("You must specify either file name or Build Queue")
        
        data = self.dm.loadfile(file_name)

        datatype = data['datatype']
        commands = cm.related_commands(datatype)
        for command in commands:
            app = self.options['commands'][command]['app']
            option = self.options['datatypes'][datatype]
            module = importlib.import_module(app)
            try:
                method = getattr(module, command)
            except AttributeError:
                raise NotImplementedError("Class `{}` does not implement `{}`".format(option['app'], datatype))
            method(data)
        logger.info("[Orchestrator.dataaction] Data Actions Complete")

########################
# Supporting Methods
########################

    def action_data(data):
        datatype = data['datatype']
        commands = cm.related_commands(datatype)
        for command in commands:
            app = self.options['commands'][command]['app']
            option = self.options['datatypes'][datatype]
            module = importlib.import_module(app)
            try:
                method = getattr(module, command)
            except AttributeError:
                raise NotImplementedError("Class `{}` does not implement `{}`".format(option['app'], datatype))
            method(data)
        logger.info("[Orchestrator.dataaction] Data Actions Complete")

    def trigger_datatype_request(self,datatype):
        '''
        Functions to call the related function based on datatype. 
        Intput is datatype as a string. 

        The options file has a mapping between datatype and the related python module which pulls that datatype
        '''

        option = self.options['datatypes'][datatype]

        # reference: https://stackoverflow.com/questions/4821104/dynamic-instantiation-from-string-name-of-a-class-in-dynamically-imported-module
        # reference: https://stackoverflow.com/questions/7936572/python-call-a-function-from-string-name/7936588
        
        #Import package based on app name in mapping file
        module = importlib.import_module(option['app'])
        logger.info("loading module: {}".format(module))
        try:
            method = getattr(module, datatype)
            data = method()
        except AttributeError:
            logger.critical("Class `{}` does not implement `{}`".format(option['app'], datatype))
            raise NotImplementedError("Class `{}` does not implement `{}`".format(option['app'], datatype))
        return data

    def validate_command(self,command):
        valid=True
        if command not in self.options['commands']:
            valid = False
            logger.error("[Orchestrator.validate_command] Invalid Command {}".format(command))
            raise Exception("[Orchestrator.validate_command] Invalid Command")
        return valid

    def validate_datatype(self,datatype):
        valid=True
        if datatype not in self.options['datatypes'].keys():
            valid = False
            logger.error("[Orchestrator.validate_datatype] Invalid datatype {} -- Valid datatypes:{}".format(datatype,self.options['datatypes'].keys()))
            raise Exception("[Orchestrator.validate_datatype] Invalid Datatype")
        return valid
