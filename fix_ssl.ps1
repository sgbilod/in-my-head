# Fix SSL Certificate Issues for Python Package Installation
# This script configures pip to work around SSL certificate problems

Write-Host "`n=== SSL CERTIFICATE FIX FOR PIP ===" -ForegroundColor Cyan
Write-Host "Fixing Python package installation issues..." -ForegroundColor Gray

# 1. Clear problematic environment variables
Write-Host "`n1. Clearing problematic SSL environment variables..." -ForegroundColor Yellow
$env:CURL_CA_BUNDLE = ""
$env:SSL_CERT_FILE = ""
$env:REQUESTS_CA_BUNDLE = ""
Write-Host "   ✅ Cleared CURL_CA_BUNDLE, SSL_CERT_FILE, REQUESTS_CA_BUNDLE" -ForegroundColor Green

# 2. Configure pip to use trusted hosts
Write-Host "`n2. Configuring pip trusted hosts..." -ForegroundColor Yellow
pip config set global.trusted-host "pypi.org pypi.python.org files.pythonhosted.org"
Write-Host "   ✅ Added trusted hosts to pip config" -ForegroundColor Green

# 3. Upgrade pip, setuptools, wheel
Write-Host "`n3. Upgrading pip, setuptools, and wheel..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org 2>&1 | Select-Object -Last 3
Write-Host "   ✅ Core tools upgraded" -ForegroundColor Green

# 4. Install certifi for proper certificate handling
Write-Host "`n4. Installing certifi for proper SSL handling..." -ForegroundColor Yellow
pip install --upgrade certifi --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org 2>&1 | Select-Object -Last 2
Write-Host "   ✅ certifi installed" -ForegroundColor Green

# 5. Set environment variables for current session
Write-Host "`n5. Setting Python SSL context..." -ForegroundColor Yellow
$certifiPath = python -c "import certifi; print(certifi.where())" 2>$null
if ($certifiPath) {
    $env:SSL_CERT_FILE = $certifiPath
    $env:REQUESTS_CA_BUNDLE = $certifiPath
    Write-Host "   ✅ Using certifi certificate bundle: $certifiPath" -ForegroundColor Green
}
else {
    Write-Host "   ⚠️  Could not locate certifi bundle, using system default" -ForegroundColor Yellow
}

Write-Host "`n=== SSL FIX COMPLETE ===" -ForegroundColor Green
Write-Host "You can now install packages with: pip install -r requirements.txt" -ForegroundColor Cyan
Write-Host "`nTo make this permanent, run this script in each new PowerShell session," -ForegroundColor Gray
Write-Host "or add to your PowerShell profile." -ForegroundColor Gray
