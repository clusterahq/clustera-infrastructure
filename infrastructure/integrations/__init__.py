"""Integrations infrastructure resources."""

import importlib

from .shared import create_kafka_resources

# Import from hyphenated directory using importlib
_gmail = importlib.import_module(".integration-gmail.pubsub", __package__)
create_pubsub_resources = _gmail.create_pubsub_resources

__all__ = ["create_kafka_resources", "create_pubsub_resources"]
