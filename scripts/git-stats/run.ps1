$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
$MainScript = Join-Path $ScriptDir "src\main.py"

Push-Location $ProjectRoot
try {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 $MainScript
        exit $LASTEXITCODE
    }
    elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
        python3 $MainScript
        exit $LASTEXITCODE
    }
    else {
        throw "Python 3 was not found. Install Python 3 or make the 'py -3' launcher available."
    }
}
finally {
    Pop-Location
}
