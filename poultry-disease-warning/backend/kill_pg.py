Get-Process postgres -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Killing $($_.Id) $($_.ProcessName)"
    Stop-Process -Id $_.Id -Force
}
Start-Sleep -Seconds 3
Write-Host "Done killing"
Get-Service postgresql-x64-18 | Select-Object Name, Status