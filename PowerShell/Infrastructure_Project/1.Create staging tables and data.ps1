
# ------------------------------
# Create Staging Tables
# ------------------------------
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "

CREATE TABLE stg_vmware (
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

CREATE TABLE stg_hyperv (
    VMID               VARCHAR(20),
    VMName             VARCHAR(100),
    Host               VARCHAR(50),
    Datacentre         VARCHAR(50),
    OS                 VARCHAR(100),
    CPUCount           INT,
    RAMAssignedGB      DECIMAL(10,2),
    RAMUsedGB          DECIMAL(10,2),
    CPUUsagePct        DECIMAL(10,2),
    PoweredOn          BIT,
    ReplicationEnabled BIT,
    CheckpointCount    INT,
    DiskAllocatedGB    DECIMAL(10,2),
    DiskUsedGB         DECIMAL(10,2),
    AVProduct          VARCHAR(50),
    LoadDate           DATETIME NOT NULL DEFAULT GETDATE()
);

CREATE TABLE stg_patching (
    VMID               VARCHAR(20),
    VMName             VARCHAR(100),
    OS                 VARCHAR(100),
    LastPatchDate      DATE,
    PatchesInstalled   INT,
    PatchesFailed      INT,
    PatchesPending     INT,
    LastPatchStatus    VARCHAR(50),
    DaysSinceLastPatch INT,
    IsCompliant        BIT,
    LoadDate           DATETIME NOT NULL DEFAULT GETDATE()
);

CREATE TABLE stg_av (
    VMID               VARCHAR(20),
    VMName             VARCHAR(100),
    AVProduct          VARCHAR(50),
    AVVersion          VARCHAR(20),
    DefinitionVersion  VARCHAR(20),
    DefinitionDate     DATE,
    LastScanDate       DATE,
    DaysSinceLastScan  INT,
    ThreatsDetected    INT,
    ThreatsRemoved     INT,
    ScanStatus         VARCHAR(50),
    IsCompliant        BIT,
    LoadDate           DATETIME NOT NULL DEFAULT GETDATE()
);

CREATE TABLE stg_storage (
    LUNID              VARCHAR(20),
    LUNName            VARCHAR(100),
    Datacentre         VARCHAR(50),
    StorageArray       VARCHAR(50),
    StorageTier        VARCHAR(20),
    Protocol           VARCHAR(20),
    AllocatedGB        DECIMAL(10,2),
    UsedGB             DECIMAL(10,2),
    FreeGB             DECIMAL(10,2),
    UsedPct            DECIMAL(10,2),
    DatastoreName      VARCHAR(100),
    RaidType           VARCHAR(20),
    IsOnline           BIT,
    LoadDate           DATETIME NOT NULL DEFAULT GETDATE()
);
"

# ------------------------------
# Import CSVs into Staging Tables
# ------------------------------

# Update this path to where your CSVs are
$csvPath = "C:\Projects\Database_Agent\PowerShell\CSV"

# VMware
Write-Host "Loading stg_vmware..."
Import-Csv "$csvPath\vmware.csv" | ForEach-Object {
    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO stg_vmware (VMID, VMName, Cluster, Datacentre, Host, OS, CPUCount, RAMAssignedGB, RAMUsedGB, CPUUsagePct, PoweredOn, ToolsInstalled, SnapshotCount, DiskAllocatedGB, DiskUsedGB, AVProduct)
    VALUES ('$($_.VMID)', '$($_.VMName)', '$($_.Cluster)', '$($_.Datacentre)', '$($_.Host)', '$($_.OS)', $($_.CPUCount), $($_.RAMAssignedGB), $($_.RAMUsedGB), $($_.CPUUsagePct), $($_.PoweredOn), $($_.ToolsInstalled), $($_.SnapshotCount), $($_.DiskAllocatedGB), $($_.DiskUsedGB), '$($_.AVProduct)')
    "
}
Write-Host "stg_vmware loaded!"

# HyperV
Write-Host "Loading stg_hyperv..."
Import-Csv "$csvPath\hyperv.csv" | ForEach-Object {
    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO stg_hyperv (VMID, VMName, Host, Datacentre, OS, CPUCount, RAMAssignedGB, RAMUsedGB, CPUUsagePct, PoweredOn, ReplicationEnabled, CheckpointCount, DiskAllocatedGB, DiskUsedGB, AVProduct)
    VALUES ('$($_.VMID)', '$($_.VMName)', '$($_.Host)', '$($_.Datacentre)', '$($_.OS)', $($_.CPUCount), $($_.RAMAssignedGB), $($_.RAMUsedGB), $($_.CPUUsagePct), $($_.PoweredOn), $($_.ReplicationEnabled), $($_.CheckpointCount), $($_.DiskAllocatedGB), $($_.DiskUsedGB), '$($_.AVProduct)')
    "
}
Write-Host "stg_hyperv loaded!"

# Patching
Write-Host "Loading stg_patching..."
Import-Csv "$csvPath\patching.csv" | ForEach-Object {
    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO stg_patching (VMID, VMName, OS, LastPatchDate, PatchesInstalled, PatchesFailed, PatchesPending, LastPatchStatus, DaysSinceLastPatch, IsCompliant)
    VALUES ('$($_.VMID)', '$($_.VMName)', '$($_.OS)', '$($_.LastPatchDate)', $($_.PatchesInstalled), $($_.PatchesFailed), $($_.PatchesPending), '$($_.LastPatchStatus)', $($_.DaysSinceLastPatch), $($_.IsCompliant))
    "
}
Write-Host "stg_patching loaded!"

# AV
Write-Host "Loading stg_av..."
Import-Csv "$csvPath\av.csv" | ForEach-Object {
    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO stg_av (VMID, VMName, AVProduct, AVVersion, DefinitionVersion, DefinitionDate, LastScanDate, DaysSinceLastScan, ThreatsDetected, ThreatsRemoved, ScanStatus, IsCompliant)
    VALUES ('$($_.VMID)', '$($_.VMName)', '$($_.AVProduct)', '$($_.AVVersion)', '$($_.DefinitionVersion)', '$($_.DefinitionDate)', '$($_.LastScanDate)', $($_.DaysSinceLastScan), $($_.ThreatsDetected), $($_.ThreatsRemoved), '$($_.ScanStatus)', $($_.IsCompliant))
    "
}
Write-Host "stg_av loaded!"

# Storage
Write-Host "Loading stg_storage..."
Import-Csv "$csvPath\storage.csv" | ForEach-Object {
    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO stg_storage (LUNID, LUNName, Datacentre, StorageArray, StorageTier, Protocol, AllocatedGB, UsedGB, FreeGB, UsedPct, DatastoreName, RaidType, IsOnline)
    VALUES ('$($_.LUNID)', '$($_.LUNName)', '$($_.Datacentre)', '$($_.StorageArray)', '$($_.StorageTier)', '$($_.Protocol)', $($_.AllocatedGB), $($_.UsedGB), $($_.FreeGB), $($_.UsedPct), '$($_.DatastoreName)', '$($_.RaidType)', $($_.IsOnline))
    "
}
Write-Host "stg_storage loaded!"

Write-Host "All staging tables loaded!"