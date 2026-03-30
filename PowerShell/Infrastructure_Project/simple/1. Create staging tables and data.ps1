
# ------------------------------
# Create Staging Tables
# ------------------------------
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "

CREATE TABLE simple_stg_vmware (
    VMID               VARCHAR(20),
    VMName             VARCHAR(100),
    Cluster            VARCHAR(50),
    Datacentre         VARCHAR(50),
    Host               VARCHAR(50),
    OS                 VARCHAR(100),
    CPUCount           INT,
    RAMAssignedGB      DECIMAL(10,2),
    RAMUsedGB          DECIMAL(10,2),
    CPUUsagePct        DECIMAL(10,2),
    PoweredOn          BIT,
    ToolsInstalled     BIT,
    SnapshotCount      INT,
    DiskAllocatedGB    DECIMAL(10,2),
    DiskUsedGB         DECIMAL(10,2),
    AVProduct          VARCHAR(50),
    LoadDate           DATETIME NOT NULL DEFAULT GETDATE()
);


"

# ------------------------------
# Import CSVs into Staging Tables
# ------------------------------

# Update this path to where your CSVs are
$csvPath = "C:\Projects\Database_Agent\PowerShell\CSV\"

# VMware
Write-Host "Loading stg_vmware..."
Import-Csv "$csvPath\vmware.csv" | ForEach-Object {
    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO simple_stg_vmware (VMID, VMName, Cluster, Datacentre, Host, OS, CPUCount, RAMAssignedGB, RAMUsedGB, CPUUsagePct, PoweredOn, ToolsInstalled, SnapshotCount, DiskAllocatedGB, DiskUsedGB, AVProduct)
    VALUES ('$($_.VMID)', '$($_.VMName)', '$($_.Cluster)', '$($_.Datacentre)', '$($_.Host)', '$($_.OS)', $($_.CPUCount), $($_.RAMAssignedGB), $($_.RAMUsedGB), $($_.CPUUsagePct), $($_.PoweredOn), $($_.ToolsInstalled), $($_.SnapshotCount), $($_.DiskAllocatedGB), $($_.DiskUsedGB), '$($_.AVProduct)')
    "
}
Write-Host "stg_vmware loaded!"

Write-Host "All staging tables loaded!"