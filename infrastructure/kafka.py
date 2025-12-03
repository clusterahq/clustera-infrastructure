"""Aiven Kafka topic resources."""

import pulumi
import pulumi_aiven as aiven


def create_kafka_resources(config: pulumi.Config) -> dict:
    """Create Kafka topics in Aiven.

    Args:
        config: Pulumi configuration object

    Returns:
        Dictionary of created resources and outputs
    """
    stack = pulumi.get_stack()

    # Get Aiven configuration
    aiven_project = config.require("aiven_project")
    kafka_service = config.require("kafka_service")

    # Sample Kafka topic
    sample_topic = aiven.KafkaTopic(
        "clustera-events-topic",
        project=aiven_project,
        service_name=kafka_service,
        topic_name=f"clustera.events.{stack}",
        partitions=3,
        replication=2,
        config={
            "retention_ms": "604800000",  # 7 days
            "cleanup_policy": "delete",
            "compression_type": "snappy",
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

    return {
        "topic": sample_topic,
        "topic_name": sample_topic.topic_name,
    }
