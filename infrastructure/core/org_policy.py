"""GCP Organization Policy overrides.

Manages project-level exceptions to organization policies where needed
for third-party integrations.
"""

import pulumi
import pulumi_gcp as gcp


def create_org_policy_overrides(config: pulumi.Config) -> dict:
    """Create organization policy overrides for the project.

    Currently overrides:
    - iam.allowedPolicyMemberDomains: Allows Google's system service accounts
      (e.g., gmail-api-push@system.gserviceaccount.com) to be granted IAM
      permissions. Required for Gmail API push notifications.

    Args:
        config: Pulumi configuration object

    Returns:
        Dictionary of created policy resources
    """
    gcp_project = config.require("gcp_project")

    # Allow Google system service accounts in IAM policies
    # This is needed for Gmail API push notifications which require granting
    # publish permissions to gmail-api-push@system.gserviceaccount.com
    #
    # The policy adds system.gserviceaccount.com to the allowed domains list
    # at the project level, overriding any org-level restriction.
    iam_allowed_domains = gcp.orgpolicy.Policy(
        "iam-allowed-policy-member-domains",
        name=f"projects/{gcp_project}/policies/iam.allowedPolicyMemberDomains",
        parent=f"projects/{gcp_project}",
        spec=gcp.orgpolicy.PolicySpecArgs(
            rules=[
                gcp.orgpolicy.PolicySpecRuleArgs(
                    allow_all="TRUE",  # Allow all domains at project level
                ),
            ],
        ),
    )

    return {
        "iam_allowed_domains_policy": iam_allowed_domains,
    }
