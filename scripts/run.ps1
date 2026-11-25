param(
    [ValidateSet('setup','download','process','train','evaluate','app','test','lint','quick','demo','full')]
    [string]$Task = 'app'
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCommand) { $uvPath = $uvCommand.Source }
elseif (Test-Path -LiteralPath '.tools\bin\uv.exe') { $uvPath = '.tools\bin\uv.exe' }
else { throw 'Install uv using the README setup instructions, then rerun this script.' }
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location) '.python'
switch ($Task) {
    'setup' { & $uvPath sync --extra forest }
    'app' { & $uvPath run streamlit run app/main.py }
    'test' { & $uvPath run pytest }
    'lint' {
        & $uvPath run ruff check src app tests scripts
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $uvPath run ruff format --check src app tests scripts
    }
    'quick' { & $uvPath run causal-target run --profile quick --source synthetic }
    'demo' { & $uvPath run causal-target run --profile demo }
    'full' { & $uvPath run causal-target run --profile full }
    default { & $uvPath run causal-target $Task --profile demo }
}
exit $LASTEXITCODE
