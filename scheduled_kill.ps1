$targetTime = (Get-Date).Date.AddHours(20)
$now = Get-Date
$diff = [math]::Max(1, [math]::Round(($targetTime - $now).TotalSeconds))
Write-Host "Sleeping for $diff seconds until 20:00:00 WIB..."
Start-Sleep -Seconds $diff
Write-Host "Stopping gas.py and Chrome processes..."
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*gas.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-Process -Name "chromedriver" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "All gas.py processes terminated cleanly at 20:00:00 WIB."
