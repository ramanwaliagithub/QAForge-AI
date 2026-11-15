"""Test data: validated models, interchangeable sources (Faker, a model, a frozen file) and a seeded factory."""
from framework.data.faker_source import FakerSource
from framework.data.models import Customer, Identity

__all__ = ["Customer", "FakerSource", "Identity"]
