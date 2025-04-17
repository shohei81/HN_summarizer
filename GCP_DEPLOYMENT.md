# GCP Deployment Guide for HN Summarizer with Secret Manager

This guide provides step-by-step instructions for deploying the HN Summarizer application to Google Cloud Platform (GCP) using Cloud Run Jobs with Secret Manager integration. This deployment method addresses GitHub Actions vulnerabilities by providing a more secure execution environment and securely manages sensitive information.

## Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed and configured
- Docker installed locally (for testing)
- Git installed

## Deployment Steps

### 1. Set Up GCP Project

```bash
# Create a new GCP project (or use an existing one)
gcloud projects create [PROJECT_ID] --name="HN Summarizer"
gcloud config set project [PROJECT_ID]

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com \
                       run.googleapis.com \
                       artifactregistry.googleapis.com \
                       cloudscheduler.googleapis.com \
                       secretmanager.googleapis.com

# Create Artifact Registry repository
gcloud artifacts repositories create hn-summarizer-repo \
    --repository-format=docker \
    --location=asia-northeast1 \
    --description="HN Summarizer Docker Repository"
```

### 2. Set Up Secret Manager

```bash
# Create secrets for sensitive information
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "YOUR_EMAIL_USERNAME" | gcloud secrets create email-username --data-file=-
echo -n "YOUR_EMAIL_PASSWORD" | gcloud secrets create email-password --data-file=-
echo -n "YOUR_EMAIL_SENDER" | gcloud secrets create email-sender --data-file=-
echo -n "YOUR_EMAIL_RECIPIENTS" | gcloud secrets create email-recipients --data-file=-
echo -n "YOUR_SLACK_WEBHOOK_URL" | gcloud secrets create slack-webhook-url --data-file=-
echo -n "YOUR_SLACK_CHANNEL" | gcloud secrets create slack-channel --data-file=-
```

### 3. Create Service Account

```bash
# Create service account for the application
gcloud iam service-accounts create hn-summarizer-sa \
    --display-name="HN Summarizer Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:hn-summarizer-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/run.invoker"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:hn-summarizer-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Grant individual secret access
for SECRET_NAME in gemini-api-key email-username email-password email-sender email-recipients slack-webhook-url slack-channel; do
  gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:hn-summarizer-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

### 4. Build and Deploy the Container

```bash
# Clone the repository (if not already done)
git clone https://github.com/yourusername/hn-summarizer.git
cd hn-summarizer

# Update config.yaml to use Secret Manager
cat > config.yaml << EOF
# HN Summarizer Configuration

# Summarizer configuration
summarizer:
  provider: gemini
  gemini_model: gemini-2.0-flash
  max_tokens: 500

# Delivery configuration
delivery:
  method: email,slack

  email:
    smtp_server: smtp.gmail.com
    smtp_port: 587
    subject_template: "Hacker News Top Stories - {date}"

  slack:
    channel: "#hn-summaries"
    username: "HN Summarizer Bot"
    icon_emoji: ":newspaper:"
    max_summaries_per_message: 1

# Security configuration
security:
  use_environment_variables: true
  use_secret_manager: true
  secret_manager_project: "[PROJECT_ID]"
  encrypt_api_keys: false
EOF

# Build and push the container using Cloud Build
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/[PROJECT_ID]/hn-summarizer-repo/hn-summarizer:latest
```

### 5. Create Cloud Run Job

```bash
# Create the Cloud Run Job
gcloud run jobs create hn-summarizer-job \
    --image=asia-northeast1-docker.pkg.dev/[PROJECT_ID]/hn-summarizer-repo/hn-summarizer:latest \
    --region=asia-northeast1 \
    --memory=1Gi \
    --timeout=30m \
    --max-retries=3 \
    --service-account=hn-summarizer-sa@[PROJECT_ID].iam.gserviceaccount.com
```

### 6. Set Up Cloud Scheduler

```bash
# Create a Cloud Scheduler job to run the Cloud Run Job daily
gcloud scheduler jobs create http hn-summarizer-scheduler \
    --schedule="0 23 * * *" \
    --time-zone="Asia/Tokyo" \
    --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/[PROJECT_ID]/jobs/hn-summarizer-job:run" \
    --oauth-service-account-email="hn-summarizer-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --description="HN Summarizer Periodic Execution Scheduler"
```

### 7. Test the Deployment

```bash
# Execute the job manually to test
gcloud run jobs execute hn-summarizer-job --region=asia-northeast1

# Check the job execution status
gcloud run jobs executions list --job=hn-summarizer-job --region=asia-northeast1
```

## Secret Manager Integration Details

The HN Summarizer application is configured to use Secret Manager for managing sensitive information. The integration works as follows:

1. **Configuration**: The `config.yaml` file has `use_secret_manager: true` to enable Secret Manager integration.

2. **Authentication**: The Cloud Run Job uses a service account with Secret Manager access permissions.

3. **Secret Naming Convention**: The application expects secrets with the following names:
   - `gemini-api-key`: API key for the Gemini LLM
   - `email-username`: Email username for SMTP authentication
   - `email-password`: Email password for SMTP authentication
   - `email-sender`: Email sender address
   - `email-recipients`: Comma-separated list of email recipients
   - `slack-webhook-url`: Webhook URL for Slack integration
   - `slack-channel`: Slack channel name (optional)

4. **Fallback Mechanism**: If a secret cannot be accessed, the application will fall back to environment variables if `use_environment_variables` is also enabled.

## Troubleshooting

### Common Issues

1. **Secret Manager Access Issues**:
   - Ensure the service account has the necessary permissions.
   - Check if the secrets exist with the expected names.
   - Verify the project ID in the configuration.

2. **Container Startup Issues**:
   - Check the container logs: `gcloud run jobs executions describe EXECUTION_ID --region=asia-northeast1`
   - Verify that the service account has the necessary permissions.

3. **Scheduler Not Triggering**:
   - Verify the scheduler configuration.
   - Check if the service account has the necessary permissions to invoke the job.

### Viewing Logs

```bash
# Get the execution ID
EXECUTION_ID=$(gcloud run jobs executions list --job=hn-summarizer-job --region=asia-northeast1 --format="value(name)" --limit=1)

# View logs for the execution
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=hn-summarizer-job AND resource.labels.execution_name=$EXECUTION_ID" --project=[PROJECT_ID] --limit=100
```

## Security Considerations

1. **Secret Management**: All sensitive information is stored in GCP Secret Manager, which provides encryption at rest and in transit.

2. **Service Account Permissions**: The service account has only the necessary permissions to access the required resources.

3. **Non-root User**: The Docker container runs as a non-root user to enhance security.

4. **Distroless Image**: The application uses a distroless image, which contains only the application and its runtime dependencies, reducing the attack surface.

5. **Regular Updates**: The base image is regularly updated with security patches.

## Maintenance

### Updating Secrets

```bash
# Update an existing secret
echo -n "NEW_SECRET_VALUE" | gcloud secrets versions add gemini-api-key --data-file=-
```

### Updating the Application

1. Make changes to the code.
2. Build and push a new container image.
3. Update the Cloud Run Job to use the new image.

```bash
# Build and push a new image
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/[PROJECT_ID]/hn-summarizer-repo/hn-summarizer:latest

# Update the Cloud Run Job
gcloud run jobs update hn-summarizer-job \
    --image=asia-northeast1-docker.pkg.dev/[PROJECT_ID]/hn-summarizer-repo/hn-summarizer:latest \
    --region=asia-northeast1
