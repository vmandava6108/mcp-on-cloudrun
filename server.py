import os
import logging
import asyncio
import signal
import subprocess

from fastmcp import FastMCP
from google.cloud import container_v1, logging_v2, recommender_v1
from kubernetes import client as k8s_client, config as k8s_config
import google.auth
import google.auth.transport.requests

# -----------------------
# Logging setup
# -----------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# -----------------------
# MCP server
# -----------------------
mcp = FastMCP("GKE MCP Server 🚀")

# -----------------------
# Helpers
# -----------------------

def get_project_id():
    return os.getenv("GOOGLE_CLOUD_PROJECT")

def get_location():
    return os.getenv("GOOGLE_CLOUD_LOCATION")

def get_access_token():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token

def get_k8s_client(cluster_name: str) -> k8s_client.CoreV1Api:
    """Get Kubernetes client by fetching cluster credentials via gcloud."""
    project_id = get_project_id()
    region = get_location()

    logger.info(f"Fetching kubeconfig for cluster {cluster_name} in {project_id}/{region}")
    try:
        subprocess.run([
            "gcloud", "container", "clusters", "get-credentials",
            cluster_name,
            "--project", project_id,
            "--region", region
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Load updated kubeconfig
        k8s_config.load_kube_config()
        return k8s_client.CoreV1Api()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get credentials for cluster {cluster_name}: {e.stderr.decode()}")
        raise

# -----------------------
# Tools (old functionality)
# -----------------------

@mcp.tool()
def cluster_toolkit(project_id: str, region: str, cluster_name: str):
    """Create AI-optimized GKE cluster."""
    logger.info(f"Creating cluster {cluster_name} in {project_id}/{region}")
    try:
        client = container_v1.ClusterManagerClient()
        parent = f"projects/{project_id}/locations/{region}"
        cluster = container_v1.Cluster(name=cluster_name, initial_node_count=1)
        op = client.create_cluster(parent=parent, cluster=cluster)
        return {"operation": op.name}
    except Exception as e:
        logger.error("Error in cluster_toolkit: %s", e)
        return {"error": str(e)}

@mcp.tool()
def list_clusters():
    """List all GKE clusters for the current project and location."""
    project_id = get_project_id()
    region = get_location()
    logger.info(f"Listing clusters in {project_id}/{region}")
    try:
        client = container_v1.ClusterManagerClient()
        parent = f"projects/{project_id}/locations/{region}"
        clusters = client.list_clusters(parent=parent)
        names = [c.name for c in clusters.clusters]
        return {"clusters": names}
    except Exception as e:
        logger.error("Error listing clusters: %s", e)
        return {"error": str(e)}

@mcp.tool()
def get_cluster(cluster_name: str):
    """Get detailed info about a single GKE cluster."""
    project_id = get_project_id()
    region = get_location()
    logger.info(f"Getting cluster {cluster_name} in {project_id}/{region}")
    try:
        client = container_v1.ClusterManagerClient()
        name = f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
        cluster = client.get_cluster(name=name)
        return {
            "name": cluster.name,
            "status": cluster.status.name,
            "endpoint": cluster.endpoint,
            "node_pools": [np.name for np in cluster.node_pools],
            "location": cluster.location,
        }
    except Exception as e:
        logger.error("Error getting cluster: %s", e)
        return {"error": str(e)}

@mcp.tool()
def giq_generate_manifest(model_name: str, replicas: int = 1):
    """Generate a Kubernetes manifest for inference workloads."""
    logger.info(f"Generating manifest for model {model_name}, replicas {replicas}")
    manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": f"{model_name}-inference"},
        "spec": {
            "replicas": replicas,
            "selector": {"matchLabels": {"app": model_name}},
            "template": {
                "metadata": {"labels": {"app": model_name}},
                "spec": {
                    "containers": [
                        {
                            "name": model_name,
                            "image": f"gcr.io/{get_project_id()}/{model_name}:latest",
                            "ports": [{"containerPort": 8080}],
                        }
                    ]
                },
            },
        },
    }
    return manifest

@mcp.tool()
def list_recommendations(recommender_id: str):
    """List GCP recommendations for GKE resources."""
    project_id = get_project_id()
    location = get_location()
    logger.info(f"Listing recommendations in {project_id}/{location}/{recommender_id}")
    try:
        client = recommender_v1.RecommenderClient()
        parent = f"projects/{project_id}/locations/{location}/recommenders/{recommender_id}"
        recs = client.list_recommendations(parent=parent)
        return {"recommendations": [r.description for r in recs]}
    except Exception as e:
        logger.error("Error in list_recommendations: %s", e)
        return {"error": str(e)}

@mcp.tool()
def query_logs(query: str, limit: int = 10):
    """Query GCP logs using LQL."""
    project_id = get_project_id()
    logger.info(f"Querying logs for {project_id} with query '{query}'")
    try:
        client = logging_v2.Client(project=project_id)
        entries = client.list_entries(filter_=query, page_size=limit)
        logs = [str(e.payload) for e in entries]
        return {"logs": logs}
    except Exception as e:
        logger.error("Error in query_logs: %s", e)
        return {"error": str(e)}

@mcp.tool()
def get_log_schema(log_type: str):
    """Get schema for a log type."""
    logger.info(f"Getting log schema for type {log_type}")
    schemas = {
        "k8s_event_logs": {"fields": ["event_type", "reason", "message", "involved_object"]},
        "k8s_audit_logs": {"fields": ["method_name", "resource_name", "response_status"]},
        "k8s_application_logs": {"fields": ["severity", "message", "timestamp"]},
    }
    return schemas.get(log_type, {"error": "Unknown log type"})

# -----------------------
# New Kubernetes tools
# -----------------------

@mcp.tool()
def list_namespaces(cluster_name: str):
    """List all namespaces in a given GKE cluster."""
    try:
        v1 = get_k8s_client(cluster_name)
        namespaces = v1.list_namespace().items
        return {"namespaces": [ns.metadata.name for ns in namespaces]}
    except Exception as e:
        logger.error("Error in list_namespaces: %s", e)
        return {"error": str(e)}

@mcp.tool()
def get_pods(cluster_name: str, namespace: str = "default"):
    """List all pods in a given namespace of a GKE cluster."""
    try:
        v1 = get_k8s_client(cluster_name)
        pods = v1.list_namespaced_pod(namespace=namespace).items
        return {"pods": [pod.metadata.name for pod in pods]}
    except Exception as e:
        logger.error("Error in get_pods: %s", e)
        return {"error": str(e)}

# -----------------------
# Graceful shutdown
# -----------------------

def shutdown(loop):
    logger.info("🛑 Received termination signal, shutting down MCP server...")
    tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
    for task in tasks:
        task.cancel()

# -----------------------
# Entrypoint
# -----------------------

def main():
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 Starting MCP server on port {port}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: shutdown(loop))

    try:
        loop.run_until_complete(
            mcp.run_async(
                transport="http",
                host="0.0.0.0",
                port=port,
                log_level="info"
            )
        )
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("🛑 MCP server stopped gracefully.")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
