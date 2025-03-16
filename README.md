# HN_summarizer

HN_summarizer is a GitHub Actions-based project that summarizes Hacker News articles using the Gemini LLM and sends the results via email.

## Features

- **LLM: Gemini Only**  
  This project exclusively uses the Gemini LLM.

- **Delivery Method: Email Only**  
  The summarized results are sent solely via email.

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
| `EMAIL_SENDER`      | The email address used as the sender                                   |
| `EMAIL_RECIPIENTS`  | The email address(es) to which summaries are sent                      |
| `EMAIL_USERNAME`    | The username for the email account used to send emails                 |
| `EMAIL_PASSWORD`    | The password or app-specific password for the email account            |

3. **Workflow Execution**  
   Once the GitHub Secrets are configured, the GitHub Actions workflow will run automatically, summarize the Hacker News articles using Gemini, and send the summary to the specified email address.

## Workflow Details

- The workflow configuration is located in the `.github/workflows/` directory.
- You can adjust the trigger schedules and other settings within the workflow file as needed.

## Notes

- Since this project runs on GitHub Actions, there is no need to clone the repository locally.
- Always manage sensitive information (such as API keys and email credentials) via GitHub Secrets.

## License

This project is licensed under the [MIT License](LICENSE).
