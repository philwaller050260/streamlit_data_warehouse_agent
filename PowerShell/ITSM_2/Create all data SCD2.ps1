
# ------------------------------
# Dim_itsm_Priority
# ------------------------------
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_itsm_Priority (PriorityCode, PriorityName, ResponseTimeMins, ResolutionTimeMins, StartDate, EndDate, IsActive) VALUES
('P1', 'Critical', 15,   240,  GETDATE(), NULL, 1),
('P2', 'High',     60,   480,  GETDATE(), NULL, 1),
('P3', 'Medium',   240,  1440, GETDATE(), NULL, 1),
('P4', 'Low',      480,  2880, GETDATE(), NULL, 1)
"

# ------------------------------
# Dim_itsm_Status
# ------------------------------
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_itsm_Status (StatusCode, StatusName, StartDate, EndDate, IsActive) VALUES
('OPN', 'Open',        GETDATE(), NULL, 1),
('INP', 'In Progress', GETDATE(), NULL, 1),
('PND', 'Pending',     GETDATE(), NULL, 1),
('RES', 'Resolved',    GETDATE(), NULL, 0),
('CLS', 'Closed',      GETDATE(), NULL, 0),
('CAN', 'Cancelled',   GETDATE(), NULL, 0)
"

# ------------------------------
# Dim_itsm_Category
# ------------------------------
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_itsm_Category (CategoryCode, CategoryName, SubCategory, StartDate, EndDate, IsActive) VALUES
('HW',  'Hardware',  'Laptop',           GETDATE(), NULL, 1),
('HW',  'Hardware',  'Desktop',          GETDATE(), NULL, 1),
('HW',  'Hardware',  'Printer',          GETDATE(), NULL, 1),
('HW',  'Hardware',  'Mobile Device',    GETDATE(), NULL, 1),
('SW',  'Software',  'Operating System', GETDATE(), NULL, 1),
('SW',  'Software',  'Microsoft 365',    GETDATE(), NULL, 1),
('SW',  'Software',  'ERP System',       GETDATE(), NULL, 1),
('SW',  'Software',  'Antivirus',        GETDATE(), NULL, 1),
('NET', 'Network',   'VPN',              GETDATE(), NULL, 1),
('NET', 'Network',   'WiFi',             GETDATE(), NULL, 1),
('NET', 'Network',   'Firewall',         GETDATE(), NULL, 1),
('NET', 'Network',   'DNS',              GETDATE(), NULL, 1),
('SEC', 'Security',  'Account Lockout',  GETDATE(), NULL, 1),
('SEC', 'Security',  'Phishing',         GETDATE(), NULL, 1),
('SEC', 'Security',  'Data Breach',      GETDATE(), NULL, 1),
('ACC', 'Access',    'New User Setup',   GETDATE(), NULL, 1),
('ACC', 'Access',    'Password Reset',   GETDATE(), NULL, 1),
('ACC', 'Access',    'Permissions',      GETDATE(), NULL, 1)
"

# ------------------------------
# Dim_itsm_Agent
# ------------------------------
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_itsm_Agent (AgentCode, AgentName, Team, Email, StartDate, EndDate, IsActive) VALUES
('AGT001', 'James Wilson',    'Service Desk',   'j.wilson@company.com',    GETDATE(), NULL, 1),
('AGT002', 'Sarah Mitchell',  'Service Desk',   's.mitchell@company.com',  GETDATE(), NULL, 1),
('AGT003', 'David Thompson',  'Service Desk',   'd.thompson@company.com',  GETDATE(), NULL, 1),
('AGT004', 'Emma Clarke',     'Service Desk',   'e.clarke@company.com',    GETDATE(), NULL, 1),
('AGT005', 'Michael Brown',   'Infrastructure', 'm.brown@company.com',     GETDATE(), NULL, 1),
('AGT006', 'Laura Jenkins',   'Infrastructure', 'l.jenkins@company.com',   GETDATE(), NULL, 1),
('AGT007', 'Chris Patterson', 'Infrastructure', 'c.patterson@company.com', GETDATE(), NULL, 1),
('AGT008', 'Rachel Adams',    'Security',       'r.adams@company.com',     GETDATE(), NULL, 1),
('AGT009', 'Tom Harrison',    'Security',       't.harrison@company.com',  GETDATE(), NULL, 1),
('AGT010', 'Sophie Turner',   'Applications',   's.turner@company.com',    GETDATE(), NULL, 1),
('AGT011', 'Daniel Hughes',   'Applications',   'd.hughes@company.com',    GETDATE(), NULL, 1),
('AGT012', 'Natalie Ford',    'Applications',   'n.ford@company.com',      GETDATE(), NULL, 1)
"

# ------------------------------
# Dim_itsm_Customer
# ------------------------------
Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_itsm_Customer (CustomerCode, CustomerName, Department, Location, Email, StartDate, EndDate, IsActive) VALUES
('CST001', 'Oliver Bennett',   'Finance',     'London',     'o.bennett@company.com',  GETDATE(), NULL, 1),
('CST002', 'Isabella Scott',   'Finance',     'London',     'i.scott@company.com',    GETDATE(), NULL, 1),
('CST003', 'Harry Walker',     'HR',          'Manchester', 'h.walker@company.com',   GETDATE(), NULL, 1),
('CST004', 'Amelia Green',     'HR',          'Manchester', 'a.green@company.com',    GETDATE(), NULL, 1),
('CST005', 'George Baker',     'Sales',       'Birmingham', 'g.baker@company.com',    GETDATE(), NULL, 1),
('CST006', 'Lily Carter',      'Sales',       'Birmingham', 'l.carter@company.com',   GETDATE(), NULL, 1),
('CST007', 'Jack Robinson',    'Sales',       'London',     'j.robinson@company.com', GETDATE(), NULL, 1),
('CST008', 'Sophia White',     'Marketing',   'London',     's.white@company.com',    GETDATE(), NULL, 1),
('CST009', 'Ethan Lewis',      'Marketing',   'Leeds',      'e.lewis@company.com',    GETDATE(), NULL, 1),
('CST010', 'Mia Harris',       'Operations',  'Leeds',      'm.harris@company.com',   GETDATE(), NULL, 1),
('CST011', 'Noah Martin',      'Operations',  'Glasgow',    'n.martin@company.com',   GETDATE(), NULL, 1),
('CST012', 'Charlotte Davies', 'Operations',  'Glasgow',    'c.davies@company.com',   GETDATE(), NULL, 1),
('CST013', 'Liam Taylor',      'IT',          'London',     'l.taylor@company.com',   GETDATE(), NULL, 1),
('CST014', 'Emily Johnson',    'IT',          'London',     'e.johnson@company.com',  GETDATE(), NULL, 1),
('CST015', 'Benjamin Moore',   'Legal',       'London',     'b.moore@company.com',    GETDATE(), NULL, 1),
('CST016', 'Grace Anderson',   'Legal',       'Edinburgh',  'g.anderson@company.com', GETDATE(), NULL, 1),
('CST017', 'Samuel Jackson',   'Procurement', 'Birmingham', 's.jackson@company.com',  GETDATE(), NULL, 1),
('CST018', 'Poppy Wright',     'Procurement', 'Manchester', 'p.wright@company.com',   GETDATE(), NULL, 1),
('CST019', 'Alfie Thompson',   'Executive',   'London',     'a.thompson@company.com', GETDATE(), NULL, 1),
('CST020', 'Isla Martinez',    'Executive',   'London',     'i.martinez@company.com', GETDATE(), NULL, 1)
"

# ------------------------------
# Dim_itsm_Date (no SCD columns)
# ------------------------------
$startDate = Get-Date "2023-01-01"
$endDate   = Get-Date "2025-12-31"
$date      = $startDate

while ($date -le $endDate) {
    $dateKey     = $date.ToString("yyyyMMdd")
    $fullDate    = $date.ToString("yyyy-MM-dd")
    $dayName     = $date.ToString("dddd")
    $dayOfWeek   = [int]$date.DayOfWeek
    $dayOfMonth  = $date.Day
    $weekOfYear  = (Get-Culture).Calendar.GetWeekOfYear($date, [System.Globalization.CalendarWeekRule]::FirstDay, [System.DayOfWeek]::Monday)
    $monthNumber = $date.Month
    $monthName   = $date.ToString("MMMM")
    $quarter     = [math]::Ceiling($date.Month / 3)
    $year        = $date.Year
    $isWeekend   = if ($date.DayOfWeek -in @('Saturday','Sunday')) { 1 } else { 0 }

    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO Dim_itsm_Date VALUES ($dateKey, '$fullDate', '$dayName', $dayOfWeek, $dayOfMonth, $weekOfYear, $monthNumber, '$monthName', $quarter, $year, $isWeekend)
    "
    $date = $date.AddDays(1)
}

# ------------------------------
# Fact_itsm_Incident (1000 rows)
# ------------------------------
$incidents      = 1000
$incidentNumber = 1

for ($i = 1; $i -le $incidents; $i++) {
    $incidentNum   = "INC" + $incidentNumber.ToString("000000")
    $dateKey       = (Get-Date "2023-01-01").AddDays((Get-Random -Minimum 0 -Maximum 1095)).ToString("yyyyMMdd")
    $customerKey   = Get-Random -Minimum 1 -Maximum 21
    $agentKey      = Get-Random -Minimum 1 -Maximum 13
    $categoryKey   = Get-Random -Minimum 1 -Maximum 19
    $priorityKey   = Get-Random -Minimum 1 -Maximum 5
    $statusKey     = Get-Random -Minimum 1 -Maximum 7
    $slaBreached   = Get-Random -Minimum 0 -Maximum 2
    $reopenCount   = Get-Random -Minimum 0 -Maximum 4

    if ($statusKey -in @(4,5)) {
        $timeToResolve = Get-Random -Minimum 30 -Maximum 2880
    } else {
        $timeToResolve = "NULL"
    }

    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO Fact_itsm_Incident (IncidentNumber, DateKey, CustomerKey, AgentKey, CategoryKey, PriorityKey, StatusKey, TimeToResolveMins, SLABreached, ReopenCount)
    VALUES ('$incidentNum', $dateKey, $customerKey, $agentKey, $categoryKey, $priorityKey, $statusKey, $timeToResolve, $slaBreached, $reopenCount)
    "
    $incidentNumber++
}