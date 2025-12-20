"""
Database Models Package
Imports all models for easy access and SQLAlchemy registration
"""

# Import models in a way that avoids circular imports
from .user import User  # noqa
from .student import Student  # noqa
from .batch import Batch  # noqa
from .enrollment import Enrollment  # noqa
from .interview import Interview  # noqa
from .announcement import Announcement  # noqa
from .resource import Resource  # noqa
from .payment import Payment  # noqa

# Import mock test related models conditionally to avoid circular imports
try:
    from .mock_test import MockTest, Question, TestAttempt  # noqa
    MOCK_TEST_MODELS = [MockTest, Question, TestAttempt]
except ImportError:
    MOCK_TEST_MODELS = []

__all__ = [
    'User',
    'Student',
    'Batch',
    'Enrollment',
    'Interview',
    'MockTest',
    'Question',
    'TestAttempt',
    'Announcement',
    'Resource',
    'Payment'
]

# This ensures SQLAlchemy can discover all models
# when using db.create_all() or similar operations
from app.extensions import db  # noqa isort:skip

def init_models():
    """Initialize all models with SQLAlchemy."""
    # This function can be called after all models are defined
    # to set up any additional relationships
    pass
