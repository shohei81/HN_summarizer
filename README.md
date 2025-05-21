# HN Summarizer (Google Cloud Edition)

HN Summarizer is a project designed for deployment on Google Cloud Platform (Cloud Run). It automatically fetches top stories from Hacker News, summarizes them using the Gemini LLM, and delivers these summaries via email or Slack.

## Features

- **LLM: Gemini Only**: Exclusively uses the Google Gemini LLM for summarization.
- **Delivery Methods**:
    - **Email**: Send summaries to specified email addresses.
    - **Slack**: Post summaries to a Slack channel using webhooks.
    - **Multiple Methods**: Configure to send to both email and Slack simultaneously.
- **Cloud Native**: Built for deployment on Google Cloud Platform, leveraging Cloud Run for job execution and Cloud Scheduler for automated execution.

## GCP Deployment and Operations

This section details how to deploy and operate the HN Summarizer on Google Cloud Platform.

### Overview

The application is packaged as a Docker container and deployed as a **Cloud Run Job**. Google Cloud Scheduler is used to trigger this job on a defined schedule (e.g., daily) to fetch, summarize, and deliver news. Secrets are managed using Google Cloud Secret Manager.

### Prerequisites for Deployment

Before you begin, ensure you have the following:

1.  **Google Cloud SDK (`gcloud`)**: Installed and configured. Authenticate with `gcloud auth login` and set your project with `gcloud config set project YOUR_PROJECT_ID`.
2.  **Docker**: Installed locally to build the container image.
3.  **GCP Project**: A Google Cloud Project with billing enabled.
4.  **Required Google Cloud APIs Enabled**: Execute the following commands to enable necessary APIs for your project:
    ```bash
    gcloud services enable artifactregistry.googleapis.com --project YOUR_PROJECT_ID
    gcloud services enable run.googleapis.com --project YOUR_PROJECT_ID
    gcloud services enable cloudscheduler.googleapis.com --project YOUR_PROJECT_ID
    gcloud services enable secretmanager.googleapis.com --project YOUR_PROJECT_ID
    ```
    Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

### Configuration - `config.yaml`

-   The `config.yaml` file in the repository root is used for general application settings, such as the Gemini model to use, number of summaries, and default delivery methods.
-   You can modify `config.yaml` locally before building the Docker container.
-   The `switch_delivery.py` script (located in the repository root) can still be used to easily change the `delivery: method:` in `config.yaml`:
    ```bash
    # Switch to email delivery
    ./switch_delivery.py email

    # Switch to Slack delivery
    ./switch_delivery.py slack

    # Switch to both email and Slack
    ./switch_delivery.py email,slack
    ```

### Secret Management with Google Secret Manager

All sensitive information, such as API keys and credentials, **must** be stored in Google Cloud Secret Manager. The application fetches these secrets at runtime.

**Required Secrets in Secret Manager:**

Create the following secrets in Secret Manager (the names/IDs below are what the application expects):

*   `HN_SUMMARIZER_GEMINI_API_KEY`: Your API key for the Gemini LLM.
*   `HN_SUMMARIZER_EMAIL_USERNAME`: Username for the email account (if using email delivery).
*   `HN_SUMMARIZER_EMAIL_PASSWORD`: Password (or app-specific password) for the email account.
*   `HN_SUMMARIZER_EMAIL_SENDER`: The email address used as the sender.
*   `HN_SUMMARIZER_EMAIL_RECIPIENTS`: Comma-separated list of email addresses for recipients.
*   `HN_SUMMARIZER_SLACK_WEBHOOK_URL`: The webhook URL for posting messages to Slack (if using Slack delivery).
*   `HN_SUMMARIZER_SLACK_CHANNEL`: (Optional) The Slack channel to post to (overrides webhook default).

**Permissions:**

*   The Cloud Run Job's runtime service account needs the **"Secret Manager Secret Accessor"** (`roles/secretmanager.secretAccessor`) IAM role for *each* of the secrets listed above, or on the project/folder level if appropriate.
*   The application also requires the `GCP_PROJECT_ID` environment variable to be set in the Cloud Run Job. The `deploy_to_gcp.sh` script handles setting this automatically during deployment.

### Containerization - `Dockerfile`

A `Dockerfile` is provided in the repository root to package the application, its dependencies, and the `config.yaml` into a container image suitable for Cloud Run.

### Deployment using `deploy_to_gcp.sh`

The `deploy_to_gcp.sh` script automates the build and deployment process.

1.  **Make the script executable**:
    ```bash
    chmod +x deploy_to_gcp.sh
    ```
2.  **Customize Variables**:
    Open `deploy_to_gcp.sh` and customize the following variables at the top of the script, or set them as environment variables before running the script:
    *   `GCP_PROJECT_ID`: Your Google Cloud Project ID.
    *   `GCP_REGION`: The GCP region for your services (e.g., `us-central1`).
    *   `CLOUD_RUN_SERVICE_NAME`: The name for your Cloud Run Job (e.g., `hn-summarizer`). This will be used as the job name.
    *   `ARTIFACT_REGISTRY_REPOSITORY`: The name for your Artifact Registry repository (e.g., `hn-summarizer-repo`).
    *   `CLOUD_RUN_SERVICE_ACCOUNT` (Optional): If you want Cloud Run to use a specific service account, set its email here. Otherwise, it defaults to the Compute Engine default service account. Ensure this service account has Secret Accessor rights.

3.  **Run the script**:
    ```bash
    ./deploy_to_gcp.sh
    ```
    The script will:
    *   Configure Docker to authenticate with Artifact Registry.
    *   Build the Docker image using the `Dockerfile`.
    *   Tag the image.
    *   Push the image to your Artifact Registry repository.
    *   Deploy the image as a Cloud Run Job, setting the `GCP_PROJECT_ID` environment variable.

### Automating with Cloud Scheduler

To run the HN Summarizer application automatically on a schedule (e.g., daily), you can use Google Cloud Scheduler to trigger your deployed **Cloud Run Job**.

**Prerequisites:**

Before creating the Cloud Scheduler job, ensure you have the following:

1.  **Cloud Run Job Deployed**: The HN Summarizer application must be successfully deployed as a Cloud Run Job using the `./deploy_to_gcp.sh` script. The `CLOUD_RUN_SERVICE_NAME` variable in the script defines your Cloud Run Job name.
2.  **GCP Project ID**: Your Google Cloud Project ID (as used in `deploy_to_gcp.sh`).
3.  **Cloud Run Job Region**: The GCP region where your Cloud Run Job is deployed (as specified by `GCP_REGION` in `deploy_to_gcp.sh`).
4.  **Scheduler Invoker Service Account**: A dedicated Google Cloud service account that Cloud Scheduler will use to invoke the Cloud Run Job.
    *   This service account **must** have the **"Cloud Run Invoker"** (`roles/run.invoker`) IAM permission granted on your Cloud Run Job (e.g., `hn-summarizer`) or at the project level.
    *   You can create a new service account for this purpose (e.g., `hn-scheduler-invoker-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com`).

**Creating the Cloud Scheduler Job:**

You can create the Cloud Scheduler job using the `gcloud` command-line tool. Use the `CLOUD_RUN_SERVICE_NAME` (for `--job-name`) and `GCP_REGION` (for `--job-region` and `--location`) values from your `deploy_to_gcp.sh` script or environment variables.

```bash
# Replace placeholders with your actual values
GCP_PROJECT_ID="YOUR_GCP_PROJECT_ID"  # Your Google Cloud Project ID
CLOUD_RUN_JOB_NAME="YOUR_CLOUD_RUN_JOB_NAME"  # Matches CLOUD_RUN_SERVICE_NAME from deploy_to_gcp.sh (e.g., hn-summarizer)
CLOUD_RUN_JOB_REGION="YOUR_JOB_REGION" # Matches GCP_REGION from deploy_to_gcp.sh (e.g., us-central1)
SCHEDULER_JOB_NAME="YOUR_SCHEDULER_JOB_NAME" # e.g., hn-summarizer-trigger
SCHEDULER_INVOKER_SA="YOUR_SCHEDULER_SA_EMAIL" # e.g., scheduler-invoker@${GCP_PROJECT_ID}.iam.gserviceaccount.com

gcloud scheduler jobs create cloud-run-job ${SCHEDULER_JOB_NAME} \
  --schedule "0 23 * * *" \
  --job-name "${CLOUD_RUN_JOB_NAME}" \
  --job-region "${CLOUD_RUN_JOB_REGION}" \
  --service-account-email "${SCHEDULER_INVOKER_SA}" \
  --location "${CLOUD_RUN_JOB_REGION}" \ # Typically same as job region
  --description "Triggers the HN Summarizer Cloud Run Job daily." \
  --project "${GCP_PROJECT_ID}"
```

**Explanation of Parameters:**

*   `YOUR_SCHEDULER_JOB_NAME` (or `${SCHEDULER_JOB_NAME}` in example): A unique name for your scheduler job.
*   `--schedule`: A cron expression defining the job's frequency. The example `"0 23 * * *"` runs the job daily at 11 PM UTC. Adjust as needed. You can also add `--time-zone "Asia/Tokyo"` if you prefer to define the schedule in a specific timezone.
*   `--job-name`: The name of your deployed Cloud Run Job (this corresponds to `CLOUD_RUN_SERVICE_NAME` from `deploy_to_gcp.sh`).
*   `--job-region`: The GCP region where your Cloud Run Job is deployed.
*   `--service-account-email`: The email address of the service account that Cloud Scheduler will use to invoke the Cloud Run Job. This service account needs the `roles/run.invoker` permission on the target Cloud Run Job.
*   `--location`: The GCP region where your Cloud Scheduler job itself will run. It's advisable to choose the same region as your Cloud Run Job.
*   `--description`: A human-readable description for your scheduler job.
*   `--project`: Your GCP Project ID.

### IAM Permissions Summary (General Guidance)

Correct IAM permissions are crucial for the application to function:

*   **Cloud Run Job's Runtime Service Account** (either Compute Engine default or the one specified in `CLOUD_RUN_SERVICE_ACCOUNT` in `deploy_to_gcp.sh`):
    *   `roles/secretmanager.secretAccessor`: To access all the application secrets stored in Secret Manager.
    *   `roles/cloudtrace.agent`: (Recommended) For Cloud Trace integration.
    *   `roles/logging.logWriter`: (Usually default) For writing logs to Cloud Logging.
*   **Cloud Scheduler Service Account** (the one specified by `--service-account-email` when creating the scheduler job):
    *   `roles/run.invoker`: To allow Cloud Scheduler to trigger your Cloud Run **Job**.
*   **User/CI/CD Principal running `deploy_to_gcp.sh`**:
    *   `roles/artifactregistry.writer` (or `roles/artifactregistry.admin`): To push Docker images to Artifact Registry. (The script can create the repository if it doesn't exist, which might require `artifactregistry.admin` or more granular `artifactregistry.repositories.create` permissions).
    *   `roles/run.admin`: To deploy and manage Cloud Run services **and jobs**.
    *   `roles/iam.serviceAccountUser`: To act as/impersonate service accounts if necessary during deployment (e.g., if the Cloud Run Job is configured to run as a specific service account).
    *   `roles/storage.objectAdmin` (or more granular permissions): If Artifact Registry uses Cloud Storage buckets for storing images (which it does by default).

## Slack Webhook Setup

To set up Slack webhook integration for receiving summaries:

1.  **Create a Slack App**:
    *   Go to the [Slack API Apps page](https://api.slack.com/apps).
    *   Click "Create New App" and choose "From scratch".
    *   Name your app (e.g., "HN Summarizer") and select your workspace.

2.  **Enable Incoming Webhooks**:
    *   In the app's settings page, navigate to "Features" -> "Incoming Webhooks" from the sidebar.
    *   Toggle "Activate Incoming Webhooks" to On.
    *   Click "Add New Webhook to Workspace".
    *   Select the channel where you want to post summaries and click "Allow".

3.  **Copy the Webhook URL**:
    *   After authorization, you'll see your new webhook URL.
    *   Copy this URL. You will store it in Google Secret Manager with the name `HN_SUMMARIZER_SLACK_WEBHOOK_URL`.

4.  **Configure Delivery Method in `config.yaml`**:
    *   Ensure `slack` is included in the `delivery: method:` in your `config.yaml` file before building and deploying your Docker image.
    ```yaml
    delivery:
      method: slack # or email,slack
    ```

5.  **Local Test (Optional)**:
    *   To test your Slack webhook URL locally (before deploying or for troubleshooting), use the test script located at `tests/slack_webhook_test.py`.
    *   Run it from the repository root:
    ```bash
    # Ensure SLACK_WEBHOOK_URL is set as an environment variable
    export SLACK_WEBHOOK_URL="your_copied_webhook_url_here"
    python tests/slack_webhook_test.py

    # Or provide the webhook URL directly as an argument
    python tests/slack_webhook_test.py --webhook-url "your_copied_webhook_url_here"
    ```
    *   If successful, you'll see a test message in your configured Slack channel.

## Notes

-   Always manage sensitive information (API keys, credentials) via Google Cloud Secret Manager.
-   The Slack integration uses Slack's Block Kit to format messages for better readability.
-   Review and adjust IAM permissions according to the principle of least privilege for your specific GCP environment.

## License

This project is licensed under the [MIT License](LICENSE).
