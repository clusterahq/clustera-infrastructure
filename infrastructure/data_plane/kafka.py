"""
Data Plane Kafka Topic Management

Creates and manages Kafka topics for the data plane using Aiven.
Topics are loaded from kafka-topics.yaml in this directory.
"""

import yaml
from pathlib import Path
import pulumi
import pulumi_aiven as aiven


DEFAULT_TOPIC_CONFIG = {
    "partitions": 1,
    "replication": 3,
    "retention_ms": "604800000",      # 7 days
    "retention_bytes": "-1",          # unlimited
    "cleanup_policy": "delete",
    "compression_type": "snappy",
    "max_message_bytes": "26214400",  # 25 MB (for large enrichment payloads)
}


def _load_topics_from_file(file_path: Path) -> list[dict]:
    """Load topic definitions from a YAML file."""
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)
        topics = data.get("topics", [])
        pulumi.log.info(f"Loaded {len(topics)} topics from {file_path.relative_to(Path.cwd())}")
        return topics


def create_data_plane_kafka_resources(config: pulumi.Config) -> dict:
    """
    Create Kafka topics for the data plane from kafka-topics.yaml.

    Topics use {stack} substitution for environment-specific naming.

    Returns:
        dict with:
            - topics: list of aiven.KafkaTopic resources
            - topic_names: list of topic name strings
    """
    stack = pulumi.get_stack()
    project = config.require("aiven_project")
    service = config.require("kafka_service")

    # Load topics from data-plane/kafka-topics.yaml
    topics_file = Path(__file__).parent / "kafka-topics.yaml"

    if not topics_file.exists():
        pulumi.log.warn(f"No kafka-topics.yaml found in data-plane directory")
        return {"topics": [], "topic_names": []}

    topics_to_create = _load_topics_from_file(topics_file)

    # Create topics
    kafka_topics = []
    topic_names = []

    for idx, topic_def in enumerate(topics_to_create):
        # Validate topic has name
        if "name" not in topic_def:
            raise ValueError(f"Topic definition {idx} missing 'name' field in {topics_file}")

        topic_name = topic_def["name"]

        # Apply {stack} substitution
        full_topic_name = topic_name.replace("{stack}", stack)

        # Build config by merging defaults with overrides
        topic_config = DEFAULT_TOPIC_CONFIG.copy()

        # Override with topic-specific settings
        if "partitions" in topic_def:
            topic_config["partitions"] = topic_def["partitions"]
        if "replication" in topic_def:
            topic_config["replication"] = topic_def["replication"]
        if "retention_ms" in topic_def:
            topic_config["retention_ms"] = topic_def["retention_ms"]
        if "retention_bytes" in topic_def:
            topic_config["retention_bytes"] = topic_def["retention_bytes"]
        if "cleanup_policy" in topic_def:
            topic_config["cleanup_policy"] = topic_def["cleanup_policy"]
        if "compression_type" in topic_def:
            topic_config["compression_type"] = topic_def["compression_type"]
        if "max_message_bytes" in topic_def:
            topic_config["max_message_bytes"] = topic_def["max_message_bytes"]

        # Create resource name (sanitize dots and underscores)
        resource_name = f"clustera-{full_topic_name.replace('.', '-').replace('_', '-')}-topic"

        # Determine protection based on stack
        is_production = stack in ["production", "prod"]

        # Create Kafka topic resource
        kafka_topic = aiven.KafkaTopic(
            resource_name,
            project=project,
            service_name=service,
            topic_name=full_topic_name,
            partitions=topic_config["partitions"],
            replication=topic_config["replication"],
            config=aiven.KafkaTopicConfigArgs(
                retention_ms=topic_config["retention_ms"],
                retention_bytes=topic_config["retention_bytes"],
                cleanup_policy=topic_config["cleanup_policy"],
                compression_type=topic_config["compression_type"],
                max_message_bytes=topic_config["max_message_bytes"],
            ),
            tags=[
                aiven.KafkaTopicTagArgs(key="environment", value=stack),
                aiven.KafkaTopicTagArgs(key="managed_by", value="pulumi"),
                aiven.KafkaTopicTagArgs(key="platform", value="clustera"),
                aiven.KafkaTopicTagArgs(key="plane", value="data-plane"),
            ],
            opts=pulumi.ResourceOptions(
                protect=is_production
            ),
        )

        kafka_topics.append(kafka_topic)
        topic_names.append(full_topic_name)

    return {
        "topics": kafka_topics,
        "topic_names": topic_names,
    }
