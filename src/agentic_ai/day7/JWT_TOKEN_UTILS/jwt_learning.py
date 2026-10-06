"""Small JWT learning demo. Do not use this demo as production authentication."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "Set JWT_SECRET to a random secret of at least 32 characters "
        "before running this demo."
    )

ALGORITHM = "HS256"
ISSUER = "agentic-ai-learning"
AUDIENCE = "agentic-ai-demo"


def create_token(user_id: str, lifetime: timedelta) -> str:
    """Sign claims into a JWT. Signing does not encrypt the claims."""
    now = datetime.now(timezone.utc)
    claims = {
        "sub": user_id,                 # Subject: who this token represents
        "iat": now,                     # Issued at
        "exp": now + lifetime,          # Expiration
        "iss": ISSUER,                  # Issuer: who created the token
        "aud": AUDIENCE,                # Audience: which app should accept it
    }
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


def validate_token(token: str) -> dict:
    """Verify signature and required claims; reject invalid or expired tokens."""
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        issuer=ISSUER,
        audience=AUDIENCE,
        options={"require": ["sub", "iat", "exp", "iss", "aud"]},
    )


def main() -> None:
    token = create_token("user-123", lifetime=timedelta(minutes=5))

    print("JWT (three dot-separated parts):")
    print(token)

    print("\nValidated claims:")
    print(validate_token(token))

    print("\nExpired-token demonstration:")
    expired_token = create_token("user-123", lifetime=timedelta(seconds=-1))

    try:
        validate_token(expired_token)
    except ExpiredSignatureError:
        print("Correctly rejected: token has expired.")
    except InvalidTokenError as exc:
        print(f"Rejected invalid token: {exc}")

        print("\nTampered-token demonstration:")
    
    
    parts = token.split(".")
    tampered_token = ".".join([parts[0], parts[1], parts[2][:-1] + ("A" if parts[2][-1] != "A" else "B")])

    try:
        validate_token(tampered_token)
    except InvalidTokenError:
        print("Correctly rejected: signature is invalid.")

    print("\nWrong-audience demonstration:")
    try:
        jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience="another-app",
        )
    except InvalidTokenError:
        print("Correctly rejected: audience does not match.")


if __name__ == "__main__":
    main()