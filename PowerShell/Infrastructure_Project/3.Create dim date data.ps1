
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
    INSERT INTO Dim_infra_Date VALUES ($dateKey, '$fullDate', '$dayName', $dayOfWeek, $dayOfMonth, $weekOfYear, $monthNumber, '$monthName', $quarter, $year, $isWeekend)
    "
    $date = $date.AddDays(1)
}

Write-Host "Dim_infra_Date populated!"