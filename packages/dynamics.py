import os
import json
import requests

from .types import CustomDict
from .oauth2 import OAuth2Flow
from .logger import CustomLogger as log


class Dynamics365():
    token: str = None
    version: str = "api/data/v9.2/" 

    exportDir = os.path.abspath(__file__).replace('packages\\dynamics.py', 'Exports\\accounts.json')
    
    def __init__(self, endpoints: CustomDict, return_raw: bool = False, format_values: bool = True):
        self.accounts = []
        
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
    
    def request(self, url: str, *, batch: int = 0) -> json:
        log.trace(f'Requesting Batch No. {batch}')

        headers = {
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0'
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            log.debug(f'Batch Request Successful - ID {batch}')
        
        data = response.json()

        self.accounts.extend(data["value"])

        return data

    
    def authenticate(self):
        log.state('Simulating OAuth2.0 Authorization Flow...')
        self.token = self.OAuthFlow.authorize()
    
    def getRequestURL(self, entity):
        return f'{self.baseURL}{self.version}/{entity}/'

    def getAccounts(self):
        log.debug('Requesting [dbo.Accounts] Table...')


        url = self.getRequestURL('accounts') + "?$select=accountnumber,new_storestatus&$filter=statuscode eq 1"
        response = self.request(url)

        batchid = 1

        while "@odata.nextLink" in response:
            response = self.request(response["@odata.nextLink"], batch=batchid)
            batchid += 1

        log.debug('Writing Account Data...')
        with open(self.exportDir, 'w+') as savefile:
            json.dump(self.accounts, savefile, indent=4)
        
        return self.accounts




    
