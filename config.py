import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    PTM_BASE_URL = os.getenv("PTM_BASE_URL", "http://localhost:8000")
    PTM_CLIENT_ID = os.getenv("PTM_CLIENT_ID", "")
    PTM_CLIENT_SECRET = os.getenv("PTM_CLIENT_SECRET", "")
    PTM_SCOPE = os.getenv("PTM_SCOPE", "tournament.read tournament.write")
    PORT = int(os.getenv("PORT", "8095"))


config = Config()
