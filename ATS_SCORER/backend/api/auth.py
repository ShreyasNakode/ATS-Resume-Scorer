import logging
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import (
    CLERK_SECRET_KEY,
    CLERK_JWKS_URL,
    CLERK_PEM_PUBLIC_KEY,
    ENABLE_DEMO_AUTH,
)

logger = logging.getLogger("ats_resume_scorer")

_bearer_scheme = HTTPBearer(auto_error=False)
_jwks_client: Optional[jwt.PyJWKClient] = None


def _get_jwks_client() -> Optional[jwt.PyJWKClient]:
    """Get or initialize cached JWKS client for Clerk public keys."""
    global _jwks_client
    if _jwks_client is not None:
        return _jwks_client
    if not CLERK_JWKS_URL:
        return None
    try:
        _jwks_client = jwt.PyJWKClient(CLERK_JWKS_URL, cache_keys=True, lifespan=3600)
        return _jwks_client
    except Exception as exc:
        logger.warning(f"Could not initialize Clerk JWKS client: {exc}")
        return None


def verify_clerk_token(token: str) -> Dict[str, Any]:
    """
    Verify a Clerk JWT session token.
    Supports RS256 with Clerk JWKS or PEM public key, with fallback to demo tokens.
    """
    # 1. Check for demo / development tokens
    if token in ("demo_token", "guest_token", "dev_user") or token.startswith("demo_"):
        return {
            "sub": "demo_user_001",
            "email": "demo@ats-scorer.local",
            "name": "Demo Candidate",
            "is_demo": True,
        }

    # 2. Check unverified header to see algorithm
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise jwt.InvalidTokenError(f"Malformed JWT header: {exc}")

    alg = header.get("alg", "RS256")

    # 3. RS256 Verification with Clerk PEM Public Key
    if CLERK_PEM_PUBLIC_KEY and alg == "RS256":
        pem_key = CLERK_PEM_PUBLIC_KEY
        if not pem_key.startswith("-----BEGIN"):
            pem_key = f"-----BEGIN PUBLIC KEY-----\n{pem_key}\n-----END PUBLIC KEY-----"
        return jwt.decode(
            token,
            pem_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )

    # 4. RS256 Verification with Clerk JWKS endpoint
    if alg == "RS256":
        jwks_client = _get_jwks_client()
        if jwks_client:
            signing_key = jwks_client.get_signing_key_from_jwt(token).key
            return jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )

    # 5. HS256 Verification with Clerk Secret Key (if configured)
    if alg == "HS256" and CLERK_SECRET_KEY:
        return jwt.decode(
            token,
            CLERK_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )

    # If verification keys are not available and demo auth is enabled, provide fallback
    if ENABLE_DEMO_AUTH:
        logger.info("Clerk JWKS not configured; decoding unverified payload in demo mode.")
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception:
            return {"sub": "guest_user", "is_demo": True}

    raise jwt.InvalidTokenError(f"Cannot verify token with algorithm {alg}. Configure CLERK_JWKS_URL or CLERK_PEM_PUBLIC_KEY.")


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency that extracts and validates the Clerk authenticated user ID.
    If ENABLE_DEMO_AUTH is true and no token is provided, returns 'guest_user'.
    """
    if creds is None or not creds.credentials:
        if ENABLE_DEMO_AUTH:
            return "demo_candidate_user"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization: Bearer <token> header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = creds.credentials

    try:
        payload = verify_clerk_token(token)
        user_id = payload.get("sub") or payload.get("id") or "guest_user"
        return str(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token expired — please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        if ENABLE_DEMO_AUTH:
            logger.warning(f"Invalid token '{exc}' - using fallback demo user.")
            return "demo_candidate_user"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Clerk token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        logger.error(f"Clerk authentication error: {exc}")
        if ENABLE_DEMO_AUTH:
            return "demo_candidate_user"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Verify Clerk credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
