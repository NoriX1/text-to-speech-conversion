param(
    [string]$HostAddress = "",
    [int]$Port = 0
)

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

$settingsRaw = python -c "from app.config import get_settings; s=get_settings(); print(f'{s.app_host}|{s.app_port}')"
$settingsParts = $settingsRaw -split '\|', 2
$envHost = $settingsParts[0]
$envPort = [int]$settingsParts[1]

if ([string]::IsNullOrWhiteSpace($HostAddress)) {
    $HostAddress = $envHost
}
if ($Port -le 0) {
    $Port = $envPort
}

uvicorn app.main:app --host $HostAddress --port $Port
