"""Aiven Kafka topic resources."""

import os
from pathlib import Path

import pulumi
import pulumi_aiven as aiven
import yaml


# Default configuration for Kafka topics
DEFAULT_TOPIC_CONFIG = {
    "partitions": 5,
    "replication": 2,
    "retention_ms": "259200000",  # 3 days
    "retention_bytes": "5368709120",  # 5GB
    "cleanup_policy": "delete",
    "compression_type": "snappy",
}


def create_kafka_resources(config: pulumi.Config) -> dict:
    """Create Kafka topics in Aiven from YAML configuration.

    Topics are defined in kafka-topics.yaml at the project root.
    This file is shared across all environments/stacks.
    Each topic requires a 'name' field, and can optionally override any
    default configuration values.

    Args:
        config: Pulumi configuration object

    Returns:
        Dictionary of created resources and outputs with keys:
        - topics: List of topic resources
        - topic_names: List of topic names
    """
    stack = pulumi.get_stack()

    # Get Aiven configuration
    aiven_project = config.require("aiven_project")
    kafka_service = config.require("kafka_service")

    # Load topics from shared YAML file
    topics_file = Path(__file__).parent.parent / "kafka-topics.yaml"

    if not topics_file.exists():
        pulumi.log.warn(f"kafka-topics.yaml not found at {topics_file}, no topics will be created")
        return {
            "topics": [],
            "topic_names": [],
        }

    with open(topics_file, "r") as f:
        topics_data = yaml.safe_load(f)

    topics_config = topics_data.get("topics", [])

    if not topics_config:
        # If no topics configured, return empty results
        return {
            "topics": [],
            "topic_names": [],
        }

    created_topics = []
    topic_names = []

    for idx, topic_def in enumerate(topics_config):
        # Topic name is required
        if not isinstance(topic_def, dict) or "name" not in topic_def:
            raise ValueError(f"Topic at index {idx} must be a dict with 'name' field")

        topic_name = topic_def["name"]

        # Build configuration by merging defaults with overrides
        partitions = topic_def.get("partitions", DEFAULT_TOPIC_CONFIG["partitions"])
        replication = topic_def.get("replication", DEFAULT_TOPIC_CONFIG["replication"])
        retention_ms = topic_def.get("retention_ms", DEFAULT_TOPIC_CONFIG["retention_ms"])
        retention_bytes = topic_def.get("retention_bytes", DEFAULT_TOPIC_CONFIG["retention_bytes"])
        cleanup_policy = topic_def.get("cleanup_policy", DEFAULT_TOPIC_CONFIG["cleanup_policy"])
        compression_type = topic_def.get("compression_type", DEFAULT_TOPIC_CONFIG["compression_type"])

        # Apply template substitution for {stack} variable in topic name
        full_topic_name = topic_name.replace("{stack}", stack)

        # Generate Pulumi resource name (sanitized, no dots or special chars)
        resource_name = full_topic_name.replace(".", "-").replace("_", "-")

        # Create the topic
        topic = aiven.KafkaTopic(
            f"clustera-{resource_name}-topic",
            project=aiven_project,
            service_name=kafka_service,
            topic_name=full_topic_name,
            partitions=partitions,
            replication=replication,
            config={
                "retention_ms": str(retention_ms),
                "retention_bytes": str(retention_bytes),
                "cleanup_policy": cleanup_policy,
                "compression_type": compression_type,
            },
            tags=[
                aiven.KafkaTopicTagArgs(
                    key="environment",
                    value=stack,
                ),
                aiven.KafkaTopicTagArgs(
                    key="managed_by",
                    value="pulumi",
                ),
                aiven.KafkaTopicTagArgs(
                    key="platform",
                    value="clustera",
                ),
            ],
        )

        created_topics.append(topic)
        topic_names.append(topic.topic_name)

    return {
        "topics": created_topics,
        "topic_names": topic_names,
    }
