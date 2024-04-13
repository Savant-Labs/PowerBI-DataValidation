# **Power BI Data Validation Tool**


### **Intended Goals**
This project examines newly reported data and attempts to identify any potential discrepancy before the data is fully published.  By implementing this process before field teams are able to access the data in Power BI, this tool is able to help improve the perceieved integrity of our reporting systems.

### **Where's the Data?**
This project collects and analyzes data from two individual sources:
- SQL Server (sales reports to be reviewed)
- Microsoft Dynamics Web API (customer information)

It will first separate the sales reports into 3 groups:
1. Current Report Period (to evaluate)
2. Reports from 90 days prior to Current Report Period
3. All other reports

This way, our current data can be compared against historical trends (in our case, 60 months) as well as a more recent trendline containing only the past 3 months. In order to ensure that this comparison is as fair as possible, we generate aggregate datasets by grouping each of these by `Customer`, `Item` and `Report Period` and then outputting the sum of Units Sold per group.


| StoreNumber | Item | Report Period | Qty |
| ----------- | ---- | ------------- | --- |
|    012345   | CHKN | Mar. 31, 2024 |  4  |
|    012345   | CHKN | Mar. 31, 2024 |  2  |
|    012345   | CHKN | Mar. 31, 2024 |  1  |
|    012345   | OILS | Jan. 31, 2024 |  4  |
|    067890   | CHKN | Jan. 31, 2024 |  4  |
becomes
| StoreNumber | Item | Report Period | Qty |
|-------------|------|---------------|-----|
|    012345   | CHKN | Mar. 31, 2024 |  7  |
|    012345   | OILS | Jan. 31, 2024 |  4  |
|    067890   | CHKN | Jan. 31, 2024 |  4  |

We then further summarize these tables by taking an average of 'Qty' (which remember is a sum by `StoreNumber`, `Item` and `ReportPeriod`) across, effectively giving us 3 values for each `StoreNumber` and `Item` tuple:
- Average Qty Per Report Period (All-time)
- Average Qty Per Report Period (Prev. 90 days)
- Average Qty Per Report Period (Current Period)

| StoreNumber | Item | All Time Avg. | Prev. 90 Day Avg. | Current |
|-------------|------|---------------|-------------------|---------|
|    012345   | CHKN |       7       |         6         |    5    |
|    012345   | OILS |       4       |         4         |   NaN   |
|    067890   | CHKN |       9       |         8         |    4    |



### **The Analysis**
Once we have our trends lined out, we can start to look for abnormalities.  We do this by adding 4 extra columns to our data frame showcasing the variance between our averages:
- TrendVar  :   Delta between `Current` and `All Time Avg.`
- TrendVar% :   `Current` represented as a % of `All Time Avg.`
- MonthVar  :   Delta between `Current` and `Prev. 90 Day Avg.`
- MonthVar% :   `Current` represented as a % of `Prev. 90 Day Avg.`

This allows us to easily identify where the store/item is:
- Experiencing slow decline      
    - [`Trend` > `Month` & `Month` > `Current`]
- Experiencing fast decline      
    - [`Trend` = `Month` & `Month` > `Current`]
- Experiencing slow growth      
    - [`Trend` < `Month` & `Month` < `Current`]
- Experiencing fast growth      
    - [`Trend` = `Month` & `Month` < `Current`]
- Missing Data / Incomplete     
    - [`Trend` = `Month` & `Current` = `0`or`NaN`]
- Missing Prolonged Data      
    - [`Trend` > `0` & `Month` = `0` or `NaN` & `Current` = `0` or `NaN`]

We then filter our summarized data set to isolate these instances by locating only rows where one of the above conditions is true.

### **Cleaning The Data**
At this point in our process, we've managed to decrease our table size from over **2,000,000** rows to just a couple thousand - but there is **still** more room to safely remove data.  Due to the nature of our database, we keep records for inactive customers permanently after they have terminated their account.  This means that our list of stores likely contains flags on customers that are no longer active.

To remove these potentially inactive accounts from our report, we pull in account data from our CRM platform (we use Dynamics 365 Sales Enterprise).  This data can only be accessed by OAuth2.0 signed requests, authorized by a user each time the request is ran.  To avoid having to have someone sign into Dynamics for each query, we simply automate the sign in process by using the `UsernameCRM` and `PasswordCRM` environment variables.  This allows the program to sign into Dynamics using our account information and authorize itself to complete the request completely autonomously.

Once it has the authorization, it can begin pulling the data down from the Common Data Service (Dataverse).  After the request is complete, we quickly scan the resulting JSON data to isolate `StoreNumbers` with a status that does not indicate a prolonged period of inactivity.  We can now utilize this list to further narrow down our discrepancy reports and hopefully end up with somewhere close to 600-700 unique [`StoreNumber`, `Item`] keys.

