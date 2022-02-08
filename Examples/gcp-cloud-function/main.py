
import logging
import time
import os
import json
from flask import escape
from sec_automation.orchestrator import Orchestrator
import sec_automation.configmanager as cm
from sec_automation.datamanager import DataManager
import sec_automation.functions as functions


# Set proxy variables
cm.load_config('proxy')

# Create loggers
log_level = cm.load_config('log_level')
logger = functions.create_logger("app", log_level)
functions.create_logger("secops_automation", log_level)

    
    

# def gcp_http_trigger(request):
#     """HTTP Cloud Function.
#     Args:
#         request (flask.Request): The request object.
#         <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
#     Returns:
#         The response text, or any set of values that can be turned into a
#         Response object using `make_response`
#         <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
#     """
#     request_json = request.get_json(silent=True)
#     request_args = request.args

#     if request_json and 'command' in request_json:
#         command = request_json['command']
#     elif request_args and 'command' in request_args:
#         command = request_args['command']
#     else:
#         logger.error("No valid command provided")
#         exit(1)
    
#     os.environ['sa_environment'] = "gcp"
#     #os.environ['sa_gcp_bucket'] = event['bucket']
#     orchestrator = Orchestrator()
#     orchestrator.getdata(command=command)
    

def gcp_bucket_trigger(event, context):
    """Background Cloud Function to be triggered by Cloud Storage.
       This generic function logs relevant data when a file is changed.

    Args:
        event (dict):  The dictionary with data specific to this type of event.
                       The `data` field contains a description of the event in
                       the Cloud Storage `object` format described here:
                       https://cloud.google.com/storage/docs/json_api/v1/objects#resource
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    os.environ['sa_environment'] = "gcp"
    os.environ['sa_gcp_bucket'] = event['bucket']
    orchestrator = Orchestrator()
    orchestrator.dataaction(file_name=event['name'])
    logger.info("[gcp_bucket_trigger] Excution complete")
    

    