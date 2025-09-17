# mcp-on-cloudrun
gke mcp 

MCP Tools
cluster_toolkit: Creates AI optimized GKE Clusters.
list_clusters: List your GKE clusters.
get_cluster: Get detailed about a single GKE Cluster.
giq_generate_manifest: Generate a GKE manifest for AI/ML inference workloads using Google Inference Quickstart.
list_recommendations: List recommendations for your GKE clusters.
query_logs: Query Google Cloud Platform logs using Logging Query Language (LQL).
get_log_schema: Get the schema for a specific GKE log type.
MCP Context
In addition to the tools above, a lot of value is provided through the bundled context instructions.

Cost: The provided instructions allows the AI to answer many questions related to GKE costs, including queries related to clusters, namespaces, and Kubernetes workloads.

GKE Known Issues: The provided instructions allows the AI to fetch the latest GKE Known issues and check whether the cluster is affected by one of these known issues.

Supported MCP Transports
By default, gke-mcp uses the stdio transport. Additionally, the Streamable HTTP transport is supported as well.

You can set the transport mode using the following options:

--server-mode: transport to use for the server: stdio (default) or http

--server-port: server port to use when server-mode is http or sse; defaults to 8080

gke-mcp --server-mode http --server-port 8080
