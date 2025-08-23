# Universal DJ USB - Windows Build Script (PowerShell)
# Uses spec files for customization, keeping this script simple and maintainable

param(
    [switch]$GUI,
    [switch]$CLI,
    [switch]$Both,
    [switch]$Clean,
    [switch]$SkipTests,
    [switch]$Help
)

# Colors for output
$RED = "Red"
$GREEN = "Green" 
$YELLOW = "Yellow"

# Build configuration
try {
    $VERSION = & uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>$null
    if ($LASTEXITCODE -ne 0) {
        # Fallback method
        $VERSION = (Get-Content pyproject.toml | Select-String 'version = "(.+)"').Matches[0].Groups[1].Value
    }
} catch {
    $VERSION = "unknown"
}

$PLATFORM = "windows"
$ARCH = if ([Environment]::Is64BitOperatingSystem) { "x64" } else { "x86" }

function Write-Header {
    Write-Host "Universal DJ USB - Build Script" -ForegroundColor $GREEN
    Write-Host "===============================" -ForegroundColor $GREEN
    Write-Host ""
    Write-Host "Version: $VERSION"
    Write-Host "Platform: $PLATFORM-$ARCH"
    Write-Host ""
}

function Show-Help {
    Write-Host "Usage: .\build.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -GUI          Build GUI application (default)"
    Write-Host "  -CLI          Build CLI application"
    Write-Host "  -Both         Build both GUI and CLI"
    Write-Host "  -Clean        Clean build artifacts before building"
    Write-Host "  -SkipTests    Skip running tests"
    Write-Host "  -Help         Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\build.ps1                    # Build GUI with default settings"
    Write-Host "  .\build.ps1 -CLI              # Build CLI only"
    Write-Host "  .\build.ps1 -Both -Clean      # Clean build both applications"
}

function Clean-Build {
    Write-Host "Cleaning build artifacts..." -ForegroundColor $YELLOW
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    Write-Host "✓ Build artifacts cleaned"
    Write-Host ""
}

function Install-Dependencies {
    Write-Host "Installing dependencies..." -ForegroundColor $YELLOW
    & uv sync --dev
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install dependencies"
        exit 1
    }
    Write-Host "✓ Dependencies installed"
    Write-Host ""
}

function Build-GUI {
    Write-Host "Building GUI application..." -ForegroundColor $YELLOW
    
    # Check if spec file exists
    if (-not (Test-Path "udj_gui.spec")) {
        Write-Error "udj_gui.spec not found"
        exit 1
    }
    
    & uv run pyinstaller udj_gui.spec --clean --noconfirm
    if ($LASTEXITCODE -ne 0) {
        Write-Error "GUI build failed"
        exit 1
    }
    
    # Cleanup Qt frameworks to reduce size (Windows version)
    if (Test-Path "scripts/cleanup_qt_frameworks.py") {
        Write-Host "Cleaning up Qt frameworks..." -ForegroundColor $YELLOW
        & uv run python scripts/cleanup_qt_frameworks.py "Universal DJ USB"
    }
    
    Write-Host "Creating portable Windows executable..." -ForegroundColor $YELLOW
    New-WindowsExecutable-GUI
    
    Write-Host "✓ GUI build completed"
}

function Build-CLI {
    Write-Host "Building CLI application..." -ForegroundColor $YELLOW
    
    # Check if spec file exists
    if (-not (Test-Path "udj_cli.spec")) {
        Write-Error "udj_cli.spec not found"
        exit 1
    }
    
    & uv run pyinstaller udj_cli.spec --clean --noconfirm
    if ($LASTEXITCODE -ne 0) {
        Write-Error "CLI build failed"
        exit 1
    }
    
    Write-Host "Creating portable CLI executable..." -ForegroundColor $YELLOW
    New-WindowsExecutable-CLI
    
    Write-Host "✓ CLI build completed"
}

function New-WindowsExecutable-GUI {
    # For onefile build, we get a single executable
    $exeName = "Universal DJ USB.exe"
    $exePath = "dist\$exeName"
    
    if (Test-Path $exePath) {
        Write-Host "✓ Single executable created: $exeName"
        Write-Host "  Location: $exePath"
        Write-Host "  Size: $((Get-Item $exePath).Length / 1MB | ForEach-Object { '{0:N1} MB' -f $_ })"
        Write-Host ""
        Write-Host "Your portable application is ready to use!"
    } else {
        Write-Warning "GUI executable not found at $exePath"
    }
}

function New-WindowsExecutable-CLI {
    # For onefile build, we get a single executable
    $exeName = "udj.exe"
    $exePath = "dist\$exeName"
    
    if (Test-Path $exePath) {
        Write-Host "✓ Single executable created: $exeName"
        Write-Host "  Location: $exePath"
        Write-Host "  Size: $((Get-Item $exePath).Length / 1MB | ForEach-Object { '{0:N1} MB' -f $_ })"
        Write-Host ""
        Write-Host "Your portable CLI application is ready to use!"
    } else {
        Write-Warning "CLI executable not found at $exePath"
    }
}

function Invoke-Tests {
    Write-Host "Running tests..." -ForegroundColor $YELLOW
    & uv run pytest --tb=short
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Tests failed"
        exit 1
    }
    Write-Host "✓ Tests passed"
    Write-Host ""
}

function Show-Results {
    Write-Host "Build Results" -ForegroundColor $GREEN
    Write-Host "=============" -ForegroundColor $GREEN
    Write-Host ""
    
    if (Test-Path "dist") {
        Write-Host "Built files:"
        Get-ChildItem "dist" | ForEach-Object {
            $size = if ($_.PSIsContainer) {
                (Get-ChildItem $_.FullName -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
                "{0:N1} MB" -f $size
            } else {
                "{0:N1} MB" -f ($_.Length / 1MB)
            }
            Write-Host "  $($_.Name): $size"
        }
    } else {
        Write-Host "No build artifacts found."
    }
    Write-Host ""
}

# Parse arguments and set defaults
$BUILD_GUI = $false
$BUILD_CLI = $false

if ($Help) {
    Show-Help
    exit 0
}

# Set defaults if no specific build target specified
if (-not $GUI -and -not $CLI -and -not $Both) {
    $BUILD_GUI = $true  # Default to GUI if no arguments
} else {
    $BUILD_GUI = $GUI -or $Both
    $BUILD_CLI = $CLI -or $Both
}

# Main build process
Write-Header

if ($Clean) {
    Clean-Build
}

Install-Dependencies

if (-not $SkipTests) {
    Invoke-Tests
}

if ($BUILD_GUI) {
    Build-GUI
    Write-Host ""
}

if ($BUILD_CLI) {
    Build-CLI  
    Write-Host ""
}

Show-Results

Write-Host "✓ Build completed successfully!" -ForegroundColor $GREEN
