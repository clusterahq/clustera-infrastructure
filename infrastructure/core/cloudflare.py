"""
Cloudflare DNS management for Clustera cluster nodes.

This module manages A records for cluster nodes, mapping node domains to their IP addresses.
Each node can have one or more IP addresses, and the domain is configured per-environment.

Example configuration in Pulumi.{stack}.yaml:
    config:
      clustera-infrastructure:cloudflare_zone_id: "abc123..."
      clustera-infrastructure:nodes:
        - name: "1"
          ips: ["192.0.2.1"]
          domain: "1.clustera.io"
        - name: "staging-1"
          ips: ["192.0.2.10", "192.0.2.11"]
          domain: "staging-1.clustera.io"
"""

import pulumi
import pulumi_cloudflare as cloudflare
from typing import Any


def create_cloudflare_dns_records(config: pulumi.Config) -> dict[str, Any]:
    """
    Create Cloudflare DNS A records for cluster nodes.

    Reads node configuration from Pulumi config and creates A records in Cloudflare
    for each node's domain pointing to its IP address(es). Each node can have multiple
    IP addresses, and separate A records will be created for each IP.

    Args:
        config: Pulumi configuration object containing:
            - cloudflare_zone_id (required): Cloudflare zone ID for the domain
            - nodes (optional): List of node configurations, each with:
                - name: Node identifier (e.g., "1", "staging-1")
                - ips: List of IP addresses for the node
                - domain: Fully qualified domain name (e.g., "1.clustera.io")

    Returns:
        dict with keys:
            - records: List of created Cloudflare Record resources
            - domains: List of domain names that were configured
    """
    stack = pulumi.get_stack()
    is_production = stack in ["production", "prod"]

    # Get Cloudflare zone ID (required)
    zone_id = config.get("cloudflare_zone_id")
    if not zone_id:
        pulumi.log.warn("No cloudflare_zone_id configured, skipping DNS record creation")
        return {"records": [], "domains": []}

    # Get nodes configuration (optional)
    nodes_config = config.get_object("nodes")
    if not nodes_config:
        pulumi.log.info("No nodes configured for DNS records")
        return {"records": [], "domains": []}

    created_records = []
    configured_domains = []

    # Process each node configuration
    for idx, node in enumerate(nodes_config):
        if not isinstance(node, dict):
            pulumi.log.warn(f"Node at index {idx} is not a dictionary, skipping")
            continue

        node_name = node.get("name")
        node_ips = node.get("ips", [])
        node_domain = node.get("domain")

        # Validate node configuration
        if not node_name:
            pulumi.log.warn(f"Node at index {idx} missing 'name' field, skipping")
            continue
        if not node_domain:
            pulumi.log.warn(f"Node '{node_name}' missing 'domain' field, skipping")
            continue
        if not node_ips or not isinstance(node_ips, list):
            pulumi.log.warn(f"Node '{node_name}' has no IPs configured, skipping")
            continue

        configured_domains.append(node_domain)

        # Create A record for each IP address
        for ip_idx, ip_address in enumerate(node_ips):
            # Generate unique resource name for Pulumi
            # Format: clustera-dns-{stack}-{node_name}-{ip_idx}
            resource_name = f"clustera-dns-{stack}-{node_name}-{ip_idx}"

            # Create the A record
            record = cloudflare.Record(
                resource_name,
                zone_id=zone_id,
                name=node_domain,
                type="A",
                content=ip_address,
                ttl=300,  # 5 minutes
                proxied=False,  # Direct DNS, not proxied through Cloudflare
                allow_overwrite=True,  # Allow adopting existing records
                comment=f"Clustera node {node_name} (managed by Pulumi)",
                tags=[
                    f"environment:{stack}",
                    "managed-by:pulumi",
                    "platform:clustera",
                    f"node:{node_name}",
                ],
                opts=pulumi.ResourceOptions(protect=is_production),
            )

            created_records.append(record)

            pulumi.log.info(
                f"Created A record for {node_domain} -> {ip_address} (node: {node_name})"
            )

    pulumi.log.info(
        f"Created {len(created_records)} DNS A records for {len(configured_domains)} nodes"
    )

    return {
        "records": created_records,
        "domains": configured_domains,
    }
