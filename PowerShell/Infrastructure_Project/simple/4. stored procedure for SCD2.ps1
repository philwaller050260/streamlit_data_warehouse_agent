# invoke sp

Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
EXEC sp_simple_transform_VM
"


# check tables

Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
SELECT VMKey, VMID, VMName, RAMAssignedGB, CPUCount, IsActive, StartDate, EndDate
FROM simple_Dim_VM 
ORDER BY VMID, VMKey
"

#check count of fact table which should increment when SP invoked even if no change!

Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "

select count(*) from simple_Fact_VM 
"



# make a change in vmware.csv to RAM/CPU

# Step 1 - Truncate staging
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
TRUNCATE TABLE simple_stg_vmware
"

# Step 2 - Reload CSV with updated RAM
$csvPath = "C:\Projects\Database_Agent\PowerShell\CSV"
Import-Csv "$csvPath\vmware.csv" | ForEach-Object {
    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO simple_stg_vmware (VMID, VMName, Cluster, Datacentre, Host, OS, CPUCount, RAMAssignedGB, RAMUsedGB, CPUUsagePct, PoweredOn, ToolsInstalled, SnapshotCount, DiskAllocatedGB, DiskUsedGB, AVProduct)
    VALUES ('$($_.VMID)', '$($_.VMName)', '$($_.Cluster)', '$($_.Datacentre)', '$($_.Host)', '$($_.OS)', $($_.CPUCount), $($_.RAMAssignedGB), $($_.RAMUsedGB), $($_.CPUUsagePct), $($_.PoweredOn), $($_.ToolsInstalled), $($_.SnapshotCount), $($_.DiskAllocatedGB), $($_.DiskUsedGB), '$($_.AVProduct)')
    "
}

# Step 3 - Run SP
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
EXEC sp_simple_transform_VM
"

# check the change in the dim table 
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
SELECT VMKey, VMID, VMName, RAMAssignedGB, CPUCount, IsActive, StartDate, EndDate
FROM simple_Dim_VM where VMID = 'VM003'
ORDER BY VMID, VMKey
"

# Check staging has the updated RAM value
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
SELECT VMID, VMName, RAMAssignedGB 
FROM simple_stg_vmware 
WHERE VMID = 'VM003'
"