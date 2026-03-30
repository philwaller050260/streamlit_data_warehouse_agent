Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_Priority (PriorityCode, PriorityName, ResponseTimeMins, ResolutionTimeMins) VALUES
('P1', 'Critical', 15,  240),
('P2', 'High',     60,  480),
('P3', 'Medium',   240, 1440),
('P4', 'Low',      480, 2880)
"


#Install-Module sqlserver 

Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "

select *  from Dim_Priority

"

Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_Status (StatusCode, StatusName, IsActive) VALUES
('OPN',  'Open',        1),
('INP',  'In Progress', 1),
('PND',  'Pending',     1),
('RES',  'Resolved',    0),
('CLS',  'Closed',      0),
('CAN',  'Cancelled',   0)
"

Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_Category (CategoryCode, CategoryName, SubCategory) VALUES
('HW',  'Hardware',  'Laptop'),
('HW',  'Hardware',  'Desktop'),
('HW',  'Hardware',  'Printer'),
('HW',  'Hardware',  'Mobile Device'),
('SW',  'Software',  'Operating System'),
('SW',  'Software',  'Microsoft 365'),
('SW',  'Software',  'ERP System'),
('SW',  'Software',  'Antivirus'),
('NET', 'Network',   'VPN'),
('NET', 'Network',   'WiFi'),
('NET', 'Network',   'Firewall'),
('NET', 'Network',   'DNS'),
('SEC', 'Security',  'Account Lockout'),
('SEC', 'Security',  'Phishing'),
('SEC', 'Security',  'Data Breach'),
('ACC', 'Access',    'New User Setup'),
('ACC', 'Access',    'Password Reset'),
('ACC', 'Access',    'Permissions')
"

Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_Agent (AgentCode, AgentName, Team, Email) VALUES
('AGT001', 'James Wilson',    'Service Desk',       'j.wilson@company.com'),
('AGT002', 'Sarah Mitchell',  'Service Desk',       's.mitchell@company.com'),
('AGT003', 'David Thompson',  'Service Desk',       'd.thompson@company.com'),
('AGT004', 'Emma Clarke',     'Service Desk',       'e.clarke@company.com'),
('AGT005', 'Michael Brown',   'Infrastructure',     'm.brown@company.com'),
('AGT006', 'Laura Jenkins',   'Infrastructure',     'l.jenkins@company.com'),
('AGT007', 'Chris Patterson', 'Infrastructure',     'c.patterson@company.com'),
('AGT008', 'Rachel Adams',    'Security',           'r.adams@company.com'),
('AGT009', 'Tom Harrison',    'Security',           't.harrison@company.com'),
('AGT010', 'Sophie Turner',   'Applications',       's.turner@company.com'),
('AGT011', 'Daniel Hughes',   'Applications',       'd.hughes@company.com'),
('AGT012', 'Natalie Ford',    'Applications',       'n.ford@company.com')
"

Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
INSERT INTO Dim_Customer (CustomerCode, CustomerName, Department, Location, Email) VALUES
('CST001', 'Oliver Bennett',   'Finance',        'London',     'o.bennett@company.com'),
('CST002', 'Isabella Scott',   'Finance',        'London',     'i.scott@company.com'),
('CST003', 'Harry Walker',     'HR',             'Manchester', 'h.walker@company.com'),
('CST004', 'Amelia Green',     'HR',             'Manchester', 'a.green@company.com'),
('CST005', 'George Baker',     'Sales',          'Birmingham', 'g.baker@company.com'),
('CST006', 'Lily Carter',      'Sales',          'Birmingham', 'l.carter@company.com'),
('CST007', 'Jack Robinson',    'Sales',          'London',     'j.robinson@company.com'),
('CST008', 'Sophia White',     'Marketing',      'London',     's.white@company.com'),
('CST009', 'Ethan Lewis',      'Marketing',      'Leeds',      'e.lewis@company.com'),
('CST010', 'Mia Harris',       'Operations',     'Leeds',      'm.harris@company.com'),
('CST011', 'Noah Martin',      'Operations',     'Glasgow',    'n.martin@company.com'),
('CST012', 'Charlotte Davies', 'Operations',     'Glasgow',    'c.davies@company.com'),
('CST013', 'Liam Taylor',      'IT',             'London',     'l.taylor@company.com'),
('CST014', 'Emily Johnson',    'IT',             'London',     'e.johnson@company.com'),
('CST015', 'Benjamin Moore',   'Legal',          'London',     'b.moore@company.com'),
('CST016', 'Grace Anderson',   'Legal',          'Edinburgh',  'g.anderson@company.com'),
('CST017', 'Samuel Jackson',   'Procurement',    'Birmingham', 's.jackson@company.com'),
('CST018', 'Poppy Wright',     'Procurement',    'Manchester', 'p.wright@company.com'),
('CST019', 'Alfie Thompson',   'Executive',      'London',     'a.thompson@company.com'),
('CST020', 'Isla Martinez',    'Executive',      'London',     'i.martinez@company.com')
"

$startDate = Get-Date "2023-01-01"
$endDate = Get-Date "2025-12-31"
$date = $startDate

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
    INSERT INTO Dim_Date VALUES ($dateKey, '$fullDate', '$dayName', $dayOfWeek, $dayOfMonth, $weekOfYear, $monthNumber, '$monthName', $quarter, $year, $isWeekend)
    "
    $date = $date.AddDays(1)
}

$incidents = 1000
$incidentNumber = 1

for ($i = 1; $i -le $incidents; $i++) {
    $incidentNum    = "INC" + $incidentNumber.ToString("000000")
    $dateKey        = (Get-Date "2023-01-01").AddDays((Get-Random -Minimum 0 -Maximum 1095)).ToString("yyyyMMdd")
    $customerKey    = Get-Random -Minimum 1 -Maximum 21
    $agentKey       = Get-Random -Minimum 1 -Maximum 13
    $categoryKey    = Get-Random -Minimum 1 -Maximum 19
    $priorityKey    = Get-Random -Minimum 1 -Maximum 5
    $statusKey      = Get-Random -Minimum 1 -Maximum 7
    $slaBreached    = Get-Random -Minimum 0 -Maximum 2
    $reopenCount    = Get-Random -Minimum 0 -Maximum 4
    
    # Resolved/Closed incidents have a resolution time, others NULL
    if ($statusKey -in @(4,5)) {
        $timeToResolve = Get-Random -Minimum 30 -Maximum 2880
    } else {
        $timeToResolve = "NULL"
    }

    Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "
    INSERT INTO Fact_Incident (IncidentNumber, DateKey, CustomerKey, AgentKey, CategoryKey, PriorityKey, StatusKey, TimeToResolveMins, SLABreached, ReopenCount)
    VALUES ('$incidentNum', $dateKey, $customerKey, $agentKey, $categoryKey, $priorityKey, $statusKey, $timeToResolve, $slaBreached, $reopenCount)
    "
    $incidentNumber++
}