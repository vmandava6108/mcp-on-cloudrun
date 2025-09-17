import logging
import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Load environment variables from .env if present
load_dotenv()

# System instructions specialized for GKE
SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for Google Kubernetes Engine (GKE). "
    "Your purpose is to use the provided MCP tools to help with GKE clusters, logs, "
    "recommendations, and manifests. "
    "You can:\n"
    "  - List GKE clusters (list_clusters)\n"
    "  - Get details about a specific cluster (get_cluster)\n"
    "  - Create optimized clusters (cluster_toolkit)\n"
    "  - Generate AI/ML manifests (giq_generate_manifest)\n"
    "  - Query GCP logs (query_logs)\n"
    "  - List recommendations (list_recommendations)\n"
    "  - Get log schemas (get_log_schema)\n\n"
    "If the user asks something unrelated to GKE, politely state you can only help "
    "with GKE clusters, logs, recommendations, or manifests."
)

logger.info("--- 🔧 Loading MCP tools from MCP Server... ---")

# Create ADK agent connected to your MCP server
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="gke_agent",
    description="An agent that helps manage and monitor GKE clusters",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
            )
        )
    ],
)

logger.info("✅ GKE Agent initialized and ready.")
