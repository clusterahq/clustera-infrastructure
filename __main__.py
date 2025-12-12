"""Main Pulumi program for Clustera infrastructure."""

import pulumi
from infrastructure import (
    create_kafka_resources,
    create_pubsub_resources,
    create_data_plane_kafka_resources,
)


def main():
    """Main entry point for Pulumi infrastructure."""
    config = pulumi.Config()
    stack = pulumi.get_stack()

    # Create integration Kafka resources in Aiven
    kafka_resources = create_kafka_resources(config)

    # Create data plane Kafka resources in Aiven
    data_plane_kafka = create_data_plane_kafka_resources(config)

    # Create Gmail integration Pub/Sub resources in GCP
    # Note: Requires org policy override (set via gcloud, not Pulumi)
    gmail_pubsub = create_pubsub_resources(config)

    # Export outputs
    pulumi.export("kafka_topic_names", kafka_resources["topic_names"])
    pulumi.export("data_plane_kafka_topic_names", data_plane_kafka["topic_names"])
    pulumi.export("gmail_topic_name", gmail_pubsub["topic_name"])
    pulumi.export("gmail_topic_path", gmail_pubsub["topic_path"])  # For Gmail API watch() calls
    pulumi.export("gmail_subscription_name", gmail_pubsub["subscription_name"])
    pulumi.export("stack", stack)


if __name__ == "__main__":
    main()
