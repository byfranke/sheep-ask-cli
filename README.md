# Sheep Ask CLI

A command-line interface for sending AI queries to [sheep.byfranke.com](https://sheep.byfranke.com), focused on Cyber Threat Intelligence (CTI) and general security questions.

<p align="center">
  <strong>AI queries from your terminal, fast and secure</strong><br>
  Version 1.0 | byFranke 2026
</p>

---

**About more:** [Sheep API](https://sheep.byfranke.com/index.html#API)

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Get Sheep Ask CLI

```bash
# Run the interactive setup wizard (recommended)
curl -fsSL https://byfranke.com/ask-cli-install | bash
```

### Install from Source

```bash
# Or install manually
git clone https://github.com/byfranke/sheep-ask-cli
cd sheep-ask-cli
chmod +x sheep-ask-cli.py setup.py install.sh
bash install.sh
python3 setup.py
```

## Configuration

### Secure Token Setup

Run the interactive setup wizard to configure your encrypted token:

```bash
python3 setup.py
```

The setup will:
- Ask for your [API token](https://sheep.byfranke.com/discord)
- Set a master password for encryption
- Store your token encrypted in `~/.sheep-ask-cli/config.ini`
- Require the master password **only once per terminal session** (cached in `/tmp` with mode `0600`, scoped to your shell's Session ID)

### Alternative: One-time Use

For single-use or testing, you can pass the token directly:

```bash
sheep-ask --token "your_api_token_here" "What is ransomware?"
```

Or via environment variable:

```bash
export SHEEP_API_TOKEN="your_api_token_here"
sheep-ask "What is ransomware?"
```

**Security**: Your token is always encrypted and password-protected when stored.

## Usage

### Basic Usage

```bash
# Ask a question
sheep-ask "What is ransomware?"

# Multi-word question (no quotes needed)
sheep-ask What are the TTPs of APT29

# Explain a framework
sheep-ask "Explain the MITRE ATT&CK framework"
```

### Save Response to Markdown

```bash
# Save response to sheep_answers_YYYYMMDD_HHMMSS.md in the current directory
sheep-ask -o "What is a zero-day vulnerability?"
```

### Use a File as Context

```bash
# Use a markdown file as context before the question
sheep-ask -p report.md "Summarize the key findings"
sheep-ask --prompt incident.md "What are the IOCs mentioned?"
```

### Output Formats

```bash
# Pretty output (default) - panel with rendered markdown
sheep-ask "Explain phishing"

# Plain text for piping / automation
sheep-ask "Explain phishing" --format plain

# Raw JSON
sheep-ask "Explain phishing" --format json

# Rendered markdown (no panel)
sheep-ask "Explain phishing" --format markdown
```

### Session Management

```bash
# Clear the cached decrypted token for the current terminal only
sheep-ask --logout
```

### Maintenance

```bash
# Show help
sheep-ask --help

# Show version
sheep-ask --version

# Re-run the setup wizard
sheep-ask --setup

# Check for updates from GitHub
sheep-ask --update
```

### Common Issues

1. **API Token Error**
   ```
   Error: API token is required
   ```
   Solution: Run `python3 setup.py` or set `SHEEP_API_TOKEN`.

2. **Connection Error**
   ```
   Error: Failed to connect to API server
   ```
   Solution: Check your internet connection and the API URL.

3. **Request Too Large (HTTP 422)**
   ```
   Error: Request too large or invalid format
   ```
   Solution: Use a shorter question or a smaller context file with `-p`.

4. **Timeout Error**
   ```
   Error: Request timed out
   ```
   Solution: The query is taking longer than 60s. Try again or simplify the question.

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Security Considerations

- **Never commit your API token** to version control
- Store tokens securely using the setup wizard (encrypted) or `SHEEP_API_TOKEN`
- Use restrictive permissions for config files:
  ```bash
  chmod 600 ~/.sheep-ask-cli/config.ini
  ```
- Session token cache lives in `/tmp/sheep-ask-cli-sess-<uid>-<sid>` with mode `0600` and is bound to your current shell's Session ID. Run `--logout` to clear it early.

## Donation Support

This tool is maintained through community support. Help keep it active:

[![Donate](https://img.shields.io/badge/Support-Development-blue?style=for-the-badge&logo=github)](https://buy.byfranke.com/b/8wM03kb3u7THeIgaEE)
