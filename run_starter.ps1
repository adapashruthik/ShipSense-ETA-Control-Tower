$ErrorActionPreference = "Stop"
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env" }
if (!(Test-Path ".venv")) { py -3.11 -m venv .venv }
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m generator.generate --size starter --seed 20261022
python -m validation.validate_data
Write-Host "Starter data created. Configure .env, create MySQL schema, then run scripts/load_data.py."
