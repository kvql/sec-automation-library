
import json
import urllib.request
import urllib.parse

logger= logging.getLogger(__name__)

class defender():
    self.aadToken=""
    def _init_(self,tenantId, appId, appSecret):
        
        url = "https://login.windows.net/%s/oauth2/token" % (tenantId)
        resourceAppIdUri = 'https://api.securitycenter.windows.com'   

        body = {
            'resource' : resourceAppIdUri,
            'client_id' : appId,
            'client_secret' : appSecret,
            'grant_type' : 'client_credentials'
        }  

        data = urllib.parse.urlencode(body).encode("utf-8")
        req = urllib.request.Request(url, data)
        response = urllib.request.urlopen(req)
        jsonResponse = json.loads(response.read())
        aadToken = jsonResponse["access_token"]
       

def wdatp_get_alerts(self):
    url = "https://api.securitycenter.windows.com/api/alerts"
    headers = {
        'Content-Type' : 'application/json',
        'Accept' : 'application/json',
        'Authorization' : "Bearer " + aadToken
    }

    req = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(req)
    jsonResponse = json.loads(response.read())
    return jsonResponse["value"]