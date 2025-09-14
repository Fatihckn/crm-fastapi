import os


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://koyeb-adm:npg_Ee2ZwayAP1Jh@ep-silent-dust-a4lfcnlq.us-east-1.pg.koyeb.app/koyebdb")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "2703a4ceb92fe47227294748c2d03f07")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10"))
    
    # Debug mode
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
