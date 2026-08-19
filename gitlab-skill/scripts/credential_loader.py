#!/usr/bin/env python3
"""
GitLab Credential Loader Module

Provides secure, layered credential management for GitLab API access.
Credentials are loaded in priority order:
1. Environment Variables (GITLAB_HOST, GITLAB_TOKEN) - Most Secure
2. User Config File (~/.veles/gitlab_config.json)
3. Legacy Config (scripts/config.json - deprecated)
4. Runtime Prompt (optional, requires --allow-prompt)
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


class CredentialManager:
    """Manages GitLab credential loading with priority-based fallback"""

    USER_CONFIG_PATH = Path.home() / ".veles" / "gitlab_config.json"
    LEGACY_CONFIG_PATH = Path(__file__).parent / "config.json"

    def __init__(self, allow_prompt: bool = False):
        """Initialize credential manager

        Args:
            allow_prompt: If True, allow interactive credential prompting as fallback
        """
        self.allow_prompt = allow_prompt
        self._credentials: Dict[str, str] = {}
        self._credential_source: Optional[str] = None

    def load_credentials(self) -> Dict[str, str]:
        """Load credentials using priority-based fallback chain

        Returns:
            Dict with 'host' and 'access_token' keys

        Raises:
            SystemExit: If no valid credentials found
        """
        if self._try_layered_sources():
            return self._credentials

        # Fallback to runtime prompt if allowed
        if self.allow_prompt:
            return self._prompt_credentials()

        # No credentials found
        self._print_setup_guide()
        sys.exit(1)

    def get_credential_source(self) -> str:
        """Return the source of loaded credentials for debugging

        Returns:
            String describing where credentials were loaded from
        """
        return self._credential_source or "unknown"

    def _try_layered_sources(self) -> bool:
        """Try loading host and token from the supported layered sources.

        Returns:
            True if a valid host and token pair was found.
        """
        host, host_source = self._load_host()
        token, token_source = self._load_token()

        if not host or not token:
            return False

        if not self._is_valid_token(token):
            print(f"⚠️  Warning: GitLab token from {token_source} appears to be a placeholder")
            return False

        self._credentials = {
            "host": host.rstrip("/"),
            "access_token": token
        }
        self._credential_source = self._format_source(host_source, token_source)
        return True

    def _load_host(self) -> Tuple[Optional[str], Optional[str]]:
        """Load GitLab host from ordinary configuration sources."""
        env_host = os.getenv("GITLAB_HOST")
        if env_host:
            return env_host.rstrip("/"), "environment_variables"

        user_config = self._read_user_config()
        user_host = user_config.get("host", "").strip().rstrip("/")
        if user_host:
            return user_host, "user_config_file"

        legacy_config = self._read_legacy_config()
        legacy_host = legacy_config.get("host", "").strip().rstrip("/")
        if legacy_host:
            self._warn_legacy_config()
            return legacy_host, "legacy_config_file"

        return None, None

    def _load_token(self) -> Tuple[Optional[str], Optional[str]]:
        """Load GitLab token, preferring secret-backed environment injection."""
        env_token = os.getenv("GITLAB_TOKEN")
        if env_token:
            return env_token, "environment_variables"

        user_config = self._read_user_config()
        user_token = user_config.get("access_token", "")
        if user_token:
            return user_token, "user_config_file"

        legacy_config = self._read_legacy_config()
        legacy_token = legacy_config.get("access_token", "")
        if legacy_token:
            self._warn_legacy_config()
            return legacy_token, "legacy_config_file"

        return None, None

    def _read_user_config(self) -> Dict[str, str]:
        """Read ~/.veles/gitlab_config.json if present."""
        if not self.USER_CONFIG_PATH.exists():
            return {}

        try:
            with open(self.USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: Failed to read user config: {e}")
            return {}

    def _read_legacy_config(self) -> Dict[str, str]:
        """Read deprecated skill-local config if present."""
        if not self.LEGACY_CONFIG_PATH.exists():
            return {}

        try:
            with open(self.LEGACY_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _warn_legacy_config(self) -> None:
        """Show deprecation warning for the skill-local config once."""
        if getattr(self, "_legacy_warning_shown", False):
            return

        self._legacy_warning_shown = True

        print("⚠️  Warning: Using deprecated config.json in skill directory")
        print("   Please migrate GITLAB_TOKEN to Veles secrets/environment variables")
        print("   and keep only ordinary host configuration in:")
        print(f"   {self.USER_CONFIG_PATH}")
        print("   See SKILL.md for migration instructions\n")

    def _format_source(self, host_source: Optional[str], token_source: Optional[str]) -> str:
        """Return a compact source description for diagnostics."""
        if host_source == token_source:
            return host_source or "unknown"
        return f"host:{host_source or 'unknown'}, token:{token_source or 'unknown'}"

    def _is_valid_token(self, token: str) -> bool:
        """Check if token appears valid (not a placeholder)

        Args:
            token: The token to validate

        Returns:
            True if token appears to be valid, False if it's a placeholder
        """
        if not token or len(token) < 10:
            return False

        placeholder_patterns = [
            "在这里",  # Chinese "here"
            "your_token",
            "your_token_here",
            "placeholder",
            "enter_token",
            "glpat-xxxxxxxxxxxx",
            "your-token-here"
        ]

        token_lower = token.lower()
        return not any(pattern in token_lower for pattern in placeholder_patterns)

    def _prompt_credentials(self) -> Dict[str, str]:
        """Prompt user for credentials interactively

        Returns:
            Dict with 'host' and 'access_token' keys
        """
        print("GitLab credentials not found in environment or config files.")
        print("\nPlease enter your GitLab credentials:\n")

        try:
            host = input("GitLab Host URL (e.g., https://gitlab.example.com): ").strip()
            if not host:
                print("Error: Host URL is required")
                sys.exit(1)

            # Use getpass for token to avoid echoing to terminal
            import getpass
            token = getpass.getpass("Access Token (input will be hidden): ").strip()

            if not self._is_valid_token(token):
                print("Error: Invalid access token")
                sys.exit(1)

            # Ask if user wants to save credentials
            save = input("\nSave credentials to user config file for future use? [y/N]: ").strip().lower()

            if save == 'y':
                self._save_user_config(host)

            return {
                "host": host.rstrip("/"),
                "access_token": token
            }

        except (KeyboardInterrupt, EOFError):
            print("\n\nCancelled.")
            sys.exit(1)

    def _save_user_config(self, host: str) -> None:
        """Save ordinary GitLab host configuration to user config file.

        Args:
            host: GitLab host URL
        """
        # Create .veles directory if it doesn't exist
        self.USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write only non-secret host config. Tokens should come from Veles secrets
        # or other environment injection.
        config = {
            "host": host.rstrip("/")
        }

        with open(self.USER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Set restrictive permissions (read/write for owner only)
        self.USER_CONFIG_PATH.chmod(0o600)

        print(f"\n✅ GitLab host saved to: {self.USER_CONFIG_PATH}")
        print("   File permissions set to 600 (read/write for owner only)")
        print("   Store GITLAB_TOKEN in Veles secrets or environment variables")

    def _print_setup_guide(self) -> None:
        """Print helpful setup instructions when credentials not found"""
        print("❌ Error: GitLab credentials not configured\n")
        print("Please configure credentials using one of these methods:\n")

        print("1. Environment Variables (Recommended - Most Secure):")
        print("   export GITLAB_HOST='https://gitlab.example.com'")
        print("   export GITLAB_TOKEN='glpat-your-token-here'\n")

        print("2. User Config File + Secret-backed Token:")
        print(f"   Create {self.USER_CONFIG_PATH}")
        print("   With content: {\"host\": \"https://gitlab.example.com\"}")
        print("   Store the token as Veles secret skills.gitlab-skill.env.GITLAB_TOKEN\n")

        print("3. Runtime Prompt (Not recommended for automation):")
        print("   Pass --allow-prompt flag when running scripts\n")

        print("For more information, see the SKILL.md documentation")


def load_credentials(allow_prompt: bool = False) -> Tuple[str, str]:
    """Convenience function to load credentials

    Args:
        allow_prompt: If True, allow interactive credential prompting

    Returns:
        Tuple of (host, token)

    Example:
        >>> from credential_loader import load_credentials
        >>> host, token = load_credentials()
        >>> print(f"Connecting to {host}")
    """
    manager = CredentialManager(allow_prompt=allow_prompt)
    creds = manager.load_credentials()
    return creds["host"], creds["access_token"]


def get_user_config_path() -> Path:
    """Get the path to the user config file

    Returns:
        Path to ~/.veles/gitlab_config.json
    """
    return CredentialManager.USER_CONFIG_PATH


def create_user_config_template() -> None:
    """Create a template user config file for the user to fill in"""
    config_path = CredentialManager.USER_CONFIG_PATH

    # Create .veles directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Create template
    template = {
        "_comment": "GitLab host configuration. Store GITLAB_TOKEN in Veles secrets or environment variables.",
        "host": "https://gitlab.example.com"
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)

    # Set permissive permissions initially (user will edit)
    config_path.chmod(0o644)

    print(f"✅ Created template config at: {config_path}")
    print("   Please edit this file and set your GitLab host")
    print("   Store GITLAB_TOKEN in Veles secrets or environment variables")
    print("   Then run: chmod 600 " + str(config_path))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="GitLab Credential Loader - Manage GitLab API credentials"
    )
    parser.add_argument("--show-source", action="store_true",
                       help="Show which credential source is being used")
    parser.add_argument("--create-template", action="store_true",
                       help="Create a template user config file")
    parser.add_argument("--allow-prompt", action="store_true",
                       help="Allow interactive credential prompting")

    args = parser.parse_args()

    if args.create_template:
        create_user_config_template()
    else:
        manager = CredentialManager(allow_prompt=args.allow_prompt)
        creds = manager.load_credentials()
        source = manager.get_credential_source()

        print(f"✅ Credentials loaded from: {source}")
        print(f"   Host: {creds['host']}")
        print(f"   Token: {creds['access_token'][:10]}..." if len(creds['access_token']) > 10
              else f"   Token: {creds['access_token']}")
