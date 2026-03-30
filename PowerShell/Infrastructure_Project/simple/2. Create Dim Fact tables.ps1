
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "

-- Simple Dim_VM with SCD Type 2
CREATE TABLE simple_Dim_VM (
    VMKey         INT IDENTITY(1,1) PRIMARY KEY,  -- surrogate key
    VMID          VARCHAR(20)       NOT NULL,      -- natural key
    VMName        VARCHAR(100)      NOT NULL,
    Datacentre    VARCHAR(50)       NOT NULL,
    Host          VARCHAR(50)       NOT NULL,
    OS            VARCHAR(100)      NOT NULL,
    CPUCount      INT               NOT NULL,
    RAMAssignedGB DECIMAL(10,2)     NOT NULL,
    PoweredOn     BIT               NOT NULL,
    -- SCD Type 2 columns
    StartDate     DATE              NOT NULL DEFAULT GETDATE(),
    EndDate       DATE              NULL,
    IsActive      BIT               NOT NULL DEFAULT 1
);

-- Simple Fact_VM - daily measurements
CREATE TABLE simple_Fact_VM (
    FactKey         INT IDENTITY(1,1) PRIMARY KEY,
    VMKey           INT               NOT NULL FOREIGN KEY REFERENCES simple_Dim_VM(VMKey),
    SnapshotDate    DATE              NOT NULL DEFAULT GETDATE(),
    CPUUsagePct     DECIMAL(10,2)     NOT NULL,
    RAMUsedGB       DECIMAL(10,2)     NOT NULL,
    DiskAllocatedGB DECIMAL(10,2)     NOT NULL,
    DiskUsedGB      DECIMAL(10,2)     NOT NULL,
    SnapshotCount   INT               NOT NULL DEFAULT 0,
    PoweredOn       BIT               NOT NULL,
    CreatedDate     DATETIME          NOT NULL DEFAULT GETDATE()
);
"