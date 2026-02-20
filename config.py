import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = "OP123"
    
    # SQL Server settings
    DB_SERVER = 'localhost\SQLEXPRESS'
    DB_NAME = 'miniproj'
    DB_DRIVER = '{ODBC Driver 17 for SQL Server}'
    
    # Connection string for Windows Authentication
    CONNECTION_STRING = f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DB_NAME};Trusted_Connection=yes;'
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Ollama settings
    OLLAMA_MODEL = 'phi3:mini'
    OLLAMA_BASE_URL = 'http://localhost:11434'
    
    # ChromaDB settings
    CHROMA_PERSIST_DIR = 'chroma_db'
    
    # Embedding settings
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

