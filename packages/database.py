import os
import sys
import pyodbc

import pandas as pd

from dotenv import load_dotenv

from .types import CustomDict
from .dynamics import Dynamics365
from .logger import CustomLogger as log


class Database():
    def __init__(self):
        self.cursor: pyodbc.Cursor = None
        self.connection: pyodbc.Connection = None

        self.env: CustomDict = self._loadEnv()
        self.structure: list = self._structure()

        self.connect()
    
    @staticmethod
    def _structure():
        build = [
            "ID",
            "WholesalerID",
            "CustomerID",
            "StoreNumber",
            "CustomerName",
            "Address",
            "City",
            "State",
            "Zipcode",
            "Description",
            "Qty",
            "UPC",
            "UnitPrice",
            "LIC",
            "ReportPeriod"
        ]

        return build
    
    @staticmethod
    def _loadEnv():
        log.debug('Loading Database Credentials from .env file...')

        load_dotenv()

        vars = {
            'server': os.getenv('ServerDB'),
            'database': os.getenv('DatabaseDB'),
            'username': os.getenv('UsernameDB'),
            'password': os.getenv('PasswordDB')
        }

        if any([vars[key] is None for key in vars]):
            missing = [key for key in vars if vars[key] is None]

            log.fatal(f'Missing Required Environment Variable: {missing}')
            sys.exit(0)

        return CustomDict(vars)
    
    @staticmethod
    def _getConnectionString(system: CustomDict) -> str:
        log.debug('Generating SQL Server Connection String...')

        dsn = f'''
            DRIVER={{ODBC Driver 18 for SQL Server}};
            SERVER={system.server};
            DATABASE={system.database};
            UID={system.username};
            PWD={system.password};
            TrustServerCertificate=yes;
        '''

        return dsn
    
    def connect(self):
        dsn = self._getConnectionString(self.env)

        log.debug('Attempting to Connect to SQL Server...')

        try:
            self.connection = pyodbc.connect(dsn)
            self.cursor = self.connection.cursor()
            log.state('Established a Connection to SQL Server')
        except Exception as e:
            log.error('ODBC Driver 18 for SQL Server could not open a connection: server not found')

            log.fatal('Failed to Connect to SQL Server - Terminating...')
            sys.exit(0)

        return

    def execute(self, query: str):
        log.debug('Reading Database...')
        records = pd.read_sql(query, self.connection)

        return records
