#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define variables - User should customize these
GCP_PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}" # Get from env var or set YOUR GCP PROJECT ID
GCP_REGION="${GCP_REGION:-us-central1}" # Get from env var or set your preferred region
CLOUD_RUN_SERVICE_NAME="${CLOUD_RUN_SERVICE_NAME:-hn-summarizer}" # Get from env var or set your job name
ARTIFACT_REGISTRY_REPOSITORY="${ARTIFACT_REGISTRY_REPOSITORY:-hn-summarizer-repo}" # Get from env var or set your repository name
IMAGE_NAME="hn-summarizer-app" # Name of the Docker image

# Construct the full image path in Artifact Registry
IMAGE_TAG="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPOSITORY}/${IMAGE_NAME}:latest"

# --- Ensure variables are set ---
if [ "$GCP_PROJECT_ID" == "your-gcp-project-id" ] || \
   [ -z "$GCP_PROJECT_ID" ] || \
   [ -z "$GCP_REGION" ] || \
   [ -z "$CLOUD_RUN_SERVICE_NAME" ] || \
   [ -z "$ARTIFACT_REGISTRY_REPOSITORY" ]; then
  echo "Error: One or more required variables (GCP_PROJECT_ID, GCP_REGION, CLOUD_RUN_SERVICE_NAME, ARTIFACT_REGISTRY_REPOSITORY) are not set."
  echo "Please set them as environment variables or directly in the script."
  exit 1
fi

echo "--- Configuration ---"
echo "GCP Project ID: ${GCP_PROJECT_ID}"
echo "GCP Region: ${GCP_REGION}"
echo "Cloud Run Service Name: ${CLOUD_RUN_SERVICE_NAME}"
echo "Artifact Registry Repository: ${ARTIFACT_REGISTRY_REPOSITORY}"
echo "Image Tag: ${IMAGE_TAG}"
echo "---------------------"

# --- Check for gcloud and Docker ---
if ! command -v gcloud &> /dev/null; then
    echo "gcloud command could not be found. Please install and configure Google Cloud SDK."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "docker command could not be found. Please install Docker."
    exit 1
fi

# --- Authenticate gcloud (if not already authenticated) ---
# This script assumes you've already run 'gcloud auth login' and 'gcloud config set project GCP_PROJECT_ID'
echo "Verifying gcloud authentication and project..."
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$GCP_PROJECT_ID" ]; then
    echo "Warning: Current gcloud project ('$CURRENT_PROJECT') is different from target project ('$GCP_PROJECT_ID')."
    echo "Consider running 'gcloud config set project $GCP_PROJECT_ID'."
fi
# It's generally better to handle login outside the script or use service accounts for CI/CD.

# --- Configure Docker to use gcloud as a credential helper for Artifact Registry ---
echo "Configuring Docker for Artifact Registry at ${GCP_REGION}-docker.pkg.dev..."
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" -q

# --- Build the Docker image ---
echo "Building Docker image: ${IMAGE_NAME}..."
docker build --platform linux/amd64 -t "${IMAGE_NAME}" . -f Dockerfile

# --- Tag the Docker image for Artifact Registry ---
echo "Tagging image as ${IMAGE_TAG}..."
docker tag "${IMAGE_NAME}" "${IMAGE_TAG}"

# --- Push the Docker image to Artifact Registry ---
echo "Pushing image to Artifact Registry: ${IMAGE_TAG}..."
# Ensure the Artifact Registry repository exists. The script could try to create it,
# but that requires more permissions and complexity.
# gcloud artifacts repositories create "${ARTIFACT_REGISTRY_REPOSITORY}" --repository-format=docker --location="${GCP_REGION}" --description="Repository for HN Summarizer" --async
docker push "${IMAGE_TAG}"

# --- Deploy to Cloud Run Job ---
echo "Deploying to Cloud Run Job: ${CLOUD_RUN_SERVICE_NAME} in region ${GCP_REGION}..."

# Define environment variables to be set in Cloud Run.
# The application will use GCP_PROJECT_ID to construct secret resource names.
# Other secret names are hardcoded in settings.py's _get_secret_from_gcp calls.
# If you passed secret names as env vars to Cloud Run and had settings.py read those, you'd list them here.
# Example: --set-env-vars=GCP_SECRET_GEMINI_API_KEY_NAME="HN_SUMMARIZER_GEMINI_API_KEY"
RUN_ENV_VARS="GCP_PROJECT_ID=${GCP_PROJECT_ID}"

# Service account for Cloud Run - replace with your service account if you have a specific one
# It needs roles/secretmanager.secretAccessor for the secrets used.
# And roles/cloudtrace.agent, roles/logging.logWriter (usually default)
CLOUD_RUN_SERVICE_ACCOUNT="${CLOUD_RUN_SERVICE_ACCOUNT:-}" # Optional: Set via env var or leave empty to use default SA for jobs

SERVICE_ACCOUNT_FLAG=""
if [ -n "$CLOUD_RUN_SERVICE_ACCOUNT" ]; then
  SERVICE_ACCOUNT_FLAG="--service-account=${CLOUD_RUN_SERVICE_ACCOUNT}"
fi

# For Cloud Run Jobs, --allow-unauthenticated is not applicable in the same way as services.
# Invocation permissions are typically handled by IAM for the principal triggering the job (e.g., Cloud Scheduler's service account).

gcloud run jobs deploy "${CLOUD_RUN_SERVICE_NAME}" \
  --image "${IMAGE_TAG}" \
  --region "${GCP_REGION}" \
  --set-env-vars "${RUN_ENV_VARS}" \
  ${SERVICE_ACCOUNT_FLAG} \
  --project "${GCP_PROJECT_ID}" \
  --quiet

echo "--- Deployment to Cloud Run Job Complete ---"
echo "Cloud Run Job '${CLOUD_RUN_SERVICE_NAME}' deployed."
echo "You can execute it manually using: gcloud run jobs execute ${CLOUD_RUN_SERVICE_NAME} --region ${GCP_REGION} --project ${GCP_PROJECT_ID}"
echo "---------------------------"

# Make the script executable: chmod +x deploy_to_gcp.sh
