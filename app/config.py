from pydantic_settings import BaseSettings


class _settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    mistral_api_key: str

    class Config:
        env_file = ".env"


settings = _settings()
