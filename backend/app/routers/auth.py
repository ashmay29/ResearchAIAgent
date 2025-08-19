from fastapi import APIRouter, HTTPException
from ..utils.security import hash_password, verify_password, gen_token
from ..schemas.auth import SignupRequest, LoginRequest, AuthResponse

router = APIRouter()

# In-memory users for demo
USERS: dict[str, dict] = {}
TOKENS: dict[str, str] = {}

@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest):
    if payload.email in USERS:
        raise HTTPException(status_code=400, detail="Email already exists")
    USERS[payload.email] = {"password": hash_password(payload.password)}
    token = gen_token()
    TOKENS[token] = payload.email
    return AuthResponse(token=token, email=payload.email)

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    user = USERS.get(payload.email)
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = gen_token()
    TOKENS[token] = payload.email
    return AuthResponse(token=token, email=payload.email)
