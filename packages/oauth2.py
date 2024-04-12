import os
import sys
import requests
import urllib

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .types import CustomDict
from .logger import CustomLogger as log


class OAuth2Flow():
    def __init__(self, endpoints: CustomDict):
        
        self.clientID = endpoints.id
        self.clientSecret = endpoints.secret
        self.authURL = endpoints.authURL
        self.tokenURL = endpoints.tokenURL
        self.scope = endpoints.requestURL + '/.default'
        self.username = endpoints.username
        self.password = endpoints.password

    
    def getSignInURL(self):
        log.debug('Generating OAuth2.0 Sign-In URL...')

        params = {
            'client_id': self.clientID,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:8000',
            'response_mode': 'query',
            'scope': self.scope,
            'state': '12345'
        }

        url = self.authURL + '?' + urllib.parse.urlencode(params)  

        return url
    
    @staticmethod
    def createBrowserEngine():
        options = webdriver.ChromeOptions()
        service = Service(ChromeDriverManager().install())

        options.headless = True
        options.add_argument("--disable-logging")
        options.add_experimental_option("excludeSwitches", ['enable-logging'])

        driver = webdriver.Chrome(service=service, options=options)

        return driver


    def login(self, url: str):
        log.state('Simulating OAuth2.0 Authorization Flow...')
        driver = self.createBrowserEngine()

        log.debug('Accessing Authorization Endpoint...')
        driver.get(url)

        log.debug('Entering Username...')
        usernameBox = EC.element_to_be_clickable((By.NAME, 'loginfmt'))
        username = WebDriverWait(driver, 10).until(usernameBox)
        username.send_keys(self.username)

        log.debug('Submitting Username...')
        nextButton = driver.find_element(By.ID, 'idSIButton9')
        nextButton.click()

        log.debug('Entering Password...')
        passwordBox = EC.element_to_be_clickable((By.NAME, 'passwd'))
        password = WebDriverWait(driver, 10).until(passwordBox)
        password.send_keys(self.password)

        log.debug('Submitting Password...')
        submitButton = driver.find_element(By.ID, 'idSIButton9')
        submitButton.click()


        log.debug('Bypassing "Stay Signed In" Prompt...')
        promptButton = EC.element_to_be_clickable((By.ID, 'idBtn_Back'))
        passthrough = WebDriverWait(driver, 10).until(promptButton)
        passthrough.click()

        log.debug('Capturing Authentication Code from Redirect URL...')
        WebDriverWait(driver, 10).until(EC.url_contains('http://localhost:8000'))
        url = urllib.parse.urlparse(driver.current_url).query
        query = urllib.parse.parse_qs(url)
        authcode = query['code'][0]

        log.state('Exiting Simulation Engine...')
        driver.quit()

        return authcode
    

    def getAccessToken(self, authcode: str):
        log.state('Converting Authorization Code into Access Token...') 

        data = {
            'client_id': self.clientID,
            'scope': self.scope,
            'client_secret': self.clientSecret,
            'grant_type': 'authorization_code',
            'code': authcode,
            'redirect_uri': 'http://localhost:8000'
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        if self.clientID:
            log.debug('Requesting Access Token...')
            token = requests.post(self.tokenURL, headers=headers, data=data)

            try:
                self.token = token.json()['access_token']
                log.debug('Retrieved Access Token...')

            except Exception as e:
                log.fatal(f'Terminating - Invalid Access Code Received')
                sys.exit(0)
        
        return self.token
    
        
    def authorize(self):
        url = self.getSignInURL()
        auth_code = self.login(url)
        access_token = self.getAccessToken(auth_code)

        return access_token