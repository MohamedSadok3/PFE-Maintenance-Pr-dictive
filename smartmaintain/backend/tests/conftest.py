"""
Shared pytest configuration and fixtures.

Sets required environment variables before any test module is imported
so services that read env vars at import time work without a real .env file.
"""

import os

# Minimum env vars needed for all services to import without raising
os.environ.setdefault("POSTGRES_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("JWT_SECRET",   "test-secret-key-for-unit-tests-only")
os.environ.setdefault("REDIS_URL",    "redis://localhost:6379")
os.environ.setdefault("MOCK_ML",      "true")
