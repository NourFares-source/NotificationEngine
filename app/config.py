# By specifying env_file = ".env", you tell Pydantic to look for a file named .env in the current
# working directory, parse key-value pairs (like POSTGRES_USER=postgres), and automatically 
# populate your Settings fields with those values.

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    
    REDIS_HOST: str
    REDIS_PORT: int
    
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()