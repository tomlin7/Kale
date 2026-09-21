param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$ScriptDir\src;$env:PYTHONPATH"
& "$ScriptDir\.venv\Scripts\kale.exe" @ScriptArgs
