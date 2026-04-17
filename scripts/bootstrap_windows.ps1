[CmdletBinding()]
param(
    [switch] $SkipDenseIndex,
    [switch] $SkipFrontendBuild
)

$ErrorActionPreference = "Stop"

$Python = ".\.venv\Scripts\python.exe"
$FrontendDir = "frontend"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $CommandArgs
    )

    & $Command @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command $($CommandArgs -join ' ')"
    }
}

function Require-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string] $CommandName,
        [Parameter(Mandatory = $true)]
        [string] $ErrorMessage
    )

    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw $ErrorMessage
    }
}

if (-not (Test-Path $Python)) {
    Write-Host "[1/5] Creating .venv with Python 3.12"
    if (Get-Command py -ErrorAction SilentlyContinue) {
        Invoke-Checked py -3.12 -m venv .venv
    } else {
        Invoke-Checked python -m venv .venv
    }
} else {
    Write-Host "[1/5] Reusing existing .venv"
}

Write-Host "[2/5] Installing Python dependencies"
Invoke-Checked $Python -m pip install --upgrade pip
Invoke-Checked $Python -m pip install -r requirements.txt

Write-Host "[3/5] Installing frontend dependencies"
Require-Command npm "Node.js and npm are required for the React frontend. Install Node.js LTS, then rerun this script."
Push-Location $FrontendDir
try {
    Invoke-Checked npm install

    if ($SkipFrontendBuild) {
        Write-Host "[4/5] Skipping frontend production build"
    } else {
        Write-Host "[4/5] Building frontend dist bundle"
        Invoke-Checked npm run build
    }
} finally {
    Pop-Location
}

$DenseChunks = "artifacts\dense_chunks.faiss"
$DenseMain = "artifacts\dense_main_passages.faiss"

if ($SkipDenseIndex) {
    Write-Host "[5/5] Skipping dense FAISS index build"
} elseif ((Test-Path $DenseChunks) -and (Test-Path $DenseMain)) {
    Write-Host "[5/5] Dense FAISS indexes already exist"
} else {
    Write-Host "[5/5] Building dense FAISS indexes"
    Invoke-Checked $Python scripts\build_dense_index.py
}

Write-Host "[done] Bootstrap complete"
Write-Host "Start the built app with:"
Write-Host "  .\.venv\Scripts\python.exe -m backend.api.minimal_api --host 127.0.0.1 --port 8000"
Write-Host "For development with hot reload, run:"
Write-Host "  .\.venv\Scripts\python.exe scripts\dev.py"
