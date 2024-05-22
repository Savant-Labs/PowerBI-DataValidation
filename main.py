import warnings

from os.path import abspath
from pandas import DataFrame

from packages import data
from packages import logger

from packages.types import CustomDict


warnings.simplefilter('ignore', UserWarning)

exportDir = abspath(__file__).replace('main.py', 'Exports\\')
log = logger.CustomLogger
logger.setup()


class ControlFlow():

    Movement = data.Movement
    Dynamics = data.Dynamics()

    previous = ["1/31/2024 12:00:00 AM", "2/29/2024 12:00:00 AM", "3/31/2024 12:00:00 AM"]
    timestamp = ["4/30/2024 12:00:00 AM", ]
    date = timestamp[0].split()[0].replace('/', '-')

    @classmethod
    def retrieve(cls) -> CustomDict:
        log.debug('Fetching Database Records...  (this may take a while)')
        raw = cls.Movement.getRecords()

        log.state('Separating Composite Datasets...')
        filtered = cls.Movement.segregate(raw, cls.timestamp)
        retroactive = cls.Movement.segregate(filtered.historical, cls.previous)

        log.state('Condensing to Aggregate Datasets...')
        _current = cls.Movement.aggregate(filtered.current)
        _previous = cls.Movement.aggregate(retroactive.current)
        _historical = cls.Movement.aggregate(retroactive.historical)

        log.state('Determining Historical Patterns...')
        current = cls.Movement.summarize(_current)
        previous = cls.Movement.summarize(_previous)
        historical = cls.Movement.summarize(_historical)

        package = {
            'current': current,
            'previous': previous,
            'historical': historical
        }

        return CustomDict(package)
    
    
    @classmethod
    def analyze(cls, package: CustomDict) -> DataFrame:
        log.debug('Comparing Current Month to Other Datasets...')
        comparison = cls.Movement.compareTrend(
            trend=package.historical,
            previous=package.previous,
            current=package.current
        )

        try:
            comparison.to_csv(exportDir + "unfiltered.csv")
        except PermissionError:
            log.issue('Failed to export Unfiltered Frame to CSV - File is Open')

        log.debug('Identifying Potential Discrepancies...')
        flagged = cls.Movement.showWarnings(comparison)

        return flagged

    @classmethod
    def filter(cls, package: DataFrame):
        log.debug('Filtering to Relevant Discrepancies...')

        log.debug('Removing Duplicates...')
        report = cls.Movement.clean(package)

        log.state('Removing Inactive Accounts...')
        accounts, expected = cls.Dynamics.get_accounts()

        if accounts is None or expected is None:
            log.issue('Unable to process account status filter - Skipping...')
            draft = report
            
        else:
            draft = report.loc[(
                (report['StoreNumber'].isin(accounts)) | 
                (report['StoreNumber'].isin(expected))
            )]

        final = draft[~draft['Month%'].isnull()]

        return final

    @classmethod
    def export(cls, data: DataFrame):
        try:
            data.to_csv(
                f"{exportDir}Period Ending {cls.date}.csv", 
                index=False
            )
        except PermissionError:
            log.error('Failed To Export to CSV - file is currently open')
            
            status: bool = False
            i = 1

            while not status:
                try:
                    log.debug(f'Attempting to Export to CSV at: Exports\\Period Ending {cls.date} ({i}).csv')

                    data.to_csv(
                        f"{exportDir}Period Ending {cls.date} ({i}).csv", 
                        index=False
                    )

                    status = True
                except:
                    log.error(f'Failed to Export CSV at destination: Exports\\Period Ending {cls.date} ({i}).csv')
                    i += 1
        
        return

    @classmethod
    def execute(cls):
        log.state('Fetching Movement Data...')
        data = cls.retrieve()

        log.state('Preparing Initial Report...')
        draft = cls.analyze(data)

        log.state('Finalizing Report...')
        report = cls.filter(draft)

        log.state('Exporting Report File...')
        cls.export(report)
        
        

if __name__ == '__main__':
    ControlFlow.execute()


