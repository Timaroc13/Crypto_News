param(
  [Parameter(Mandatory=$true)]
  [string]$ProjectId,

  [string]$Region = "us-central1",
  [string]$ServiceName = "crypto-news-parser",

  # Container registry: Artifact Registry repository name.
  # The script will create it if it doesn't exist.
  [string]$Repo = "crypto-news",

  # Require auth by default; set -AllowUnauthenticated to make it public.
  [switch]$AllowUnauthenticated,

  # Optional env vars
  [string]$ModelVersion = "news-parser-0.1"
)

# PowerShell can turn native stderr output into errors (NativeCommandError).
# We rely on gcloud exit codes and explicitly throw when needed.
$ErrorActionPreference = "Continue"

$GcloudExe = "gcloud.cmd"
try {
  $resolved = (Get-Command $GcloudExe -ErrorAction Stop).Source
  if ($resolved) {
    $GcloudExe = $resolved
  }
} catch {
  # Fall back to whatever is on PATH.
  $GcloudExe = "gcloud"
}

function Invoke-Gcloud {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Args
  )

  & $GcloudExe @Args
  if ($LASTEXITCODE -ne 0) {
    throw "gcloud failed (exit $LASTEXITCODE): gcloud $($Args -join ' ')"
  }
}

function Test-Gcloud {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Args
  )

  & $GcloudExe @Args 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
}

Write-Host "Setting project..." -ForegroundColor Cyan
Invoke-Gcloud @("config", "set", "project", $ProjectId)

Write-Host "Enabling required services..." -ForegroundColor Cyan
Invoke-Gcloud @(
  "services",
  "enable",
  "run.googleapis.com",
  "cloudbuild.googleapis.com",
  "artifactregistry.googleapis.com"
)

# Ensure Artifact Registry repo exists
$repoFull = "$Region-docker.pkg.dev/$ProjectId/$Repo"
Write-Host "Ensuring Artifact Registry repo exists: $Repo ($Region)" -ForegroundColor Cyan
if (-not (Test-Gcloud @("artifacts", "repositories", "describe", $Repo, "--location", $Region))) {
  Invoke-Gcloud @(
    "artifacts",
    "repositories",
    "create",
    $Repo,
    "--repository-format=docker",
    "--location",
    $Region,
    "--description",
    "Docker images for crypto-news-parser"
  )
}

# NOTE: use ${ServiceName} to avoid PowerShell treating ':latest' like a scoped variable.
$image = "$repoFull/${ServiceName}:latest"

Write-Host "Building and pushing image: $image" -ForegroundColor Cyan
Invoke-Gcloud @(
  "builds",
  "submit",
  "--tag",
  $image
)

$authFlag = "--no-allow-unauthenticated"
if ($AllowUnauthenticated) {
  $authFlag = "--allow-unauthenticated"
}

Write-Host "Deploying to Cloud Run: $ServiceName ($Region)" -ForegroundColor Cyan
# Notes:
# - min-instances=0 keeps scale-to-zero
# - concurrency=80 is a good default for lightweight parsing
# - cpu-boost improves cold start; can be removed to save a bit

Invoke-Gcloud @(
  "run",
  "deploy",
  $ServiceName,
  "--image",
  $image,
  "--region",
  $Region,
  $authFlag,
  "--set-env-vars",
  "MODEL_VERSION=$ModelVersion",
  "--port",
  "8080",
  "--cpu",
  "1",
  "--memory",
  "512Mi",
  "--timeout",
  "60",
  "--concurrency",
  "80",
  "--min-instances",
  "0",
  "--max-instances",
  "10",
  "--cpu-boost"
)

Write-Host "Done." -ForegroundColor Green
Write-Host "Tip: set API_KEY via Secret Manager + --set-secrets API_KEY=...:latest" -ForegroundColor Yellow
