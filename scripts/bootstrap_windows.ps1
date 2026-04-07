$ErrorActionPreference = "Stop"

$Python = ".\.venv\Scripts\python.exe"

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

if (-not (Test-Path $Python)) {
    Write-Host "[1/4] Creating .venv with Python 3.12"
    if (Get-Command py -ErrorAction SilentlyContinue) {
        Invoke-Checked py -3.12 -m venv .venv
    } else {
        Invoke-Checked python -m venv .venv
    }
} else {
    Write-Host "[1/4] Reusing existing .venv"
}

Write-Host "[2/4] Installing Python dependencies"
Invoke-Checked $Python -m pip install --upgrade pip
Invoke-Checked $Python -m pip install -r requirements.txt

$DenseChunks = "artifacts\dense_chunks.faiss"
$DenseMain = "artifacts\dense_main_passages.faiss"

if ((Test-Path $DenseChunks) -and (Test-Path $DenseMain)) {
    Write-Host "[3/4] Dense FAISS indexes already exist"
} else {
    Write-Host "[3/4] Building dense FAISS indexes"
    Invoke-Checked $Python scripts\build_dense_index.py
}

Write-Host "[4/4] Bootstrap complete"
Write-Host "Start the app with:"
Write-Host "  .\.venv\Scripts\python.exe -m backend.api.minimal_api --host 127.0.0.1 --port 8000"
