#!/usr/bin/env python3
"""
Sheep Ask CLI: AI Query Tool
Copyright (c) 2026 byFranke - Security Solutions
GitHub: https://github.com/byfranke/sheep-ask-cli

A command-line interface for sending AI queries to sheep.byfranke.com,
focused on Cyber Threat Intelligence and general security questions.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
import configparser
from getpass import getpass
import base64

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import keyring
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

_VERSION_FILE = Path(__file__).parent / "VERSION"
VERSION = _VERSION_FILE.read_text().strip() if _VERSION_FILE.exists() else "1.0.0"
DEFAULT_API_URL = "https://sheep.byfranke.com/api/ai/ask"
DEFAULT_CONFIG_FILE = "~/.sheep-ask-cli/config.ini"
INSTALL_DIR = Path.home() / ".sheep-ask-cli"
DEFAULT_TIMEOUT = 60
GITHUB_REPO = "https://github.com/byfranke/sheep-ask-cli"
PRIVACY_POLICY = "https://sheep.byfranke.com/pages/privacy.html"
SUPPORT_EMAIL = "support@byfranke.com"

CHUNK_WORDS = 500
CONTEXT_CHAR_LIMIT = 2000

console = Console()


class SheepAskClient:
    """Client for the Sheep AI Ask API."""

    def __init__(self, api_token: Optional[str] = None, api_url: Optional[str] = None):
        self.api_token = api_token or self._load_token()
        self.api_url = api_url or DEFAULT_API_URL

        if not self.api_token:
            raise ValueError(
                "API token is required. Configure it via:\n"
                "  1. Run: python3 setup.py to configure encrypted token\n"
                "  2. Use --token argument for one-time use\n"
                "  3. Set SHEEP_API_TOKEN environment variable\n\n"
                "To reinstall: curl -fsSL https://byfranke.com/ask-cli-install | bash\n"
                f"Support: {SUPPORT_EMAIL}\n"
                f"Documentation: {GITHUB_REPO}"
            )

    def _session_cache_path(self) -> Optional[Path]:
        """Path for the per-terminal-session decrypted token cache."""
        try:
            sid = os.getsid(os.getpid())
        except (AttributeError, OSError):
            return None
        uid = os.getuid() if hasattr(os, "getuid") else 0
        return Path(f"/tmp/sheep-ask-cli-sess-{uid}-{sid}")

    def _read_session_cache(self) -> Optional[str]:
        cache = self._session_cache_path()
        if cache is None or not cache.exists():
            return None
        try:
            st = cache.stat()
            if hasattr(os, "getuid") and st.st_uid != os.getuid():
                return None
            if st.st_mode & 0o077:
                return None
            token = cache.read_text().strip()
            return token or None
        except Exception:
            return None

    def _write_session_cache(self, token: str) -> None:
        cache = self._session_cache_path()
        if cache is None:
            return
        try:
            fd = os.open(str(cache), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(token)
        except Exception:
            pass

    def _decrypt_token(self, encrypted_token: str, password: str) -> Optional[str]:
        if not ENCRYPTION_AVAILABLE:
            console.print("[yellow]Warning: Encryption libraries not available[/yellow]")
            return None
        try:
            salt = b'sheep-ask-cli-salt-2026'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            f = Fernet(key)
            encrypted = base64.b64decode(encrypted_token.encode())
            decrypted = f.decrypt(encrypted)
            return decrypted.decode()
        except Exception:
            return None

    def _load_token(self) -> Optional[str]:
        """Load API token from env, keyring, or config file."""
        token = os.environ.get("SHEEP_API_TOKEN")
        if token:
            return token

        if ENCRYPTION_AVAILABLE:
            try:
                token = keyring.get_password("sheep-ask-cli", "api_token")
                if token:
                    return token
            except Exception:
                pass

        config_path = Path(DEFAULT_CONFIG_FILE).expanduser()
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(config_path)

            if "api" in config:
                if config["api"].get("encryption_enabled") == "true" and "encrypted_token" in config["api"]:
                    cached = self._read_session_cache()
                    if cached:
                        return cached

                    encrypted_token = config["api"]["encrypted_token"]
                    console.print("[yellow]Token is encrypted. Enter your master password:[/yellow]")

                    for attempt in range(3):
                        password = getpass("Master Password: ")
                        token = self._decrypt_token(encrypted_token, password)
                        if token:
                            self._write_session_cache(token)
                            return token
                        console.print(f"[red]Invalid password. {2 - attempt} attempts remaining.[/red]")

                    console.print("[red]Failed to decrypt token after 3 attempts[/red]")
                    return None

                if "token" in config["api"]:
                    return config["api"]["token"]

        return None

    def ask(self, question: str) -> Dict[str, Any]:
        """Send a question to the Sheep AI API."""
        headers = {
            "X-API-Token": self.api_token,
            "Content-Type": "application/json",
        }
        payload = {"question": question}

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task("Sheep is thinking...", total=None)
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=DEFAULT_TIMEOUT,
                )
        except requests.exceptions.Timeout:
            console.print("[red]Error: Request timed out[/red]")
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            console.print("[red]Error: Failed to connect to API server[/red]")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            sys.exit(1)

        if response.status_code == 401:
            console.print("[red]Error: Invalid API token[/red]")
            sys.exit(1)
        if response.status_code == 422:
            console.print("[red]Error: Request too large or invalid format[/red]")
            console.print("[yellow]Try a shorter question or smaller context file[/yellow]")
            sys.exit(1)
        if response.status_code == 429:
            console.print("[red]Error: Rate limit exceeded. Please wait before trying again[/red]")
            sys.exit(1)
        if response.status_code != 200:
            console.print(f"[red]Error: API returned status {response.status_code}[/red]")
            sys.exit(1)

        try:
            return response.json()
        except ValueError:
            console.print("[red]Error: Invalid API response[/red]")
            sys.exit(1)

    def _summarize_chunk(self, chunk: str) -> str:
        """Ask the API to summarize a single chunk. Returns '' on failure."""
        question = f"Summarize key points: {chunk[:1500]}"
        headers = {"X-API-Token": self.api_token, "Content-Type": "application/json"}
        try:
            resp = requests.post(
                self.api_url,
                headers=headers,
                json={"question": question},
                timeout=DEFAULT_TIMEOUT,
            )
            if resp.status_code != 200:
                return ""
            data = resp.json()
            if data.get("success"):
                return data.get("response", "") or ""
        except (requests.exceptions.RequestException, ValueError):
            pass
        return ""

    def build_context_from_file(self, file_path: str) -> Optional[str]:
        """
        Read a file and return it as context. Mirrors bash sheep-ask behavior:
        - Files <= CHUNK_WORDS words are returned as-is (final truncate to
          CONTEXT_CHAR_LIMIT still applies).
        - Larger files are split into CHUNK_WORDS-word chunks, each summarized
          by the API, and the consolidated summary is returned.
        """
        path = Path(file_path)
        if not path.is_file():
            console.print(f"[red]Error: File '{file_path}' not found[/red]")
            sys.exit(1)

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            sys.exit(1)

        words: List[str] = content.split()
        total_words = len(words)
        console.print(f"[cyan]Processing context from:[/cyan] {file_path} ({total_words} words)")

        if total_words <= CHUNK_WORDS:
            console.print("[dim]Processing file in single pass...[/dim]")
            context = content
        else:
            console.print("[yellow]File is large, processing in chunks...[/yellow]")
            chunks = [
                " ".join(words[i:i + CHUNK_WORDS])
                for i in range(0, total_words, CHUNK_WORDS)
            ]
            summaries: List[str] = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Summarizing chunks...", total=len(chunks))
                for idx, chunk in enumerate(chunks, start=1):
                    progress.update(task, description=f"Summarizing chunk {idx}/{len(chunks)}...")
                    summary = self._summarize_chunk(chunk)
                    if summary:
                        summaries.append(summary)
                    progress.advance(task)
                    if idx < len(chunks):
                        time.sleep(1)
            context = "\n\n".join(summaries).strip()

        if len(context) > CONTEXT_CHAR_LIMIT:
            context = context[:CONTEXT_CHAR_LIMIT] + "...[truncated]"
        return context


def save_response_to_markdown(response_text: str, question: str) -> str:
    """Save the AI response to a timestamped markdown file in CWD."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sheep_answers_{timestamp}.md"
    content = (
        f"# Sheep Ask Response\n\n"
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"**Question:** {question}\n\n"
        f"---\n\n"
        f"{response_text}\n"
    )
    Path(filename).write_text(content, encoding="utf-8")
    return filename


def display_response(result: Dict[str, Any], output_format: str = "pretty") -> Optional[str]:
    """Display the API response. Returns the response text on success."""
    if not result.get("success"):
        error = result.get("error", "Unknown error")
        if output_format == "json":
            console.print_json(json.dumps(result, indent=2))
        else:
            console.print(Panel(f"[red]{error}[/red]", title="Error", border_style="red"))
        return None

    answer = result.get("response", "")

    if output_format == "json":
        console.print_json(json.dumps(result, indent=2))
    elif output_format == "plain":
        print(answer)
    elif output_format == "markdown":
        console.print(Markdown(answer))
    else:  # pretty
        try:
            console.print(Panel(
                Markdown(answer),
                title="Sheep AI Response",
                border_style="green",
            ))
        except Exception:
            console.print(Panel(answer, title="Sheep AI Response", border_style="green"))

    return answer


def init_config():
    """Initialize an empty configuration file with placeholders."""
    config_dir = Path(DEFAULT_CONFIG_FILE).expanduser().parent
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = Path(DEFAULT_CONFIG_FILE).expanduser()

    if config_path.exists():
        console.print(f"[yellow]Configuration file already exists at {config_path}[/yellow]")
        overwrite = console.input("Do you want to overwrite it? (y/N): ")
        if overwrite.lower() != "y":
            return

    config = configparser.ConfigParser()
    config["api"] = {"token": "YOUR_API_TOKEN_HERE", "url": DEFAULT_API_URL}
    config["defaults"] = {"output_format": "pretty"}

    with open(config_path, "w") as f:
        config.write(f)
    try:
        os.chmod(config_path, 0o600)
    except Exception:
        pass

    console.print(f"[green]Configuration file created at {config_path}[/green]")
    console.print("[yellow]Please edit the file and add your API token, or run setup.py[/yellow]")


def check_for_updates():
    console.print("[bold cyan]Checking for updates...[/bold cyan]")
    console.print(f"Current version: {VERSION}")

    if not GIT_AVAILABLE:
        console.print("[yellow]Git module not available - check manually[/yellow]")
        console.print(f"\nFor updates, visit: {GITHUB_REPO}")
        console.print("To reinstall: [cyan]curl -fsSL https://byfranke.com/ask-cli-install | bash[/cyan]")
        return

    if not (INSTALL_DIR / ".git").exists():
        console.print(f"[yellow]Git repository not found at {INSTALL_DIR}[/yellow]")
        console.print("To reinstall: [cyan]curl -fsSL https://byfranke.com/ask-cli-install | bash[/cyan]")
        return

    try:
        console.print("Pulling latest updates...")
        repo = git.Repo(INSTALL_DIR)
        repo.remotes.origin.pull()
        console.print("[green][OK][/green] Repository updated")

        version_file = INSTALL_DIR / "VERSION"
        if version_file.exists():
            new_version = version_file.read_text().strip()
            if new_version != VERSION:
                console.print(f"[green]Updated to version {new_version} (was {VERSION})[/green]")
                console.print("[yellow]Upgrading dependencies...[/yellow]")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r",
                     str(INSTALL_DIR / "requirements.txt"), "--user", "--upgrade"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    console.print("[green][OK][/green] Dependencies upgraded")
                else:
                    console.print("[yellow]Could not upgrade dependencies automatically[/yellow]")
                    console.print(f"Run manually: pip install -r {INSTALL_DIR}/requirements.txt --upgrade")
            else:
                console.print(f"[green][OK][/green] Already at latest version ({VERSION})")
    except Exception as e:
        console.print(f"[yellow]Could not check for updates: {e}[/yellow]")
        console.print(f"\nFor updates, visit: {GITHUB_REPO}")


def main():
    parser = argparse.ArgumentParser(
        description="AI query tool for Cyber Threat Intelligence via sheep.byfranke.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s "What is ransomware?"
  %(prog)s "What are the TTPs of APT29?" -o
  %(prog)s -p report.md "Summarize the key findings"
  %(prog)s --prompt incident.md "What are the IOCs mentioned?"

Setup & Configuration:
  python3 setup.py                 # Run interactive setup wizard
  %(prog)s --init                  # Quick config file creation
  %(prog)s --update                # Check for updates (uses git pull)
  %(prog)s --logout                # Clear cached token for this terminal

Install / Reinstall:
  curl -fsSL https://byfranke.com/ask-cli-install | bash

Support:
  Documentation: {GITHUB_REPO}
  Privacy Policy: {PRIVACY_POLICY}
  Email: {SUPPORT_EMAIL}

Copyright (c) 2026 byFranke - Security Solutions
        """,
    )

    parser.add_argument("question", nargs="*", help="The question to ask the AI")
    parser.add_argument("-p", "--prompt", metavar="FILE",
                        help="Markdown file to use as context before the question")
    parser.add_argument("-o", "--output-file", action="store_true",
                        help="Save the AI response to a timestamped markdown file")
    parser.add_argument("--token", help="API authentication token (one-time use)")
    parser.add_argument("--api-url", help=f"API endpoint URL (default: {DEFAULT_API_URL})")
    parser.add_argument("--format", choices=["pretty", "json", "markdown", "plain"],
                        default="pretty", help="Output format (default: pretty)")
    parser.add_argument("--init", action="store_true", help="Initialize configuration file")
    parser.add_argument("--update", action="store_true", help="Check for updates from GitHub")
    parser.add_argument("--setup", action="store_true", help="Run interactive setup wizard")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--about", action="store_true", help="Show about information")
    parser.add_argument("--logout", action="store_true",
                        help="Clear the cached decrypted token for the current terminal session")

    args = parser.parse_args()

    if args.about:
        about_info = f"""
[bold cyan]Sheep Ask CLI v{VERSION}[/bold cyan]
AI Query Tool for Cyber Threat Intelligence

[bold]Copyright:[/bold] (c) 2026 byFranke - Security Solutions
[bold]License:[/bold] byFranke License
[bold]GitHub:[/bold] {GITHUB_REPO}
[bold]Privacy Policy:[/bold] {PRIVACY_POLICY}
[bold]Support:[/bold] {SUPPORT_EMAIL}

[bold]Features:[/bold]
- Ask AI questions from the terminal
- Use markdown files as context
- Save responses as timestamped markdown files
- Encrypted token storage with per-session cache
        """
        console.print(Panel(about_info, title="About Sheep Ask CLI", style="cyan"))
        return

    if args.logout:
        try:
            client = SheepAskClient.__new__(SheepAskClient)
            cache = client._session_cache_path()
            if cache and cache.exists():
                cache.unlink()
                console.print("[green]Session token cache cleared[/green]")
            else:
                console.print("[yellow]No cached session token to clear[/yellow]")
        except Exception as e:
            console.print(f"[red]Failed to clear session cache: {e}[/red]")
        return

    if args.setup:
        console.print("[cyan]Launching setup wizard...[/cyan]")
        script_dir = Path(__file__).resolve().parent
        os.system(f"{sys.executable} {script_dir / 'setup.py'}")
        return

    if args.update:
        check_for_updates()
        return

    if args.init:
        init_config()
        return

    question = " ".join(args.question).strip()
    if not question:
        parser.error("Question is required (use --help for options)")

    try:
        client = SheepAskClient(api_token=args.token, api_url=args.api_url)

        if args.prompt:
            context = client.build_context_from_file(args.prompt)
            if context:
                question = f"Context: {context}\n\nQuestion: {question}"

        result = client.ask(question)
        answer = display_response(result, args.format)

        if answer and args.output_file:
            filename = save_response_to_markdown(answer, question)
            console.print(f"\n[green]Response saved to:[/green] {filename}")

    except ValueError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        if args.verbose:
            console.print_exception()
        else:
            console.print(f"[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
