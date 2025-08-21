# Get current directory
$cwd = Get-Location

# Path to python.exe inside .venv
$python = Join-Path $cwd ".venv\Scripts\python.exe"
$script = Join-Path $cwd "main.py"

# Check if python executable exists
if (-Not (Test-Path $python)) {
    Write-Error "Python executable not found at $python"
    exit 1
}

# Check if main.py exists
if (-Not (Test-Path $script)) {
    Write-Error "Script not found at $script"
    exit 1
}

# Run python script
& $python $script
exit $LASTEXITCODE
