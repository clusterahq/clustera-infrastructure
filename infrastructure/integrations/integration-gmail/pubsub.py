"""GCP Pub/Sub resources for Gmail API push notifications.

Gmail API uses Pub/Sub to deliver push notifications when emails arrive.
This module creates the required infrastructure:
- Pub/Sub topic for Gmail to publish notifications
- IAM binding granting Gmail API service account publish permissions
- Push subscription to forward notifications to our webhook endpoint

Reference: https://developers.google.com/workspace/gmail/api/guides/push
"""

import pulumi
import pulumi_gcp as gcp


# Gmail API's service account that publishes push notifications
GMAIL_API_SERVICE_ACCOUNT = "gmail-api-push@system.gserviceaccount.com"


def create_pubsub_resources(config: pulumi.Config, depends_on: list = None) -> dict:
    """Create Pub/Sub resources for Gmail push notifications.

    Creates:
    - Topic: Where Gmail publishes email notifications
    - IAM binding: Grants Gmail API publish access to the topic
    - Push subscription: Forwards notifications to webhook endpoint

    Args:
        config: Pulumi configuration object
        depends_on: Optional list of resources that must be created first
                   (e.g., org policy overrides)

    Returns:
        Dictionary of created resources and outputs
    """
    if depends_on is None:
        depends_on = []
    stack = pulumi.get_stack()
    is_production = stack in ["production", "prod"]

    # Get GCP configuration
    gcp_project = config.require("gcp_project")

    # Get webhook endpoint URL (optional - if not set, creates pull subscription)
    webhook_endpoint = config.get("gmail_webhook_endpoint")

    # Topic for Gmail push notifications
    # Google recommends using a single topic for all Gmail API notifications
    gmail_topic = gcp.pubsub.Topic(
        "integration-gmail-webhook-topic",
        name=f"{stack}-integration-gmail-webhook",
        project=gcp_project,
        labels={
            "environment": stack,
            "managed_by": "pulumi",
            "platform": "clustera",
            "integration": "gmail",
        },
        message_retention_duration="86400s",  # 1 day (notifications are time-sensitive)
        opts=pulumi.ResourceOptions(protect=is_production),
    )

    # Grant Gmail API service account permission to publish to the topic
    # This is required for Gmail to send push notifications
    # Note: Requires org policy override to allow system.gserviceaccount.com
    gmail_publisher_binding = gcp.pubsub.TopicIAMMember(
        "gmail-api-publisher",
        project=gcp_project,
        topic=gmail_topic.name,
        role="roles/pubsub.publisher",
        member=f"serviceAccount:{GMAIL_API_SERVICE_ACCOUNT}",
        opts=pulumi.ResourceOptions(
            protect=is_production,
            depends_on=depends_on,
        ),
    )

    # Create subscription based on whether webhook endpoint is configured
    if webhook_endpoint:
        # Push subscription - forwards messages to webhook endpoint
        gmail_subscription = gcp.pubsub.Subscription(
            "integration-gmail-webhook-subscription",
            name=f"{stack}-integration-gmail-webhook-sub",
            topic=gmail_topic.name,
            project=gcp_project,
            ack_deadline_seconds=30,  # Time to process notification
            message_retention_duration="600s",  # 10 minutes (short for webhooks)
            retain_acked_messages=False,
            expiration_policy=gcp.pubsub.SubscriptionExpirationPolicyArgs(
                ttl="",  # Never expire
            ),
            push_config=gcp.pubsub.SubscriptionPushConfigArgs(
                push_endpoint=webhook_endpoint,
                attributes={
                    "x-goog-version": "v1",
                },
            ),
            retry_policy=gcp.pubsub.SubscriptionRetryPolicyArgs(
                minimum_backoff="10s",
                maximum_backoff="600s",  # 10 minutes max retry
            ),
            labels={
                "environment": stack,
                "managed_by": "pulumi",
                "platform": "clustera",
                "integration": "gmail",
            },
            opts=pulumi.ResourceOptions(protect=is_production),
        )
    else:
        # Pull subscription - application pulls messages
        gmail_subscription = gcp.pubsub.Subscription(
            "integration-gmail-webhook-subscription",
            name=f"{stack}-integration-gmail-webhook-sub",
            topic=gmail_topic.name,
            project=gcp_project,
            ack_deadline_seconds=30,
            message_retention_duration="3600s",  # 1 hour for pull
            retain_acked_messages=False,
            expiration_policy=gcp.pubsub.SubscriptionExpirationPolicyArgs(
                ttl="",  # Never expire
            ),
            labels={
                "environment": stack,
                "managed_by": "pulumi",
                "platform": "clustera",
                "integration": "gmail",
            },
            opts=pulumi.ResourceOptions(protect=is_production),
        )

    # Export the full topic path for use with Gmail API watch() calls
    # Format: projects/{project}/topics/{topic}
    topic_path = pulumi.Output.concat(
        "projects/", gcp_project, "/topics/", gmail_topic.name
    )

    return {
        "topic": gmail_topic,
        "topic_iam_binding": gmail_publisher_binding,
        "subscription": gmail_subscription,
        "topic_name": gmail_topic.name,
        "topic_path": topic_path,  # Full path for Gmail API watch() calls
        "subscription_name": gmail_subscription.name,
    }
