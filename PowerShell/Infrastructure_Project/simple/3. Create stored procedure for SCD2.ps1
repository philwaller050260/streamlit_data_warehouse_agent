
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
ALTER PROCEDURE sp_simple_transform_VM
AS
BEGIN
    SET NOCOUNT ON;

    -- ============================================
    -- STEP 1: MERGE - Handle New and Changed VMs
    -- New VMs    -> INSERT
    -- Changed VMs -> Retire old row (UPDATE IsActive=0)
    -- ============================================
    MERGE simple_Dim_VM AS target
    USING simple_stg_vmware AS source
    ON target.VMID = source.VMID AND target.IsActive = 1

    -- New VM - insert fresh row
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (
            VMID, VMName, Datacentre, Host, OS,
            CPUCount, RAMAssignedGB, PoweredOn,
            StartDate, EndDate, IsActive
        )
        VALUES (
            source.VMID, source.VMName, source.Datacentre, source.Host, source.OS,
            source.CPUCount, source.RAMAssignedGB, source.PoweredOn,
            GETDATE(), NULL, 1
        )

    -- Existing VM with changes - retire old row
    WHEN MATCHED AND (
        source.RAMAssignedGB <> target.RAMAssignedGB OR
        source.CPUCount      <> target.CPUCount      OR
        source.Host          <> target.Host          OR
        source.PoweredOn     <> target.PoweredOn
    ) THEN
        UPDATE SET
            target.IsActive = 0,
            target.EndDate  = GETDATE();

    -- ============================================
    -- STEP 2: INSERT new row for changed VMs
    -- MERGE cant do this in one pass for SCD Type 2
    -- So we insert where IsActive=1 doesnt exist
    -- ============================================
    INSERT INTO simple_Dim_VM (
        VMID, VMName, Datacentre, Host, OS,
        CPUCount, RAMAssignedGB, PoweredOn,
        StartDate, EndDate, IsActive
    )
    SELECT
        s.VMID, s.VMName, s.Datacentre, s.Host, s.OS,
        s.CPUCount, s.RAMAssignedGB, s.PoweredOn,
        GETDATE(), NULL, 1
    FROM simple_stg_vmware s
    WHERE NOT EXISTS (
        SELECT 1 FROM simple_Dim_VM d
        WHERE d.VMID     = s.VMID
        AND   d.IsActive = 1
    );

    -- ============================================
    -- STEP 3: Load Facts
    -- Always insert new rows regardless of changes
    -- ============================================
    INSERT INTO simple_Fact_VM (
        VMKey, SnapshotDate, CPUUsagePct, RAMUsedGB,
        DiskAllocatedGB, DiskUsedGB, SnapshotCount, PoweredOn
    )
    SELECT
        d.VMKey,
        GETDATE(),
        s.CPUUsagePct,
        s.RAMUsedGB,
        s.DiskAllocatedGB,
        s.DiskUsedGB,
        s.SnapshotCount,
        s.PoweredOn
    FROM simple_stg_vmware s
    JOIN simple_Dim_VM d ON d.VMID = s.VMID AND d.IsActive = 1;

    PRINT 'sp_simple_transform_VM completed successfully';
END
"