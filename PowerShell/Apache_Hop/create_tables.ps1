Write-Verbose "Get creds" -Verbose
$data = Get-Content C:\Projects\streamlit_data_warehouse_agent\secrets.toml

Write-Verbose "get sql content" -Verbose
$sql_content = Get-Content "C:\Projects\streamlit_data_warehouse_agent\Udemy_Data_Modelling\Data_Modelling.sql"


Write-Verbose "Get csb files" -Verbose
$csv_files = Get-ChildItem C:\Projects\streamlit_data_warehouse_agent\Udemy_Data_Modelling\source_csv

Write-Verbose "Create sql creds" -Verbose
$sql = [pscustomobject]@{

    azure_sql_server = ($data |? {$_ -match 'azure_sql_server'}).split("=").Replace('"','').Trim()[-1]
    azure_sql_database = ($data |? {$_ -match 'azure_sql_database'}).split("=").Replace('"','').Trim()[-1]
    azure_sql_username = ($data |? {$_ -match 'azure_sql_username'}).split("=").Replace('"','').Trim()[-1]
    azure_sql_password = ($data |? {$_ -match 'azure_sql_password'}).split("=").Replace('"','').Trim()[-1]
}
Write-Verbose "Create sql tables" -Verbose
Invoke-Sqlcmd -ServerInstance $sql.azure_sql_server -Database $sql.azure_sql_database -Username $sql.azure_sql_username -Password $sql.azure_sql_password -Query "

$sql_content

"




$password = ConvertTo-SecureString $sql.azure_sql_password -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ($sql.azure_sql_username, $password)
######################################################
##     If this doesnt work write-sqltabeldata    #####
##     close the ISE and start a new one #############
######################################################
$i = 0
do {
$csv_file = $csv_files[$i].FullName
$table = $csv_files[$i].Name.Replace('.csv','')
Write-Verbose "table $table" -Verbose
foreach ($row in Import-Csv $csv_file)
{
    Write-Verbose "adding data $row" -Verbose
    Write-SqlTableData -ServerInstance $sql.azure_sql_server -DatabaseName $sql.azure_sql_database -SchemaName dbo -InputData $row -Credential $cred -TableName $table
}
$i++ 
Start-Sleep 5
}until($i -eq $csv_files.Count)
Test-NetConnection -ComputerName $sql.azure_sql_server -Port 1433
$tables = 
foreach ($table in $csv_files.Name.Replace('.csv',''))
{
    "Drop table $table"
}

Invoke-Sqlcmd -ServerInstance $sql.azure_sql_server -Database $sql.azure_sql_database -Username $sql.azure_sql_username -Password $sql.azure_sql_password -Query "

$tables

"
