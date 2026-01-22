from pydantic_settings import BaseSettings, SettingsConfigDict

# Configuration class to manage API keys from environment variables
# pydantic's BaseSettings automatically reads from a .env file
# We are creating a Config class that inherits from BaseSettings to define our configuration schema

class Config(BaseSettings):
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env")   
    
config = Config()