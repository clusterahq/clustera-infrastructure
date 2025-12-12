"""Aiven Kafka topic resources."""

from pathlib import Path

import pulumi
import pulumi_aiven as aiven
import yaml


# Default configuration for Kafka topics
DEFAULT_TOPIC_CONFIG = {
    "partitions": 1,
    "replication": 2,
    "retention_ms": "259200000",  # 3 days
    "retention_bytes": "629145600",  # 600 MB
    "cleanup_policy": "delete",
    "compression_type": "snappy",
    "max_message_bytes": "26214400",  # 25 MB (for large enrichment payloads)
}


def _find_topic_files() -> list[Path]:
    """Find all kafka-topics.yaml files in the integrations directory.

    Recursively searches the integrations directory (parent of shared/)
    for any kafka-topics.yaml files.

    Returns:
        List of paths to kafka-topics.yaml files
    """
    integrations_dir = Path(__file__).parent.parent
    return sorted(integrations_dir.rglob("kafka-topics.yaml"))


def _load_topics_from_file(topics_file: Path) -> list[dict]:
    """Load topics from a YAML file.

    Args:
        topics_file: Path to the kafka-topics.yaml file

    Returns:
        List of topic definitions from the file
    """
    with open(topics_file, "r") as f:
        topics_data = yaml.safe_load(f)

    if not topics_data:
        return []

    return topics_data.get("topics", [])


def create_kafka_resources(config: pulumi.Config) -> dict:
    """Create Kafka topics in Aiven from YAML configuration.

    Topics are defined in kafka-topics.yaml files found recursively in
    the integrations directory. Each integration can optionally have its
    own kafka-topics.yaml file.

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

    # Find all kafka-topics.yaml files in integrations directory
    topic_files = _find_topic_files()

    if not topic_files:
        pulumi.log.warn("No kafka-topics.yaml files found in integrations directory")
        return {
            "topics": [],
            "topic_names": [],
        }

    # Load topics from all files
    all_topics = []
    for topic_file in topic_files:
        topics = _load_topics_from_file(topic_file)
        if topics:
            pulumi.log.info(f"Loaded {len(topics)} topics from {topic_file.relative_to(topic_file.parent.parent.parent)}")
            all_topics.extend(topics)

    if not all_topics:
        return {
            "topics": [],
            "topic_names": [],
        }

    created_topics = []
    topic_names = []

    # Protect production resources from accidental deletion
    is_production = stack in ["production", "prod"]

    for idx, topic_def in enumerate(all_topics):
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
        max_message_bytes = topic_def.get("max_message_bytes", DEFAULT_TOPIC_CONFIG["max_message_bytes"])

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
                "max_message_bytes": str(max_message_bytes),
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
            opts=pulumi.ResourceOptions(protect=is_production),
        )

        created_topics.append(topic)
        topic_names.append(topic.topic_name)

    return {
        "topics": created_topics,
        "topic_names": topic_names,
    }
