"""Deployment script for Google Maps MCP Agent."""

import os
import sys

import vertexai
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

from google_maps_mcp_agent.agent import root_agent

load_dotenv()

# Configuration
GCP_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
GCP_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")
GCP_STAGING_BUCKET = os.environ.get("GOOGLE_CLOUD_STORAGE_BUCKET")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

if not all([GCP_PROJECT_ID, GCP_LOCATION, GCP_STAGING_BUCKET, GOOGLE_MAPS_API_KEY]):
    print("ERROR: Missing required environment variables")
    print(f"GOOGLE_CLOUD_PROJECT: {GCP_PROJECT_ID}")
    print(f"GOOGLE_CLOUD_LOCATION: {GCP_LOCATION}")
    print(f"GOOGLE_CLOUD_STORAGE_BUCKET: {GCP_STAGING_BUCKET}")
    print(f"GOOGLE_MAPS_API_KEY: {'***' if GOOGLE_MAPS_API_KEY else 'NOT SET'}")
    sys.exit(1)

print("🚀 Deploying Google Maps MCP Agent")
print(f"PROJECT: {GCP_PROJECT_ID}")
print(f"LOCATION: {GCP_LOCATION}")
print(f"BUCKET: gs://{GCP_STAGING_BUCKET}")
print("=" * 60)

# Initialize Vertex AI
vertexai.init(
    project=GCP_PROJECT_ID,
    location=GCP_LOCATION,
    staging_bucket=f"gs://{GCP_STAGING_BUCKET}",
)

# Create AdkApp
app = AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

# 設定 extra_packages 和 build_options
extra_packages = [
    "./google_maps_mcp_agent",
    "installation_scripts/install_npx.sh",
]

build_options = {"installation_scripts": ["installation_scripts/install_npx.sh"]}

# 設定運行時環境變數
env_vars = {
    "GOOGLE_MAPS_API_KEY": GOOGLE_MAPS_API_KEY,
    "MODEL": os.getenv("MODEL", "gemini-2.5-flash"),
}

# Deploy using FIXED versions
print("\n📦 Creating agent with MCP toolset...")
remote_app = agent_engines.create(
    app,
    display_name="Google Maps MCP Agent",
    requirements=[
        "cloudpickle",
        "google-adk>=1.15.1",
        "google-genai",
        "google-cloud-aiplatform[agent-engines]==1.119.0",  # FIXED version
        "pydantic",
        "python-dotenv",
    ],
    extra_packages=extra_packages,
    build_options=build_options,
    env_vars=env_vars,
)

# Test if requested
if "--test" in sys.argv:
    import asyncio

    async def async_test(remote_app):
        user_id = "test_user"
        session = await remote_app.async_create_session(user_id=user_id)
        print(f"Session: {session.get('id')}")

        test_query = "我要拜訪客戶沃司科技，我是思想科技台北出發，客戶是在No. 655號, Bannan Rd, Zhonghe District, New Taipei City, 235"

        print(f"\nQuery: {test_query}\n")
        print("=" * 80)

        events = []
        async for event in remote_app.async_stream_query(
            user_id=user_id,
            session_id=session.get("id"),
            message=test_query,
        ):
            print(f"Event: {event}")
            events.append(event)

        print("=" * 80)
        print(f"\nReceived {len(events)} events")

    asyncio.run(async_test(remote_app))

# Delete if requested
if "--delete" in sys.argv:
    print("\nDeleting agent...")
    remote_app.delete(force=True)
    print("✅ Agent deleted successfully")
else:
    print(f"\n✅ Agent deployed: {remote_app.resource_name}")
    print(f"\nResource ID: {remote_app.resource_name.split('/')[-1]}")

    print("\n" + "=" * 80)
    print("📋 NEXT STEPS:")
    print("=" * 80)
    print("\n1. Update your .env file with:")
    print(f"   AGENT_ENGINE_RESOURCE_NAME={remote_app.resource_name}")

    print("\n2. Link agent to AgentSpace:")
    print("   python agentspace_manager.py link")

    print("\n3. Verify AgentSpace integration:")
    print("   python agentspace_manager.py verify")

    print("\n4. Get AgentSpace UI URL:")
    print("   python agentspace_manager.py url")

    print("\n5. Test the agent:")
    print("   python query_agent_engine.py")
    print("=" * 80)
