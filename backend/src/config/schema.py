from datetime import date, time
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class BirthDetails(BaseModel):
    name: str = Field(..., description="Full name of the individual", min_length=1)
    dateOfBirth: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    timeOfBirth: str = Field(..., description="Time of birth in HH:MM format (24-hour clock)")
    placeOfBirth: str = Field(..., description="City and country of birth (e.g., 'Tokyo, Japan')")
    gender: Literal["Male", "Female"] = Field(..., description="Gender (Male or Female)")

    @field_validator("dateOfBirth")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("dateOfBirth must be in YYYY-MM-DD format")
        return v

    @field_validator("timeOfBirth")
    @classmethod
    def validate_time(cls, v: str) -> str:
        try:
            time.fromisoformat(v)
        except ValueError:
            raise ValueError("timeOfBirth must be in HH:MM or HH:MM:SS format")
        return v

class ReportConfig(BaseModel):
    primary: BirthDetails
    secondary: BirthDetails
    outputDir: str = "./output"

