# HN_summarizer

HN_summarizer is a GitHub Actions-based project that summarizes Hacker News articles using the Gemini LLM and sends the results via email or Slack.

## Features

- **LLM: Gemini Only**  
  This project exclusively uses the Gemini LLM.

- **Delivery Methods**  
  - **Email**: Send summaries to specified email addresses
  - **Slack**: Post summaries to a Slack channel using webhooks
  - **Multiple Methods**: Send to both email and Slack simultaneously

- **GitHub Actions Execution**  
  The project runs entirely on GitHub Actions. There is no need to clone the repository locally; simply configure the required secrets in GitHub.

## Setup Instructions

1. **Fork or Create the Repository**  
   Fork the repository or create a new one on GitHub.

2. **Configure GitHub Secrets**  
   Add the following secrets to your GitHub repository settings:

   ### GitHub Secrets Configuration

| Secret Name         | Description                                                            |
|---------------------|------------------------------------------------------------------------|
| `GEMINI_API_KEY`    | API key for accessing the Gemini LLM                                   |
| **Email Delivery**  |                                                                        |
| `EMAIL_SENDER`      | The email address used as the sender                                   |
| `EMAIL_RECIPIENTS`  | The email address(es) to which summaries are sent                      |
| `EMAIL_USERNAME`    | The username for the email account used to send emails                 |
| `EMAIL_PASSWORD`    | The password or app-specific password for the email account            |
| **Slack Delivery**  |                                                                        |
| `SLACK_WEBHOOK_URL` | The webhook URL for posting messages to Slack                          |
| `SLACK_CHANNEL`     | (Optional) The Slack channel to post to (overrides webhook default)    |

3. **Workflow Execution**  
   Once the GitHub Secrets are configured, the GitHub Actions workflow will run automatically, summarize the Hacker News articles using Gemini, and deliver the summaries via your chosen method (email or Slack).

4. **Configuring Delivery Method**  
   To choose your delivery method, you can either:
   
   - Edit the `config.yaml` file directly:
     ```yaml
     delivery:
       method: email  # Change to 'slack' to use Slack delivery
     ```
     
     To use multiple delivery methods, use a comma-separated list:
     ```yaml
     delivery:
       method: email,slack  # Send to both email and Slack
     ```
   
   - Or use the provided utility script:
     ```bash
     # Switch to email delivery
     ./switch_delivery.py email
     
     # Switch to Slack delivery
     ./switch_delivery.py slack
     
     # Switch to both email and Slack
     ./switch_delivery.py email,slack
     ```

## Workflow Details

- The workflow configuration is located in the `.github/workflows/` directory.
- You can adjust the trigger schedules and other settings within the workflow file as needed.

## Slack Webhook Setup

To set up Slack webhook integration:

1. **Create a Slack App**:
   - Go to [Slack API Apps page](https://api.slack.com/apps)
   - Click "Create New App" and choose "From scratch"
   - Name your app (e.g., "HN Summarizer") and select your workspace

2. **Enable Incoming Webhooks**:
   - In the left sidebar, click on "Incoming Webhooks"
   - Toggle "Activate Incoming Webhooks" to On
   - Click "Add New Webhook to Workspace"
   - Select the channel where you want to post summaries
   - Click "Allow" to authorize the webhook

3. **Copy the Webhook URL**:
   - After authorization, you'll see a new webhook URL
   - Copy this URL and add it as the `SLACK_WEBHOOK_URL` secret in your GitHub repository

4. **Configure the Delivery Method**:
   - Edit the `config.yaml` file to use Slack:
   ```yaml
   delivery:
     method: slack
   ```

5. **Test the Webhook Integration**:
   - Use the included test script to verify your webhook is working:
   ```bash
   # Using environment variables
   export SLACK_WEBHOOK_URL="your_webhook_url_here"
   python slack_webhook_test.py

   # Or provide the webhook URL directly
   python slack_webhook_test.py --webhook-url "your_webhook_url_here"
   
   # You can also run it directly (it's executable)
   ./slack_webhook_test.py --webhook-url "your_webhook_url_here"
   ```
   - If successful, you'll see a test message in your Slack channel

## Notes

- Since this project runs on GitHub Actions, there is no need to clone the repository locally.
- Always manage sensitive information (such as API keys and email credentials) via GitHub Secrets.
- The Slack integration uses Slack's Block Kit to format messages in a readable and visually appealing way.

## License

This project is licensed under the [MIT License](LICENSE).
