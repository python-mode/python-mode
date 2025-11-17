# PowerShell script for running Vader tests on Windows
# This script is designed to run in GitHub Actions CI environment on Windows

# Set error action preference but allow continue on some errors
$ErrorActionPreference = "Continue"

# Colors for output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

Set-Location $ProjectRoot

Write-Info "Project root: $ProjectRoot"
Write-Info "PowerShell version: $($PSVersionTable.PSVersion)"
Write-Info "OS: $([System.Environment]::OSVersion.VersionString)"

# Create /tmp symlink or directory for Windows compatibility
# Some tests use /tmp/ paths which don't exist on Windows
$TmpDir = $env:TEMP
if (-not (Test-Path "C:\tmp")) {
    # Try to create C:\tmp directory
    try {
        New-Item -ItemType Directory -Path "C:\tmp" -Force | Out-Null
        Write-Info "Created C:\tmp directory for test compatibility"
    } catch {
        Write-Warn "Could not create C:\tmp, tests using /tmp/ may fail"
    }
}

# Try python3 first, then python, then py
$PythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} else {
    Write-Error "Python is not installed (tried python3, python, py)"
    exit 1
}

Write-Info "Python command: $PythonCmd"
Write-Info "Python version: $(& $PythonCmd --version 2>&1)"

# Try to find vim in PATH or common locations
$VimCmd = $null
if (Get-Command vim -ErrorAction SilentlyContinue) {
    $VimCmd = "vim"
} else {
    # Try common Vim installation paths
    $possiblePaths = @(
        "C:\Program Files (x86)\Vim\vim91\vim.exe",
        "C:\Program Files\Vim\vim91\vim.exe",
        "C:\tools\vim\vim91\vim.exe"
    )
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $VimCmd = $path
            $env:Path += ";$(Split-Path $path -Parent)"
            Write-Info "Found Vim at: $VimCmd"
            break
        }
    }
    if (-not $VimCmd) {
        Write-Error "Vim is not installed or not found in PATH"
        exit 1
    }
}

Write-Info "Vim command: $VimCmd"
Write-Info "Vim version: $(& $VimCmd --version 2>&1 | Select-Object -First 1)"

# Prerequisites already checked above

# Set up Vim runtime paths (Windows uses different path format)
$VimHome = Join-Path $env:USERPROFILE ".vim"
$VaderDir = Join-Path $VimHome "pack\vader\start\vader.vim"
$PymodeDir = $ProjectRoot

# Install Vader.vim if not present
if (-not (Test-Path $VaderDir)) {
    Write-Info "Installing Vader.vim..."
    $VaderParent = Split-Path -Parent $VaderDir
    New-Item -ItemType Directory -Force -Path $VaderParent | Out-Null
    
    # Use git to clone Vader.vim
    $env:GIT_TERMINAL_PROMPT = 0
    git clone --depth 1 https://github.com/junegunn/vader.vim.git $VaderDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install Vader.vim"
        exit 1
    }
    Write-Success "Vader.vim installed"
} else {
    Write-Info "Vader.vim already installed"
}

# Create a CI-specific vimrc
$CiVimrc = Join-Path $ProjectRoot "tests\utils\vimrc.ci"
$VimHomeEscaped = $VimHome -replace '\\', '\\'
$ProjectRootEscaped = $ProjectRoot -replace '\\', '\\'

$VimrcContent = @"
" CI-specific vimrc for Windows test execution
set nocompatible
set nomore
set shortmess=at
set cmdheight=10
set backupdir=
set directory=
set undodir=
set viewdir=
set noswapfile
set nobackup
set nowritebackup
set paste
set shell=cmd.exe

" Enable magic for motion support (required for text object mappings)
set magic

" Enable filetype detection
filetype plugin indent on
syntax on

" Set up runtimepath for CI environment
let s:vim_home = '$VimHomeEscaped'
let s:project_root = '$ProjectRootEscaped'

" Add Vader.vim to runtimepath (Windows uses backslashes)
execute 'set rtp+=' . substitute(s:vim_home . '\pack\vader\start\vader.vim', '\\', '/', 'g')

" Add python-mode to runtimepath
execute 'set rtp+=' . substitute(s:project_root, '\\', '/', 'g')

" Load python-mode configuration FIRST to set g:pymode_rope = 1
if filereadable(substitute(s:project_root . '\tests\utils\pymoderc', '\\', '/', 'g'))
    execute 'source ' . substitute(s:project_root . '\tests\utils\pymoderc', '\\', '/', 'g')
endif

" Load python-mode plugin AFTER pymoderc so it sees rope is enabled
runtime plugin/pymode.vim

" Ensure rope variables exist even if rope gets disabled later
if !exists('g:pymode_rope_completion')
    let g:pymode_rope_completion = 1
endif
if !exists('g:pymode_rope_autoimport_import_after_complete')
    let g:pymode_rope_autoimport_import_after_complete = 0
endif
if !exists('g:pymode_rope_regenerate_on_write')
    let g:pymode_rope_regenerate_on_write = 1
endif
if !exists('g:pymode_rope_goto_definition_bind')
    let g:pymode_rope_goto_definition_bind = '<C-c>g'
endif
if !exists('g:pymode_rope_rename_bind')
    let g:pymode_rope_rename_bind = '<C-c>rr'
endif
if !exists('g:pymode_rope_extract_method_bind')
    let g:pymode_rope_extract_method_bind = '<C-c>rm'
endif
if !exists('g:pymode_rope_organize_imports_bind')
    let g:pymode_rope_organize_imports_bind = '<C-c>ro'
endif
"@

Set-Content -Path $CiVimrc -Value $VimrcContent -Encoding UTF8
Write-Info "Created CI vimrc at $CiVimrc"

# Find test files
$TestFiles = @()
$VaderDirPath = Join-Path $ProjectRoot "tests\vader"
if (Test-Path $VaderDirPath) {
    $TestFiles = Get-ChildItem -Path $VaderDirPath -Filter "*.vader" -File | Sort-Object Name | ForEach-Object { $_.FullName }
}

if ($TestFiles.Count -eq 0) {
    Write-Error "No Vader test files found in tests\vader\"
    exit 1
}

Write-Info "Found $($TestFiles.Count) test file(s)"

# Run tests
$FailedTests = @()
$PassedTests = @()
$TotalAssertions = 0
$PassedAssertions = 0

foreach ($TestFile in $TestFiles) {
    $TestName = [System.IO.Path]::GetFileNameWithoutExtension($TestFile)
    Write-Info "Running test: $TestName"
    
    # Convert Windows path to Unix-style for Vim (Vim on Windows can handle both)
    $TestFileUnix = $TestFile -replace '\\', '/'
    
    # Run Vader test
    $VimArgs = @(
        "-es",
        "-i", "NONE",
        "-u", $CiVimrc,
        "-c", "Vader! $TestFileUnix",
        "-c", "qa!"
    )
    
    try {
        # Capture both stdout and stderr
        # Use a script block to capture all streams
        $Output = & {
            & $VimCmd $VimArgs 2>&1
        } | Out-String
        
        # Get exit code - PowerShell sets $LASTEXITCODE for native commands
        $ExitCode = $LASTEXITCODE
        
        # If LASTEXITCODE is not set (PowerShell < 6), try to determine from $?
        if ($null -eq $ExitCode) {
            if ($?) {
                $ExitCode = 0
            } else {
                $ExitCode = 1
            }
        }
        
        # If exit code is 0 but we have errors in output, check more carefully
        if ($ExitCode -eq 0) {
            # Check if Vim actually ran successfully by looking at output
            if ($Output -match "E\d+|error|Error|ERROR") {
                # Might be an error, but check if it's a Vader test failure vs Vim error
                if ($Output -notmatch "Success/Total:") {
                    # No success message, likely a Vim error
                    # But don't change exit code if we see Vader output
                    if ($Output -notmatch "Vader|vader") {
                        $ExitCode = 1
                    }
                }
            }
        }
        
        # Check for timeout (not applicable in PowerShell, but keep for consistency)
        if ($ExitCode -eq 124) {
            Write-Error "Test timed out: $TestName (exceeded 120s timeout)"
            $FailedTests += $TestName
            continue
        }
        
        # Parse Vader output for success/failure
        if ($Output -match "Success/Total:\s*(\d+)/(\d+)") {
            $PassedCount = [int]$Matches[1]
            $TotalTests = [int]$Matches[2]
            
            # Extract assertion counts if available
            if ($Output -match "assertions:\s*(\d+)/(\d+)") {
                $AssertPassed = [int]$Matches[1]
                $AssertTotal = [int]$Matches[2]
                $TotalAssertions += $AssertTotal
                $PassedAssertions += $AssertPassed
            }
            
            if ($PassedCount -eq $TotalTests) {
                Write-Success "Test passed: $TestName ($PassedCount/$TotalTests)"
                $PassedTests += $TestName
            } else {
                Write-Error "Test failed: $TestName ($PassedCount/$TotalTests passed)"
                Write-Host "--- Test Output for $TestName ---"
                $Output -split "`n" | Select-Object -Last 30 | ForEach-Object { Write-Host $_ }
                Write-Host "--- End Output ---"
                $FailedTests += $TestName
            }
        } elseif ($ExitCode -eq 0 -and $Output -notmatch "(FAILED|failed|error|E\d+)") {
            # Exit code 0 and no errors found - consider it a pass
            Write-Success "Test passed: $TestName (exit code 0, no errors)"
            $PassedTests += $TestName
        } else {
            Write-Error "Test failed: $TestName"
            Write-Host "--- Test Output for $TestName ---"
            Write-Host "Exit code: $ExitCode"
            $Output -split "`n" | Select-Object -Last 50 | ForEach-Object { Write-Host $_ }
            Write-Host "--- End Output ---"
            $FailedTests += $TestName
        }
    } catch {
        Write-Error "Exception running test $TestName : $_"
        Write-Error "Exception details: $($_.Exception.Message)"
        Write-Error "Stack trace: $($_.ScriptStackTrace)"
        $FailedTests += $TestName
    } finally {
        # Cleanup if needed
    }
}

# Generate test results JSON
$ResultsDir = Join-Path $ProjectRoot "results"
$LogsDir = Join-Path $ProjectRoot "test-logs"
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

$TestResultsJson = Join-Path $ProjectRoot "test-results.json"
$PythonVersion = (& $PythonCmd --version 2>&1).ToString() -replace 'Python ', ''
$VimVersion = (& $VimCmd --version 2>&1 | Select-Object -First 1).ToString() -replace '.*VIM.*v(\S+).*', '$1'

$ResultsJson = @{
    timestamp = [int64]((Get-Date).ToUniversalTime() - (Get-Date "1970-01-01")).TotalSeconds
    python_version = $PythonVersion
    vim_version = $VimVersion
    total_tests = $TestFiles.Count
    passed_tests = $PassedTests.Count
    failed_tests = $FailedTests.Count
    total_assertions = $TotalAssertions
    passed_assertions = $PassedAssertions
    results = @{
        passed = $PassedTests
        failed = $FailedTests
    }
} | ConvertTo-Json -Depth 10

Set-Content -Path $TestResultsJson -Value $ResultsJson -Encoding UTF8

# Validate JSON syntax
try {
    $null = $ResultsJson | ConvertFrom-Json
} catch {
    Write-Error "Generated JSON is invalid!"
    Get-Content $TestResultsJson
    exit 1
}

# Create summary log
$SummaryLog = Join-Path $LogsDir "test-summary.log"
$SummaryContent = @"
Test Summary
============
Python Version: $(& $PythonCmd --version 2>&1)
Vim Version: $(& $VimCmd --version 2>&1 | Select-Object -First 1)
Timestamp: $(Get-Date)

Total Tests: $($TestFiles.Count)
Passed: $($PassedTests.Count)
Failed: $($FailedTests.Count)
Total Assertions: $TotalAssertions
Passed Assertions: $PassedAssertions

Passed Tests:
$($PassedTests | ForEach-Object { "  ✓ $_" })

Failed Tests:
$($FailedTests | ForEach-Object { "  ✗ $_" })
"@

Set-Content -Path $SummaryLog -Value $SummaryContent -Encoding UTF8

# Print summary
Write-Host ""
Write-Info "Test Summary"
Write-Info "============"
Write-Info "Total tests: $($TestFiles.Count)"
Write-Info "Passed: $($PassedTests.Count)"
Write-Info "Failed: $($FailedTests.Count)"
if ($TotalAssertions -gt 0) {
    Write-Info "Assertions: $PassedAssertions/$TotalAssertions"
}

if ($FailedTests.Count -gt 0) {
    Write-Host ""
    Write-Error "Failed tests:"
    $FailedTests | ForEach-Object { Write-Host "  ✗ $_" }
    Write-Host ""
    Write-Info "Test results saved to: $TestResultsJson"
    Write-Info "Summary log saved to: $SummaryLog"
    exit 1
} else {
    Write-Host ""
    Write-Success "All tests passed!"
    Write-Info "Test results saved to: $TestResultsJson"
    Write-Info "Summary log saved to: $SummaryLog"
    exit 0
}

