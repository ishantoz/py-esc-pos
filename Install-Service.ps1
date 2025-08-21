Param(
    [string]$ServiceName = "POSPrinterService",
    [string]$ExePath = "C:\path\to\dist\app.exe",
    [int]$Port = 5000
)

# Compose the argument list for your EXE
$args = "--port $Port"

# If the service already exists, skip creation
if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Write-Host "Service '$ServiceName' already exists."
} else {
    # Create the new service
    New-Service -Name $ServiceName `
        -BinaryPathName "`"$ExePath`" $args" `
        -DisplayName "POS Printer Service" `
        -Description "Runs the POS print queue service" `
        -StartupType Automatic

    Write-Host "Service '$ServiceName' created successfully."
}

# Start the service immediately
Start-Service -Name $ServiceName
Write-Host "Service '$ServiceName' started."
