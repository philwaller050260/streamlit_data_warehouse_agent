Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
DROP TABLE IF EXISTS Fact_Incident
DROP TABLE IF EXISTS Dim_Date
DROP TABLE IF EXISTS Dim_Customer
DROP TABLE IF EXISTS Dim_Agent
DROP TABLE IF EXISTS Dim_Category
DROP TABLE IF EXISTS Dim_Status
DROP TABLE IF EXISTS Dim_Priority
"


Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
DROP TABLE IF EXISTS Fact_Order
DROP TABLE IF EXISTS Fact_Incident
DROP TABLE IF EXISTS Dim_Date
DROP TABLE IF EXISTS Dim_Customer
DROP TABLE IF EXISTS Dim_Product
DROP TABLE IF EXISTS Dim_ShippingMethod
DROP TABLE IF EXISTS Dim_OrderStatus
DROP TABLE IF EXISTS Dim_PaymentMethod
DROP TABLE IF EXISTS Dim_Salesperson
DROP TABLE IF EXISTS Dim_Warehouse
DROP TABLE IF EXISTS Dim_Agent
DROP TABLE IF EXISTS Dim_Category
DROP TABLE IF EXISTS Dim_Status
DROP TABLE IF EXISTS Dim_Priority
DROP TABLE IF EXISTS configuration
DROP TABLE IF EXISTS incident_management
DROP TABLE IF EXISTS change_management
DROP TABLE IF EXISTS problem_management
DROP TABLE IF EXISTS RAG_evaluation_runs
DROP TABLE IF EXISTS RAG_query_results
DROP TABLE IF EXISTS RAG_run_metrics
"


Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
DECLARE @sql NVARCHAR(MAX) = ''

-- Drop all FK constraints first
SELECT @sql += 'ALTER TABLE ' + QUOTENAME(TABLE_SCHEMA) + '.' + QUOTENAME(TABLE_NAME) + 
               ' DROP CONSTRAINT ' + QUOTENAME(CONSTRAINT_NAME) + ';'
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
WHERE CONSTRAINT_TYPE = 'FOREIGN KEY'

EXEC(@sql)

-- Now drop all tables
SET @sql = ''
SELECT @sql += 'DROP TABLE ' + QUOTENAME(TABLE_SCHEMA) + '.' + QUOTENAME(TABLE_NAME) + ';'
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'

EXEC(@sql)
"