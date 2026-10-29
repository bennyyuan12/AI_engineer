from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    GROK_API_KEY: str
    GOOGLE_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

config = Config() # type: ignore
