# HN Summarizer

A tool to fetch, summarize, and deliver top Hacker News stories on a daily basis.

## Features

- **Automated Fetching**: Retrieves the top stories from Hacker News API daily
- **Content Extraction**: Extracts the main content from article URLs
- **AI Summarization**: Summarizes articles using Google's Gemini 1.5 Flash (with support for OpenAI, Anthropic, or local Ollama)
- **Email Delivery**: Sends summaries via email (with support for Slack or LINE)
- **Secure Configuration**: Handles sensitive credentials via environment variables
- **Scheduled Execution**: Runs automatically using GitHub Actions

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`
- API keys for the chosen LLM provider
- Credentials for the chosen delivery method

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/HN_summarizer.git
   cd HN_summarizer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a configuration file:
   ```bash
   cp config.yaml.example config.yaml
   ```

4. Edit `config.yaml` with your settings and API keys, or set up environment variables.

## Usage

### Running Manually

Run the script with default settings:

```bash
python src/main.py
```

Specify a custom configuration file:

```bash
python src/main.py --config my_config.yaml
```

Fetch a different number of top stories:

```bash
python src/main.py --top 5
```

Override the delivery method:

```bash
python src/main.py --delivery slack
```

Enable debug logging:

```bash
python src/main.py --debug
```

### Automated Execution with GitHub Actions

The repository includes a GitHub Actions workflow that runs the script daily. To use it:

1. Fork this repository
2. Add your API keys and credentials as GitHub Secrets:
   - `GEMINI_API_KEY` (or other LLM API keys)
   - `EMAIL_USERNAME` and `EMAIL_PASSWORD`
3. Customize the schedule in `.github/workflows/daily_summary.yml` if needed

## Configuration

The `config.yaml` file allows you to customize:

- LLM provider (OpenAI, Anthropic, or Ollama)
- Delivery method (email, Slack, or LINE)
- Security settings

See `config.yaml.example` for a complete example with comments.

### LLM Provider Options

#### Google Gemini (Default)
- Pros: Cost-effective, fast, good quality
- Cons: Newer API, may have fewer features than more established options

#### OpenAI
- Pros: Good quality, widely used
- Cons: Not the cheapest option

#### Anthropic Claude
- Pros: Good at understanding context, competitive pricing
- Cons: API may be less stable than OpenAI

#### Ollama (Local LLM)
- Pros: Free, no API costs, private
- Cons: Requires local setup, quality may vary by model

### Delivery Method Options

#### Email
- Good for personal use
- Supports HTML formatting

#### Slack
- Good for team collaboration
- Supports rich formatting with blocks

#### LINE
- Popular in Japan and parts of Asia
- Good for mobile notifications

## Security Considerations

- API keys and credentials are sensitive information
- Use environment variables when possible
- GitHub Secrets for CI/CD
- Be mindful of rate limits and API costs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
