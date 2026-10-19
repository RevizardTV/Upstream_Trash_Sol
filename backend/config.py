import os
import sys
from dotenv import load_dotenv
from urllib.parse import quote_plus
load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class Config:
    DB_USER = os.getenv("DB_USER", "").strip()
    DB_PASSWORD = os.getenv("DB_PASSWORD", "").strip()
    DB_HOST = os.getenv("DB_HOST", "").strip()
    DB_PORT = os.getenv("DB_PORT", "").strip()
    DB_NAME = os.getenv("DB_NAME", "").strip()
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    EM_RESET_KEY = os.getenv("EM_RESET_KEY", "")
    
    @classmethod
    def db_validate(cls):
        """Ensures all required database environment variables are present."""
        required_vars = ["DB_USER", "DB_PASSWORD", "DB_NAME"]
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required database environment variables: {', '.join(missing)}")
        
    @classmethod
    def auth_validate(cls):
        """Ensures all required Redis and Resend API authentication variables are present."""
        required_vars = ["REDIS_URL", "RESEND_API_KEY"]
        missing = [var for var in required_vars if not getattr(cls, var)]

        if missing:
            raise ValueError(f"Missing required authentication variables: {', '.join(missing)}")
                
    @property
    def DB_URL(self):
        """Dynamic database URL generation using quote_plus for password escaping."""
        encoded_password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{self.DB_USER}:{encoded_password}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
config = Config()
config.db_validate()
config.auth_validate()