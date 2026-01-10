# Activate venv
& ".\.venv\Scripts\Activate.ps1"

# Get local IP address for convenience
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -match "Wi-Fi|Ethernet" }).IPAddress
Write-Host "Jupyter will be available at: http://$($ip[0]):8888"

# Launch Jupyter Lab listening on all IPs
# Note: This is not secure for public internet, only for local network!
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token='' --NotebookApp.password=''
