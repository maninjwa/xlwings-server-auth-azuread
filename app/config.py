from pydantic import BaseSettings


class Settings(BaseSettings):
    azuread_tenant_id: str
    azuread_client_id: str

    class Config:
        env_file = ".env"


settings = Settings()
