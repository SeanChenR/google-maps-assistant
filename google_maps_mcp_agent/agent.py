import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")

if not google_maps_api_key:
    print(
        "WARNING: GOOGLE_MAPS_API_KEY is not set. Please set it as an environment variable or update it in the script."
    )

google_maps_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-google-maps",
            ],
            env={"GOOGLE_MAPS_API_KEY": google_maps_api_key},
        ),
        timeout=15,
    ),
    errlog=None
)

root_agent = Agent(
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    name="maps_assistant_agent",
    description="Google Maps assistant with MCP toolset for location search, directions, and geocoding.",
    instruction="""You are a Google Maps assistant with access to mapping and location tools.

YOUR CAPABILITIES:
- Search for places and locations
- Get directions between locations
- Geocode addresses to coordinates
- Find nearby points of interest

WORKFLOW:
1. When users ask about locations or directions, use the Google Maps MCP tools
2. Provide clear, actionable guidance with addresses and navigation instructions
3. Include relevant details like distance, travel time, and route information

Always provide helpful location information and navigation guidance.""",
    tools=[google_maps_tools]
)
