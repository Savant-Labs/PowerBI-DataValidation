fetch_all = '''
    SELECT *
    FROM dbo.tblWholesalerMovement;
'''


fetch_sample = '''
    WITH Movement AS (
        SELECT *,
        ROW_NUMBER() OVER (ORDER BY ReportPeriod) AS 'RowNumber'
        FROM dbo.tblWholesalerMovement
    ) 

    SELECT * 
    FROM Movement 
    WHERE RowNumber < 10000;
'''
