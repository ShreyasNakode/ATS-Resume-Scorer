import os
from typing import Optional


def get_clerk_publishable_key() -> str:
    """Retrieve Clerk publishable key from environment or secrets."""
    return os.getenv("CLERK_PUBLISHABLE_KEY", "")


def is_demo_user(token: Optional[str]) -> bool:
    """Check if the session token is a demo token."""
    if not token:
        return True
    return token.startswith("demo_") or token in ("demo_token", "guest_token")
