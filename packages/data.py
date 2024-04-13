import os

import pandas as pd

from dotenv import load_dotenv

from . import queries
from .types import CustomDict
from .database import Database
from .dynamics import Dynamics365
from .logger import CustomLogger as log


class Analytics():

    @staticmethod
    def TrendVar(x, y):
        result = None

        if x <= 0 or x is None:
            result = None
        elif y == 0 or y is None:
            result = x
        else:
            result = y-x
        
        log.trace(f'Assigned Trend Variance of {result}')
        return result

    
    @staticmethod
    def MonthVar(x, y):
        result = None

        if x <= 0 or x is None:
            result = None
        elif y == 0 or y is None:
            result = x
        else:
            result = y-x
        
        log.trace(f'Assigned MoM Variance of {result}')
        return result
    
    @staticmethod
    def TrendDelta(x, y):
        result = None

        if x <= 0 or x is None:
            result = None
        elif y == 0 or y is None:
            result = -1
        else:
            try:
                result = round((y/x), 2)
            except ValueError:
                result = 0
        
        log.trace(f'Assigned Trend Variance % of {result}')

        return result
    
    @staticmethod
    def MonthDelta(x, y):
        result = None

        if x <= 0 or x is None:
            result = None
        elif y == 0 or y is None:
            result = -1
        else:
            try:
                result = round((y/x), 2)
            except ValueError:
                result = 0
        
        log.trace(f'Assigned MoM Variance % of {result}')

        return result

class Movement():

    db: Database = Database()

    @classmethod
    def getRecords(cls) -> pd.DataFrame:
        results = cls.db.execute(queries.fetch_all)

        return results
    
    @staticmethod
    def segregate(data, cutoff: list) -> CustomDict:
        log.debug(f'Segregating Data using Cutoff Period: {cutoff}')

        historical = data[~data['ReportPeriod'].isin(cutoff)]
        current = data[data['ReportPeriod'].isin(cutoff)]

        package = {
            "historical": historical,
            "current": current
        }

        return CustomDict(package)

    @staticmethod
    def aggregate(data: pd.DataFrame):
        log.debug('Condensing Dataset into Unique [StoreNumber.UPC.ReportPeriod] keys')
        summarized = data.groupby(['StoreNumber', 'UPC', 'ReportPeriod'], as_index=False)['Qty'].sum()

        return summarized

    @staticmethod
    def summarize(data: pd.DataFrame) -> pd.DataFrame:
        log.debug('Averaging Dataset into unique [StoreNumber.UPC] pairs')
        average = data.groupby(['StoreNumber', 'UPC'], as_index=False)['Qty'].mean()
        average['Qty'] = pd.to_numeric(average['Qty'], errors='coerce')

        return average

    @staticmethod
    def compareTrend(*, trend: pd.DataFrame, previous: pd.DataFrame, current: pd.DataFrame):
        log.debug('Merging Trend and LastMonth Datasets...')      
        df = trend.merge(
            previous[['StoreNumber', 'UPC', 'Qty']],
            how='left',
            on=['StoreNumber', 'UPC']
        )
        
        log.debug('Adding CurrentMonth Dataset...')
        comparison = df.merge(
            current[['StoreNumber', 'UPC', 'Qty']],
            how='left',
            on=['StoreNumber', 'UPC']
        )

        comparison.columns = ['StoreNumber', 'UPC', 'Trend', 'LastMonth', 'CurrentMonth']

        log.state('Analyzing Performance Deltas...')

        log.debug('Creating Comparison of Average Historical Trend to Current Month')
        comparison['TrendVar'] = comparison.apply(
            lambda x: Analytics.TrendVar(x['Trend'], x['CurrentMonth']),
            axis=1
        )

        log.debug('Creating Comparison of LastMonth to Current Month')
        comparison['MonthVar'] = comparison.apply(
            lambda x: Analytics.MonthVar(x['LastMonth'], x['CurrentMonth']),
            axis=1
        )

        log.debug('Creating Comparison of Average Historical Trend to Current Month as a %')
        comparison['Trend%'] = comparison.apply(
            lambda x: Analytics.TrendDelta(x['Trend'], x['CurrentMonth']),
            axis=1
        )

        log.debug('Creating Comparison of LastMonth to Current Month as a %')
        comparison['Month%'] = comparison.apply(
            lambda x: Analytics.MonthDelta(x['LastMonth'], x['CurrentMonth']),
            axis=1
        )


        return comparison

    @staticmethod
    def showWarnings(data: pd.DataFrame):
        df = data.loc[(
            ((data['Trend%'] < 0.8) & (data['TrendVar'] < -10)) |
            ((data['Month%'] < 0.8) & (data['MonthVar'] < -10)) |
            ((data['CurrentMonth'] == 0) & (data['Trend'] > 10)) |
            ((data['CurrentMonth'].isnull()) & (data['Trend'] > 10)) |
            ((data['CurrentMonth'] == 0) & (data['LastMonth'] > 10)) |
            ((data['CurrentMonth'].isnull()) & (data['LastMonth'] > 10))
        )]
        

        return df
    
    @staticmethod
    def clean(data: pd.DataFrame):
        original = data.shape[0]
        report = data.drop_duplicates(subset=['StoreNumber', 'UPC'], keep='first')

        log.debug(f'Removed {original - report.shape[0]} duplicate values')

        return report


class Dynamics():

    def __init__(self):
        self.connection = self.ConnectToDynamics365()
        self.authenticate()

    @staticmethod
    def ConnectToDynamics365() -> Dynamics365:
        load_dotenv()

        package = {
            'requestURL': os.getenv('RequestEndpointCRM'),
            'tokenURL': os.getenv('TokenEndpointCRM'),
            'authURL': os.getenv('AuthEndpointCRM'),
            'id': os.getenv('AppIdCRM'),
            'secret': os.getenv('AppSecretCRM'),
            'username': os.getenv('UsernameCRM'),
            'password': os.getenv('PasswordCRM')
        }

        endpoints = CustomDict(package)

        connection = Dynamics365(endpoints)

        return connection
    
    def authenticate(self):
        self.connection.authenticate()

    def get_accounts(self):
        accounts = self.connection.getAccounts()
        if accounts is None:
            log.issue('Failed to Retrieve Account Data')
            return None, None

        active = [
            record["accountnumber"]
            for record in accounts["value"]
        ]

        expected = [
            record["accountnumber"] 
            for record in accounts["value"]
            if record["new_storestatus"] not in [100000008, 100000006, 100000005]
        ]

        return active, expected
