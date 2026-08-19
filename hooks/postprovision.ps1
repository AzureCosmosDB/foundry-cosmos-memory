$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== [postprovision] Setting up Python environment ==="
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Failed to create the Python virtual environment." }
& .\.venv\Scripts\Activate.ps1
python -m pip install --quiet --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip." }
python -m pip install --quiet -r requirements.txt --pre
if ($LASTEXITCODE -ne 0) { throw "Failed to install Python dependencies." }

Write-Host ""
Write-Host "=== [postprovision] Creating Foundry PromptAgent ==="
$agentOut = python -m src.create_agent
if ($LASTEXITCODE -ne 0) { throw "Failed to create or retrieve the Foundry agent." }
$agentOut | ForEach-Object { Write-Host $_ }

$name = ($agentOut | Select-String '^FOUNDRY_AGENT_NAME=(.*)$').Matches.Groups[1].Value
$version = ($agentOut | Select-String '^FOUNDRY_AGENT_VERSION=(.*)$').Matches.Groups[1].Value
if (-not $name -or -not $version) {
  throw "Foundry agent creation did not return a name and version."
}

azd env set FOUNDRY_AGENT_NAME $name | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Failed to persist FOUNDRY_AGENT_NAME." }
$env:FOUNDRY_AGENT_NAME = $name

azd env set FOUNDRY_AGENT_VERSION $version | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Failed to persist FOUNDRY_AGENT_VERSION." }
$env:FOUNDRY_AGENT_VERSION = $version

Write-Host ""
Write-Host "=== [postprovision] Proving cross-conversation Cosmos memory ==="
python -m src.run_memory_test
if ($LASTEXITCODE -ne 0) { throw "The Cosmos memory test failed." }

Write-Host ""
Write-Host "Deployment and memory test succeeded. See README.md to start the browser chat."
