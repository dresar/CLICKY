# PowerShell Script to register Scheduled Tasks in Windows Task Scheduler

$ScriptDir = "c:\Users\NCN0C\Downloads\CLICKY"
$BatPath   = "$ScriptDir\run_gas_scheduled.bat"

# 1. TASK UTAMA: Mulai pukul 19:00, batas waktu 1 jam (stop otomatis 20:00)
$actionStart   = New-ScheduledTaskAction -Execute $BatPath -WorkingDirectory $ScriptDir
$triggerStart  = New-ScheduledTaskTrigger -Daily -At 19:00
$settingsStart = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "CLICKY_Traffic_Start" -Action $actionStart -Trigger $triggerStart -Settings $settingsStart -Description "Jalan otomatis tiap jam 19.00 - 20.00 WIB untuk gas traffic." -Force

# 2. TASK KILL PAKSA (TAKEDOWN): Pukul 20:00 membunuh sisa proses Chrome/Python jika ada
$killCmd    = '/c taskkill /F /IM chromedriver.exe /FI "STATUS eq RUNNING" 2>nul & taskkill /F /FI "WINDOWTITLE eq CLICKY_Traffic_Simulator*" 2>nul'
$actionKill = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $killCmd
$triggerKill= New-ScheduledTaskTrigger -Daily -At 20:00

Register-ScheduledTask -TaskName "CLICKY_Traffic_Kill" -Action $actionKill -Trigger $triggerKill -Description "Membunuh paksa proses traffic jam 20.00 tepat." -Force

Write-Host "✅ BERHASIL: Kedua Scheduled Task telah terdaftar di Windows Task Scheduler!"
