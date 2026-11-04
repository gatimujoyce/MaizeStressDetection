from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CHECKIN_INFERENCE_MODE: Literal["demo", "real"] = "demo"
    ML_ROOT: str = ""
    # Farmers must enter a code texted to their phone when they register. Turn off only while testing without SMS.
    PHONE_VERIFICATION_REQUIRED: bool = True
    # Testing only: also print each texted code in the server window. Leave off in real use.
    AUTH_LOG_CODES: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
