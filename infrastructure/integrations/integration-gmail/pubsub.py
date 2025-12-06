"""GCP Pub/Sub topic resources."""

import pulumi
import pulumi_gcp as gcp


def create_pubsub_resources(config: pulumi.Config) -> dict:
    """Create Pub/Sub topics in GCP.

    Args:
        config: Pulumi configuration object

    Returns:
        Dictionary of created resources and outputs
    """
    stack = pulumi.get_stack()

    # Get GCP configuration
    gcp_project = config.require("gcp_project")

    # Sample Pub/Sub topic
    sample_topic = gcp.pubsub.Topic(
        "clustera-notifications-topic",
        name=f"clustera-notifications-{stack}",
        project=gcp_project,
        labels={
            "environment": stack,
            "managed_by": "pulumi",
            "platform": "clustera",
        },
        message_retention_duration="604800s",  # 7 days
    )

    # Create a subscription for the topic
    sample_subscription = gcp.pubsub.Subscription(
        "clustera-notifications-subscription",
        name=f"clustera-notifications-sub-{stack}",
        topic=sample_topic.name,
        project=gcp_project,
        ack_deadline_seconds=20,
        message_retention_duration="604800s",  # 7 days
        retain_acked_messages=False,
        expiration_policy=gcp.pubsub.SubscriptionExpirationPolicyArgs(
            ttl="",  # Never expire
        ),
        labels={
            "environment": stack,
            "managed_by": "pulumi",
            "platform": "clustera",
        },
    )

    return {
        "topic": sample_topic,
        "subscription": sample_subscription,
        "topic_name": sample_topic.name,
        "subscription_name": sample_subscription.name,
    }
