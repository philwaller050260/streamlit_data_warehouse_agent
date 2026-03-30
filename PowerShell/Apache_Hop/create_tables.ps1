
$data = Get-Content C:\Projects\Database_Agent\Udemy_Data_Modelling\Data_Modelling.sql -Raw

$data.Replace('GO','') | Set-Content C:\Projects\Database_Agent\Udemy_Data_Modelling\Data_Modelling.sql


Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "


$data

"