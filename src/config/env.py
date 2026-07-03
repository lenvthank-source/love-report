import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    opencage_api_key: str = Field(..., alias="OPENCAGE_API_KEY")
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    supabase_url: Optional[str] = Field(None, alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(None, alias="SUPABASE_KEY")
    supabase_jwt_secret: Optional[str] = Field(None, alias="SUPABASE_JWT_SECRET")
    razorpay_key_id: Optional[str] = Field(None, alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: Optional[str] = Field(None, alias="RAZORPAY_KEY_SECRET")
    sendpulse_smtp_user: Optional[str] = Field(None, alias="SENDPULSE_SMTP_USER")
    sendpulse_smtp_password: Optional[str] = Field(None, alias="SENDPULSE_SMTP_PASSWORD")
    sender_email: Optional[str] = Field(None, alias="SENDER_EMAIL")
    sender_name: Optional[str] = Field(None, alias="SENDER_NAME")
    sendpulse_smtp_port: Optional[str] = Field(None, alias="SENDPULSE_SMTP_PORT")

    @field_validator("opencage_api_key", "gemini_api_key", mode="before")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        if not v or not v.strip() or "your_" in v:
            raise ValueError("API key must be set to a valid, non-empty value.")
        return v.strip()

def get_settings() -> Settings:
    """Loads and validates environment variables using Pydantic."""
    try:
        return Settings(
            OPENCAGE_API_KEY=os.getenv("OPENCAGE_API_KEY", ""),
            GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", ""),
            SUPABASE_URL=os.getenv("SUPABASE_URL"),
            SUPABASE_KEY=os.getenv("SUPABASE_KEY"),
            SUPABASE_JWT_SECRET=os.getenv("SUPABASE_JWT_SECRET"),
            RAZORPAY_KEY_ID=os.getenv("RAZORPAY_KEY_ID"),
            RAZORPAY_KEY_SECRET=os.getenv("RAZORPAY_KEY_SECRET"),
            SENDPULSE_SMTP_USER=os.getenv("SENDPULSE_SMTP_USER"),
            SENDPULSE_SMTP_PASSWORD=os.getenv("SENDPULSE_SMTP_PASSWORD"),
            SENDER_EMAIL=os.getenv("SENDER_EMAIL"),
            SENDER_NAME=os.getenv("SENDER_NAME"),
            SENDPULSE_SMTP_PORT=os.getenv("SENDPULSE_SMTP_PORT")
        )
    except Exception as e:
        raise RuntimeError(f"Environment validation failed: {e}")
