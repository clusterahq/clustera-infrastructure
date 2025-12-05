"""Main Pulumi program for Clustera infrastructure."""

import pulumi
from infrastructure import create_kafka_resources, create_pubsub_resources


def main():
    """Main entry point for Pulumi infrastructure."""
    config = pulumi.Config()
    stack = pulumi.get_stack()

    # Create Kafka resources in Aiven
    kafka_resources = create_kafka_resources(config)

    # Create Pub/Sub resources in GCP (commented out for now)
    # pubsub_resources = create_pubsub_resources(config)

    # Export outputs
    pulumi.export("kafka_topic_names", kafka_resources["topic_names"])
    # pulumi.export("pubsub_topic_name", pubsub_resources["topic_name"])
    # pulumi.export("pubsub_subscription_name", pubsub_resources["subscription_name"])
    pulumi.export("stack", stack)


if __name__ == "__main__":
    main()
