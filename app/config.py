from typing import Optional, List
from pydantic import BaseSettings


class Settings(BaseSettings):
    azuread_tenant_id: str
    azuread_client_id: str
    azuread_scopes: Optional[List[str]] = []

    class Config:
        env_file = ".env"


settings = Settings()
