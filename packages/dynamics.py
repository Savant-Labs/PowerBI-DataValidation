import json
import requests

from .types import CustomDict
from .oauth2 import OAuth2Flow
from .logger import CustomLogger as log


class Dynamics365():
    token: str = None
    version: str = "api/data/v9.2/" 
    
    def __init__(self, endpoints: CustomDict, return_raw: bool = False, format_values: bool = True):
        
        self._baseURL = endpoints.requestURL
        self.clientID = endpoints.id
        self.clientSecret = endpoints.secret
        self.username = endpoints.username
        self.password = endpoints.password
        self.authURL = endpoints.authURL

        self.rawValues = return_raw
        self.formatValues = format_values

        self.OAuthFlow = OAuth2Flow(endpoints)

    @property
    def baseURL(self):
        if self._baseURL.endswith('/'):
            return self._baseURL
        return self._baseURL + '/'
    
    def authenticate(self):
        log.state('Simulating OAuth2.0 Authorization Flow...')
        self.token = self.OAuthFlow.authorize()
    
    def getRequestURL(self, entity):
        return f'{self.baseURL}{self.version}/{entity}/'


    def getAccounts(self):
        log.debug('Requesting [dbo.Accounts] Table...')

        headers = {
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0'
        }

        url = self.getRequestURL('accounts') + f'$select=accountnumber,new_storestatus'
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            log.debug('Data Request Successful')
            log.debug('Exporting Account Data to JSON...')

            with open('Exports/accounts.json', 'w+') as file:
                json.dump(response.json(), file, indent=4)
                file.close()
            
        else:
            log.error(f'Request Returned with Response Code: {response.status_code}')
            return None

        return response.json()




    
