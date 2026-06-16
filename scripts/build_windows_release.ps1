[CmdletBinding()]
param(
    [Parameter()]
    [string]$PythonExecutable = "python"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,

        [Parameter(Mandatory)]
        [string[]]$Arguments,

        [Parameter(Mandatory)]
        [string]$Description
    )

    Write-Host "=== $Description ==="
    & $FilePath @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$distRoot = Join-Path $repoRoot "dist"
$buildRoot = Join-Path $repoRoot "build"
$artifactRoot = Join-Path $repoRoot "artifacts"

$bundleName = "Bureaucrats-and-Broomsticks"
$bundleDirectory = Join-Path $distRoot $bundleName
$exePath = Join-Path $bundleDirectory "$bundleName.exe"

$zipPath = Join-Path `
    $artifactRoot `
    "$bundleName-Windows-x64.zip"

$hashPath = "$zipPath.sha256"

Push-Location $repoRoot

try {
    foreach ($path in @($distRoot, $buildRoot, $artifactRoot)) {
        if (Test-Path $path) {
            Remove-Item -Path $path -Recurse -Force
        }
    }

    New-Item `
        -ItemType Directory `
        -Path $artifactRoot `
        -Force | Out-Null

    Invoke-NativeChecked `
        -FilePath $PythonExecutable `
        -Arguments @(
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--console",
            "--noupx",
            "--name",
            $bundleName,
            "--paths",
            "src",
            "--add-data",
            "data:data",
            "src/bab/main.py"
        ) `
        -Description "PyInstaller Windows build"

    if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) {
        throw "Expected executable was not created: $exePath"
    }

    Copy-Item `
        -LiteralPath (Join-Path $repoRoot "release/PLAY.txt") `
        -Destination (Join-Path $bundleDirectory "PLAY.txt") `
        -Force

    Write-Host "=== Packaged executable smoke test ==="

    $smokeOutput = "quit" | & $exePath 2>&1
    $smokeExitCode = $LASTEXITCODE
    $smokeText = $smokeOutput | Out-String

    Write-Host $smokeText

    if ($smokeExitCode -ne 0) {
        throw "Packaged executable smoke test failed with exit code $smokeExitCode."
    }

    if ($smokeText -notmatch "Game quit") {
        throw "Packaged executable started but did not complete the expected quit flow."
    }

    Compress-Archive `
        -Path (Join-Path $bundleDirectory "*") `
        -DestinationPath $zipPath `
        -CompressionLevel Optimal `
        -Force

    if (-not (Test-Path -LiteralPath $zipPath -PathType Leaf)) {
        throw "Release archive was not created: $zipPath"
    }

    $hash = (
        Get-FileHash `
            -LiteralPath $zipPath `
            -Algorithm SHA256
    ).Hash.ToLowerInvariant()

    [System.IO.File]::WriteAllText(
        $hashPath,
        "$hash  $([System.IO.Path]::GetFileName($zipPath))`n",
        [System.Text.UTF8Encoding]::new($false)
    )

    Write-Host "=== Windows release package created ==="
    Write-Host $zipPath
    Write-Host $hashPath
}
finally {
    Pop-Location
}
