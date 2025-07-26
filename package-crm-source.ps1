#!/usr/bin/env pwsh
# Package CRM source code for CodeBuild

param(
    [string]$BucketName = "cura-genesis-crm-build-$(Get-Random)",
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Packaging CRM source code for remote build..." -ForegroundColor Green
Write-Host ""

# Create a temporary build directory
$buildDir = "crm-build-temp"
if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
New-Item -ItemType Directory -Path $buildDir | Out-Null

Write-Host "✅ Created temporary build directory" -ForegroundColor Green

# Copy essential files
$filesToCopy = @(
    "crm_main.py",
    "crm_shared_models.py", 
    "crm_monitoring.py",
    "requirements.txt",
    "manifest.json"
)

foreach ($file in $filesToCopy) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $buildDir -Force
        Write-Host "✅ Copied $file" -ForegroundColor Green
    } else {
        Write-Host "⚠️  File $file not found, skipping" -ForegroundColor Yellow
    }
}

# Create a proper Dockerfile
$dockerfile = @"
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 crmuser && chown -R crmuser:crmuser /app
USER crmuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "crm_main.py"]
"@

$dockerfile | Out-File -FilePath "$buildDir/Dockerfile" -Encoding UTF8
Write-Host "✅ Created Dockerfile" -ForegroundColor Green

# Create buildspec.yml
$buildspec = @"
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region `$AWS_DEFAULT_REGION | docker login --username AWS --password-stdin `$AWS_ACCOUNT_ID.dkr.ecr.`$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=`$AWS_ACCOUNT_ID.dkr.ecr.`$AWS_DEFAULT_REGION.amazonaws.com/`$IMAGE_REPO_NAME
      - IMAGE_TAG=`${CODEBUILD_RESOLVED_SOURCE_VERSION:0:7}
      - echo Repository URI is `$REPOSITORY_URI
      - echo Image tag is `$IMAGE_TAG
  build:
    commands:
      - echo Build started on ``date``
      - echo Building the Docker image...
      - docker build -t `$IMAGE_REPO_NAME .
      - docker tag `$IMAGE_REPO_NAME:`$IMAGE_TAG `$REPOSITORY_URI:`$IMAGE_TAG
      - docker tag `$IMAGE_REPO_NAME:`$IMAGE_TAG `$REPOSITORY_URI:latest
  post_build:
    commands:
      - echo Build completed on ``date``
      - echo Pushing the Docker image...
      - docker push `$REPOSITORY_URI:`$IMAGE_TAG
      - docker push `$REPOSITORY_URI:latest
      - echo Image pushed successfully
"@

$buildspec | Out-File -FilePath "$buildDir/buildspec.yml" -Encoding UTF8
Write-Host "✅ Created buildspec.yml" -ForegroundColor Green

# Create ZIP package
$zipFile = "crm-source.zip"
if (Test-Path $zipFile) { Remove-Item $zipFile -Force }

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory((Resolve-Path $buildDir), (Resolve-Path .), "Optimal", $false)

Write-Host "✅ Created source package: $zipFile" -ForegroundColor Green

# Clean up temp directory
Remove-Item -Recurse -Force $buildDir

Write-Host ""
Write-Host "📦 Source package ready: $zipFile" -ForegroundColor Cyan
Write-Host "🚀 Ready to upload and trigger CodeBuild..." -ForegroundColor Cyan 