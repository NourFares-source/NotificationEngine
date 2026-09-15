# By specifying env_file = ".env", you tell Pydantic to look for a file named .env in the current
# working directory, parse key-value pairs (like POSTGRES_USER=postgres), and automatically 
# populate your Settings fields with those values.


from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    
    # Optional URL override for CI/Testing environments
    DATABASE_URL: Optional[str] = None

    class Config:
        env_file = ".env"
settings = Settings()