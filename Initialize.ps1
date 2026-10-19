if (-not (Get-Command uv -EA SilentlyContinue)) {
    if ($IsWindows) { irm https://astral.sh/uv/install.ps1 | iex } else { curl -sSf https://astral.sh/uv/install.sh | sh }
    $env:Path = "$env:HOME/.local/bin;$env:LOCALAPPDATA\bin;$env:Path"
}

uv venv .venv --prompt Agradrishti --python 3.12 --allow-existing

$H = switch ($true) {
    $IsWindows { (Get-PnpDevice -EA SilentlyContinue).FriendlyName; break }
    { $IsLinux -and (Get-Command lspci -EA SilentlyContinue) } { lspci; break }
    { $IsMacOS -and (Get-Command system_profiler -EA SilentlyContinue) } { system_profiler SPDisplaysDataType; break }
}

$E = switch ($true) {
    { Get-Command nvidia-smi -EA SilentlyContinue } { "cuda"; break }
    { $H -match "Intel.*NPU|Intel.*AI Boost" } { "openvino"; break }
    { $H -match "Radeon|AMD.*Graphics|Intel.*Graphics" } { "directml"; break }
}

uv sync $(if ($E) { "--extra=$E" })
Write-Host "`nEnvironment instantiated | Framework: $($E ?? 'cpu')"
