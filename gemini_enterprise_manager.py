#!/usr/bin/env python3
"""
Gemini Enterprise Manager for Google Maps MCP Agent

This script manages Gemini Enterprise operations including registration, updates,
and deletion of agents in Gemini Enterprise.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import google.auth
import requests
import typer
from dotenv import load_dotenv
from google.auth.transport import requests as google_requests
from typing_extensions import Annotated

app = typer.Typer(
    add_completion=False,
    help="Manage Gemini Enterprise operations for the Google Maps MCP Agent.",
)

DISCOVERY_ENGINE_API_BASE = "https://discoveryengine.googleapis.com/v1alpha"


class GeminiEnterpriseManager:
    """Manages AgentSpace configuration and operations."""

    def __init__(self, env_file: Path):
        """
        Initialize the Gemini Enterprise manager.

        Args:
            env_file: Path to the environment file.
        """
        self.env_file = env_file
        self.env_vars = self._load_env_vars()
        self.creds, self.project = google.auth.default()

    def _load_env_vars(self) -> Dict[str, str]:
        """Load environment variables from the .env file using python-dotenv."""
        if self.env_file.exists():
            load_dotenv(self.env_file, override=True)
        env_vars = dict(os.environ)
        return env_vars

    def _update_env_var(self, key: str, value: str) -> None:
        """Update an environment variable in the .env file."""
        if not self.env_file.exists():
            self.env_file.touch()

        lines = []
        if self.env_file.exists():
            with open(self.env_file, "r") as f:
                lines = f.readlines()

        # Find existing key or add new one
        key_found = False
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith("#") and "=" in line:
                existing_key = line.split("=", 1)[0].strip()
                if existing_key == key:
                    lines[i] = f"{key}={value}\n"
                    key_found = True
                    break

        if not key_found:
            lines.append(f"{key}={value}\n")

        with open(self.env_file, "w") as f:
            f.writelines(lines)

        # Update in-memory env_vars
        self.env_vars[key] = value

    def _get_access_token(self) -> Optional[str]:
        """Get Google Cloud access token."""
        if not self.creds.valid:
            self.creds.refresh(google_requests.Request())
        return self.creds.token

    def _validate_environment(self) -> Tuple[bool, list]:
        """Validate required environment variables for Gemini Enterprise operations."""
        required_vars = [
            "GOOGLE_CLOUD_PROJECT",
            "GCP_PROJECT_NUMBER",
            "AGENTSPACE_APP_ID",
            "AGENT_ENGINE_RESOURCE_NAME",
            "GOOGLE_CLOUD_LOCATION",
        ]
        missing = [var for var in required_vars if not self.env_vars.get(var)]
        return not missing, missing

    def _make_request(
        self, method: str, url: str, **kwargs: Any
    ) -> Optional[requests.Response]:
        """Make an authenticated request to the Discovery Engine API."""
        access_token = self._get_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": self.env_vars["GCP_PROJECT_NUMBER"],
        }
        headers.update(kwargs.pop("headers", {}))

        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            typer.secho(f" API request failed: {e}", fg=typer.colors.RED)
            if e.response is not None:
                typer.echo(f"  Response: {e.response.text}")
            return None

    def _get_agent_api_url(self, agent_id: Optional[str] = None) -> str:
        """Construct the API URL for Gemini Enterprise agents."""
        project_number = self.env_vars["GCP_PROJECT_NUMBER"]
        app_id = self.env_vars["AGENTSPACE_APP_ID"]
        collection = self.env_vars.get("AGENTSPACE_COLLECTION", "default_collection")
        assistant = self.env_vars.get("AGENTSPACE_ASSISTANT", "default_assistant")

        url = (
            f"{DISCOVERY_ENGINE_API_BASE}/projects/{project_number}/"
            f"locations/global/collections/{collection}/engines/{app_id}/"
            f"assistants/{assistant}/agents"
        )
        if agent_id:
            url += f"/{agent_id}"
        return url

    def _build_agent_config(self) -> Dict[str, Any]:
        """Build the agent configuration payload."""
        config = {
            "displayName": self.env_vars.get(
                "AGENT_DISPLAY_NAME", "Google Maps MCP Agent"
            ),
            "description": self.env_vars.get(
                "AGENT_DESCRIPTION",
                "AI-powered assistant for Google Maps location search, directions, and geocoding",
            ),
            "adk_agent_definition": {
                "tool_settings": {
                    "tool_description": self.env_vars.get(
                        "AGENT_TOOL_DESCRIPTION",
                        "Google Maps tools for location search, directions, and address lookup",
                    )
                },
                "provisioned_reasoning_engine": {
                    "reasoning_engine": self.env_vars["AGENT_ENGINE_RESOURCE_NAME"]
                },
            },
        }
        if oauth_auth_id := self.env_vars.get("OAUTH_AUTH_ID"):
            config["adk_agent_definition"]["authorizations"] = [
                f"projects/{self.env_vars['GCP_PROJECT_NUMBER']}/locations/global/authorizations/{oauth_auth_id}"
            ]
        else:
            config["adk_agent_definition"]["authorizations"] = []
        return config

    def link_agent(
        self,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tool_description: Optional[str] = None,
    ) -> bool:
        """Link an existing agent engine to Gemini Enterprise."""
        typer.echo("🔗 Linking agent to AgentSpace...")
        valid, missing = self._validate_environment()
        if not valid:
            typer.secho(
                f" Missing required variables: {', '.join(missing)}",
                fg=typer.colors.RED,
            )
            return False

        # Check if already linked
        if self.env_vars.get("AGENTSPACE_AGENT_ID"):
            typer.secho(
                " Agent already linked. Use unlink first to re-link.",
                fg=typer.colors.YELLOW,
            )
            return False

        # Override config if provided
        if display_name:
            self.env_vars["AGENT_DISPLAY_NAME"] = display_name
        if description:
            self.env_vars["AGENT_DESCRIPTION"] = description
        if tool_description:
            self.env_vars["AGENT_TOOL_DESCRIPTION"] = tool_description

        api_url = self._get_agent_api_url()
        agent_config = self._build_agent_config()

        response = self._make_request("POST", api_url, json=agent_config)
        if response and response.status_code == 200:
            result = response.json()
            agent_name = result.get("name", "")
            agent_id = agent_name.split("/")[-1] if agent_name else ""

            typer.secho(" Agent linked successfully!", fg=typer.colors.GREEN)
            typer.echo(f"  Agent Name: {agent_name}")
            typer.echo(f"  Agent ID: {agent_id}")

            if agent_id:
                self._update_env_var("AGENTSPACE_AGENT_ID", agent_id)
                typer.echo("  Saved AGENTSPACE_AGENT_ID to .env")
            return True
        return False

    def unlink_agent(self, force: bool = False) -> bool:
        """Unlink agent from Gemini Enterprise."""
        agent_id = self.env_vars.get("AGENTSPACE_AGENT_ID")
        if not agent_id:
            typer.secho(" No agent linked.", fg=typer.colors.YELLOW)
            return True

        if not force and not typer.confirm(
            f"Are you sure you want to unlink agent {agent_id}?"
        ):
            typer.echo("Cancelled.")
            return False

        api_url = self._get_agent_api_url(agent_id)
        response = self._make_request("DELETE", api_url)

        if response and response.status_code in [200, 204]:
            typer.secho(" Agent unlinked successfully!", fg=typer.colors.GREEN)
            self._update_env_var("AGENTSPACE_AGENT_ID", "")
            return True
        return False

    def verify_agent(self) -> bool:
        """Verify Gemini Enterprise agent configuration."""
        typer.echo("🔍 Verifying Gemini Enterprise configuration...")
        valid, missing = self._validate_environment()
        if not valid:
            typer.secho(
                f" Missing required variables: {', '.join(missing)}",
                fg=typer.colors.RED,
            )
            return False

        agent_id = self.env_vars.get("AGENTSPACE_AGENT_ID")
        if not agent_id:
            typer.secho(" No agent linked yet.", fg=typer.colors.YELLOW)
            return False

        api_url = self._get_agent_api_url(agent_id)
        response = self._make_request("GET", api_url)

        if response and response.status_code == 200:
            result = response.json()
            typer.secho(" Agent verified successfully!", fg=typer.colors.GREEN)
            typer.echo(f"  Display Name: {result.get('displayName', 'N/A')}")
            typer.echo(f"  Description: {result.get('description', 'N/A')}")
            return True
        return False

    def display_url(self) -> None:
        """Display Gemini Enterprise UI URL."""
        project_id = self.env_vars.get("GOOGLE_CLOUD_PROJECT")
        app_id = self.env_vars.get("AGENTSPACE_APP_ID")

        if not all([project_id, app_id]):
            typer.secho(
                " Cannot generate URL - missing configuration.", fg=typer.colors.RED
            )
            return

        url = f"https://console.cloud.google.com/gen-ai-studio/agentspace/apps/{app_id}?project={project_id}"
        typer.echo("\n📱 Gemini Enterprise UI URL:")
        typer.echo("=" * 80)
        typer.echo(url)
        typer.echo("=" * 80)


@app.command()
def link(
    display_name: Annotated[
        Optional[str],
        typer.Option("--display-name", help="Display name for the agent."),
    ] = None,
    description: Annotated[
        Optional[str], typer.Option("--description", help="Description of the agent.")
    ] = None,
    tool_description: Annotated[
        Optional[str], typer.Option("--tool-description", help="Tool description.")
    ] = None,
    env_file: Annotated[
        Path, typer.Option(help="Path to the environment file.")
    ] = Path(".env"),
) -> None:
    """Link the agent to Gemini Enterprise."""
    manager = GeminiEnterpriseManager(env_file)
    if not manager.link_agent(display_name, description, tool_description):
        raise typer.Exit(code=1)


@app.command()
def unlink(
    force: Annotated[
        bool, typer.Option("--force", help="Force unlinking without confirmation.")
    ] = False,
    env_file: Annotated[
        Path, typer.Option(help="Path to the environment file.")
    ] = Path(".env"),
) -> None:
    """Unlink the agent from Gemini Enterprise."""
    manager = GeminiEnterpriseManager(env_file)
    if not manager.unlink_agent(force):
        raise typer.Exit(code=1)


@app.command()
def verify(
    env_file: Annotated[
        Path, typer.Option(help="Path to the environment file.")
    ] = Path(".env"),
) -> None:
    """Verify the Gemini Enterprise agent configuration."""
    manager = GeminiEnterpriseManager(env_file)
    if not manager.verify_agent():
        raise typer.Exit(code=1)


@app.command()
def url(
    env_file: Annotated[
        Path, typer.Option(help="Path to the environment file.")
    ] = Path(".env"),
) -> None:
    """Display the Gemini Enterprise UI URL."""
    manager = GeminiEnterpriseManager(env_file)
    manager.display_url()


if __name__ == "__main__":
    app()
