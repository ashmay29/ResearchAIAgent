import secrets

def hash_password(pw: str) -> str:
    # Placeholder only; replace with bcrypt/argon2 in production
    return f"hashed:{pw}"

def verify_password(pw: str, hashed: str) -> bool:
    return hashed == hash_password(pw)

def gen_token() -> str:
    return secrets.token_urlsafe(24)
