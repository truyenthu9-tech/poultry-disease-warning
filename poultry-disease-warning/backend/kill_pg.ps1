Get-Process postgres -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Killing $($_.Id)"
    Stop-Process -Id $_.Id -Force
}
Start-Sleep -Seconds 3
Write-Host "Done"
Get-Service postgresql-x64-18 | Select-Object Name, Status