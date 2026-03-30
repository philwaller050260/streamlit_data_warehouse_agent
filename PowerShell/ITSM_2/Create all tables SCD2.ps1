
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "

-- ============================================
-- DIMENSION TABLES (with SCD Type 2 columns)
-- ============================================

-- Priority is LOW cardinality - rarely changes
-- SCD columns added but unlikely to be used much
CREATE TABLE Dim_itsm_Priority (
    PriorityKey        INT IDENTITY(1,1) PRIMARY KEY,
    PriorityCode       VARCHAR(5)        NOT NULL,
    PriorityName       VARCHAR(20)       NOT NULL,
    ResponseTimeMins   INT               NOT NULL,
    ResolutionTimeMins INT               NOT NULL,
    -- SCD Type 2 columns
    StartDate          DATE              NOT NULL DEFAULT GETDATE(),
    EndDate            DATE              NULL,
    IsActive           BIT               NOT NULL DEFAULT 1
);

-- Status is LOW cardinality - rarely changes
CREATE TABLE Dim_itsm_Status (
    StatusKey          INT IDENTITY(1,1) PRIMARY KEY,
    StatusCode         VARCHAR(5)        NOT NULL,
    StatusName         VARCHAR(20)       NOT NULL,
    -- SCD Type 2 columns
    StartDate          DATE              NOT NULL DEFAULT GETDATE(),
    EndDate            DATE              NULL,
    IsActive           BIT               NOT NULL DEFAULT 1
);

-- Category - could change e.g. new subcategories added
CREATE TABLE Dim_itsm_Category (
    CategoryKey        INT IDENTITY(1,1) PRIMARY KEY,
    CategoryCode       VARCHAR(5)        NOT NULL,
    CategoryName       VARCHAR(20)       NOT NULL,
    SubCategory        VARCHAR(50)       NOT NULL,
    -- SCD Type 2 columns
    StartDate          DATE              NOT NULL DEFAULT GETDATE(),
    EndDate            DATE              NULL,
    IsActive           BIT               NOT NULL DEFAULT 1
);

-- Agent - HIGH value for SCD - agents change teams, roles
-- e.g. Sarah moves from Service Desk to Infrastructure
-- Type 2 lets you keep history of which team handled incidents
CREATE TABLE Dim_itsm_Agent (
    AgentKey           INT IDENTITY(1,1) PRIMARY KEY,
    AgentCode          VARCHAR(10)       NOT NULL,
    AgentName          VARCHAR(50)       NOT NULL,
    Team               VARCHAR(50)       NOT NULL,
    Email              VARCHAR(100)      NOT NULL,
    -- SCD Type 2 columns
    StartDate          DATE              NOT NULL DEFAULT GETDATE(),
    EndDate            DATE              NULL,
    IsActive           BIT               NOT NULL DEFAULT 1
);

-- Customer - HIGH value for SCD - customers change dept, location
-- e.g. James moves from London to Manchester
-- Type 2 lets you report incidents by location at time of raise
CREATE TABLE Dim_itsm_Customer (
    CustomerKey        INT IDENTITY(1,1) PRIMARY KEY,
    CustomerCode       VARCHAR(10)       NOT NULL,
    CustomerName       VARCHAR(100)      NOT NULL,
    Department         VARCHAR(50)       NOT NULL,
    Location           VARCHAR(50)       NOT NULL,
    Email              VARCHAR(100)      NOT NULL,
    -- SCD Type 2 columns
    StartDate          DATE              NOT NULL DEFAULT GETDATE(),
    EndDate            DATE              NULL,
    IsActive           BIT               NOT NULL DEFAULT 1
);

-- Date dim - NO SCD columns needed
-- Dates never change - 1st Jan 2024 is always 1st Jan 2024
CREATE TABLE Dim_itsm_Date (
    DateKey            INT               PRIMARY KEY,
    FullDate           DATE              NOT NULL,
    DayName            VARCHAR(10)       NOT NULL,
    DayOfWeek          INT               NOT NULL,
    DayOfMonth         INT               NOT NULL,
    WeekOfYear         INT               NOT NULL,
    MonthNumber        INT               NOT NULL,
    MonthName          VARCHAR(10)       NOT NULL,
    Quarter            INT               NOT NULL,
    Year               INT               NOT NULL,
    IsWeekend          BIT               NOT NULL
);

-- ============================================
-- FACT TABLE
-- No SCD columns - facts are immutable events
-- CreatedDate added for audit tracking
-- FK references now correctly point to Dim_itsm_ tables
-- ============================================
CREATE TABLE Fact_itsm_Incident (
    IncidentKey        INT IDENTITY(1,1) PRIMARY KEY,
    IncidentNumber     VARCHAR(20)       NOT NULL,
    DateKey            INT               NOT NULL FOREIGN KEY REFERENCES Dim_itsm_Date(DateKey),
    CustomerKey        INT               NOT NULL FOREIGN KEY REFERENCES Dim_itsm_Customer(CustomerKey),
    AgentKey           INT               NOT NULL FOREIGN KEY REFERENCES Dim_itsm_Agent(AgentKey),
    CategoryKey        INT               NOT NULL FOREIGN KEY REFERENCES Dim_itsm_Category(CategoryKey),
    PriorityKey        INT               NOT NULL FOREIGN KEY REFERENCES Dim_itsm_Priority(PriorityKey),
    StatusKey          INT               NOT NULL FOREIGN KEY REFERENCES Dim_itsm_Status(StatusKey),
    TimeToResolveMins  INT               NULL,
    SLABreached        BIT               NOT NULL,
    ReopenCount        INT               NOT NULL DEFAULT 0,
    CreatedDate        DATETIME          NOT NULL DEFAULT GETDATE()
);
"