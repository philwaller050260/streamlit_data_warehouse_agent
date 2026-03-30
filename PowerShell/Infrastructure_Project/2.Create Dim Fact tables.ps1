
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "

-- ============================================
-- LOW CARDINALITY DIMS (simple, rarely change)
-- ============================================

CREATE TABLE Dim_infra_Date (
    DateKey     INT          PRIMARY KEY,
    FullDate    DATE         NOT NULL,
    DayName     VARCHAR(10)  NOT NULL,
    DayOfWeek   INT          NOT NULL,
    DayOfMonth  INT          NOT NULL,
    WeekOfYear  INT          NOT NULL,
    MonthNumber INT          NOT NULL,
    MonthName   VARCHAR(10)  NOT NULL,
    Quarter     INT          NOT NULL,
    Year        INT          NOT NULL,
    IsWeekend   BIT          NOT NULL
);


-- Datacentre dimension
CREATE TABLE Dim_Datacentre (
    DatacentreKey  INT IDENTITY(1,1) PRIMARY KEY,
    DatacentreID   VARCHAR(20)       NOT NULL,
    DatacentreName VARCHAR(50)       NOT NULL,
    Location       VARCHAR(50)       NOT NULL,
    StartDate      DATE              NOT NULL DEFAULT GETDATE(),
    EndDate        DATE              NULL,
    IsActive       BIT               NOT NULL DEFAULT 1
);

-- OS dimension
CREATE TABLE Dim_OS (
    OSKey          INT IDENTITY(1,1) PRIMARY KEY,
    OSID           VARCHAR(20)       NOT NULL,
    OSName         VARCHAR(100)      NOT NULL,
    OSFamily       VARCHAR(50)       NOT NULL,
    OSVersion      VARCHAR(50)       NOT NULL,
    StartDate      DATE              NOT NULL DEFAULT GETDATE(),
    EndDate        DATE              NULL,
    IsActive       BIT               NOT NULL DEFAULT 1
);

-- AV Product dimension
CREATE TABLE Dim_AVProduct (
    AVProductKey   INT IDENTITY(1,1) PRIMARY KEY,
    AVProductID    VARCHAR(20)       NOT NULL,
    AVProductName  VARCHAR(50)       NOT NULL,
    StartDate      DATE              NOT NULL DEFAULT GETDATE(),
    EndDate        DATE              NULL,
    IsActive       BIT               NOT NULL DEFAULT 1
);

-- Storage Tier dimension
CREATE TABLE Dim_StorageTier (
    StorageTierKey  INT IDENTITY(1,1) PRIMARY KEY,
    StorageTierID   VARCHAR(20)       NOT NULL,
    StorageTierName VARCHAR(20)       NOT NULL,
    StartDate       DATE              NOT NULL DEFAULT GETDATE(),
    EndDate         DATE              NULL,
    IsActive        BIT               NOT NULL DEFAULT 1
);

-- Platform dimension (VMware vs HyperV)
CREATE TABLE Dim_Platform (
    PlatformKey    INT IDENTITY(1,1) PRIMARY KEY,
    PlatformID     VARCHAR(20)       NOT NULL,
    PlatformName   VARCHAR(50)       NOT NULL,
    StartDate      DATE              NOT NULL DEFAULT GETDATE(),
    EndDate        DATE              NULL,
    IsActive       BIT               NOT NULL DEFAULT 1
);

-- ============================================
-- DIM_VM - CORE ENTITY - FULL SCD TYPE 2
-- This is where history is tracked
-- VMID is the natural key from source
-- VMKey is the surrogate - increments on change
-- ============================================
CREATE TABLE Dim_VM (
    VMKey            INT IDENTITY(1,1) PRIMARY KEY,  -- surrogate, never changes
    VMID             VARCHAR(20)       NOT NULL,      -- natural key from source
    VMName           VARCHAR(100)      NOT NULL,
    Cluster          VARCHAR(50)       NULL,          -- VMware only
    Host             VARCHAR(50)       NOT NULL,
    DatacentreKey    INT               NOT NULL FOREIGN KEY REFERENCES Dim_Datacentre(DatacentreKey),
    OSKey            INT               NOT NULL FOREIGN KEY REFERENCES Dim_OS(OSKey),
    PlatformKey      INT               NOT NULL FOREIGN KEY REFERENCES Dim_Platform(PlatformKey),
    AVProductKey     INT               NOT NULL FOREIGN KEY REFERENCES Dim_AVProduct(AVProductKey),
    CPUCount         INT               NOT NULL,
    RAMAssignedGB    DECIMAL(10,2)     NOT NULL,
    PoweredOn        BIT               NOT NULL,
    -- SCD Type 2 columns
    StartDate        DATE              NOT NULL DEFAULT GETDATE(),
    EndDate          DATE              NULL,          -- NULL = current record
    IsActive         BIT               NOT NULL DEFAULT 1
);

-- ============================================
-- FACT TABLES - measurements, immutable
-- ============================================

-- VM Performance fact - daily snapshot from VMware/HyperV
CREATE TABLE Fact_VM_Performance (
    PerformanceKey    INT IDENTITY(1,1) PRIMARY KEY,
    VMKey             INT               NOT NULL FOREIGN KEY REFERENCES Dim_VM(VMKey),
    DateKey           INT               NOT NULL FOREIGN KEY REFERENCES Dim_infra_Date(DateKey),
    CPUUsagePct       DECIMAL(10,2)     NOT NULL,
    RAMUsedGB         DECIMAL(10,2)     NOT NULL,
    DiskAllocatedGB   DECIMAL(10,2)     NOT NULL,
    DiskUsedGB        DECIMAL(10,2)     NOT NULL,
    SnapshotCount     INT               NOT NULL DEFAULT 0,
    CheckpointCount   INT               NOT NULL DEFAULT 0,
    ReplicationEnabled BIT              NOT NULL DEFAULT 0,
    CreatedDate       DATETIME          NOT NULL DEFAULT GETDATE()
);

-- Patching fact - compliance snapshot
CREATE TABLE Fact_Patching (
    PatchingKey        INT IDENTITY(1,1) PRIMARY KEY,
    VMKey              INT               NOT NULL FOREIGN KEY REFERENCES Dim_VM(VMKey),
    DateKey            INT               NOT NULL FOREIGN KEY REFERENCES Dim_infra_Date(DateKey),
    PatchesInstalled   INT               NOT NULL DEFAULT 0,
    PatchesFailed      INT               NOT NULL DEFAULT 0,
    PatchesPending     INT               NOT NULL DEFAULT 0,
    DaysSinceLastPatch INT               NOT NULL DEFAULT 0,
    IsCompliant        BIT               NOT NULL DEFAULT 0,
    CreatedDate        DATETIME          NOT NULL DEFAULT GETDATE()
);

-- AV fact - scan and threat snapshot
CREATE TABLE Fact_AV (
    AVKey              INT IDENTITY(1,1) PRIMARY KEY,
    VMKey              INT               NOT NULL FOREIGN KEY REFERENCES Dim_VM(VMKey),
    DateKey            INT               NOT NULL FOREIGN KEY REFERENCES Dim_infra_Date(DateKey),
    AVProductKey       INT               NOT NULL FOREIGN KEY REFERENCES Dim_AVProduct(AVProductKey),
    DaysSinceLastScan  INT               NOT NULL DEFAULT 0,
    ThreatsDetected    INT               NOT NULL DEFAULT 0,
    ThreatsRemoved     INT               NOT NULL DEFAULT 0,
    IsCompliant        BIT               NOT NULL DEFAULT 0,
    CreatedDate        DATETIME          NOT NULL DEFAULT GETDATE()
);

-- Storage fact - LUN capacity snapshot
CREATE TABLE Fact_Storage (
    StorageKey         INT IDENTITY(1,1) PRIMARY KEY,
    LUNID              VARCHAR(20)       NOT NULL,
    DateKey            INT               NOT NULL FOREIGN KEY REFERENCES Dim_infra_Date(DateKey),
    DatacentreKey      INT               NOT NULL FOREIGN KEY REFERENCES Dim_Datacentre(DatacentreKey),
    StorageTierKey     INT               NOT NULL FOREIGN KEY REFERENCES Dim_StorageTier(StorageTierKey),
    AllocatedGB        DECIMAL(10,2)     NOT NULL,
    UsedGB             DECIMAL(10,2)     NOT NULL,
    FreeGB             DECIMAL(10,2)     NOT NULL,
    UsedPct            DECIMAL(10,2)     NOT NULL,
    IsOnline           BIT               NOT NULL DEFAULT 1,
    CreatedDate        DATETIME          NOT NULL DEFAULT GETDATE()
);
"