from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class SettingsIn(BaseModel):
    default_summary_length: str = "medium"

SETTINGS = SettingsIn()

@router.get("")
def get_settings():
    return SETTINGS

@router.post("")
def update_settings(payload: SettingsIn):
    global SETTINGS
    SETTINGS = payload
    return SETTINGS
