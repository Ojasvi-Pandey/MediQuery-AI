import pyodbc
from config import Config

def create_database():
    """Create database if it doesn't exist"""
    try:
        conn_str = f'DRIVER={Config.DB_DRIVER};SERVER={Config.DB_SERVER};DATABASE=master;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(f"""
        IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{Config.DB_NAME}')
        BEGIN
            CREATE DATABASE {Config.DB_NAME}
        END
        """)
        
        print(f"Database '{Config.DB_NAME}' created or already exists.")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")

def create_tables():
    """Create all necessary tables"""
    try:
        conn = pyodbc.connect(Config.CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users')
        BEGIN
            CREATE TABLE Users (
                user_id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(50) UNIQUE NOT NULL,
                email NVARCHAR(100) UNIQUE NOT NULL,
                password_hash NVARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT GETDATE()
            )
        END
        """)
        
        # Documents table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Documents')
        BEGIN
            CREATE TABLE Documents (
                doc_id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT FOREIGN KEY REFERENCES Users(user_id),
                filename NVARCHAR(255) NOT NULL,
                file_type NVARCHAR(10) NOT NULL,
                file_path NVARCHAR(500) NOT NULL,
                upload_date DATETIME DEFAULT GETDATE(),
                total_pages INT,
                status NVARCHAR(50) DEFAULT 'uploaded',
                file_hash NVARCHAR(64)
            )
        END
        """)
        
        # Chat Sessions table 
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ChatSessions')
        BEGIN
            CREATE TABLE ChatSessions (
                session_id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT FOREIGN KEY REFERENCES Users(user_id),
                session_name NVARCHAR(255) DEFAULT 'New Chat',
                created_at DATETIME DEFAULT GETDATE(),
                updated_at DATETIME DEFAULT GETDATE(),
                chroma_collection_name NVARCHAR(255)
            )
        END
        """)
        
        # Session Documents table 
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SessionDocuments')
        BEGIN
            CREATE TABLE SessionDocuments (
                session_doc_id INT IDENTITY(1,1) PRIMARY KEY,
                session_id INT FOREIGN KEY REFERENCES ChatSessions(session_id) ON DELETE CASCADE,
                doc_id INT FOREIGN KEY REFERENCES Documents(doc_id),
                uploaded_at DATETIME DEFAULT GETDATE()
            )
        END
        """)
        
        # Chat Messages table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ChatMessages')
        BEGIN
            CREATE TABLE ChatMessages (
                message_id INT IDENTITY(1,1) PRIMARY KEY,
                session_id INT FOREIGN KEY REFERENCES ChatSessions(session_id) ON DELETE CASCADE,
                message_type NVARCHAR(10) NOT NULL,
                content NVARCHAR(MAX) NOT NULL,
                confidence_score FLOAT,
                source_pages NVARCHAR(255),
                source_doc_names NVARCHAR(500),
                created_at DATETIME DEFAULT GETDATE(),
                is_edited BIT DEFAULT 0,
                is_correct BIT DEFAULT 0
            )
        END
        ELSE
        BEGIN
            -- Add is_correct column if it doesn't exist (for existing databases)
            IF NOT EXISTS (SELECT * FROM sys.columns 
                           WHERE object_id = OBJECT_ID('ChatMessages') 
                           AND name = 'is_correct')
            BEGIN
                ALTER TABLE ChatMessages ADD is_correct BIT DEFAULT 0
                PRINT 'Added is_correct column to ChatMessages table'
            END
        END
        """)
        
        # Excel Processing Tasks table 
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ExcelTasks')
        BEGIN
            CREATE TABLE ExcelTasks (
                task_id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT FOREIGN KEY REFERENCES Users(user_id),
                task_name NVARCHAR(255) DEFAULT 'Excel Q&A Task',
                excel_file_id INT FOREIGN KEY REFERENCES Documents(doc_id),
                created_at DATETIME DEFAULT GETDATE(),
                chroma_collection_name NVARCHAR(255),
                total_questions INT,
                status NVARCHAR(50) DEFAULT 'completed'
            )
        END
        """)
        
        # Task Documents table 
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TaskDocuments')
        BEGIN
            CREATE TABLE TaskDocuments (
                task_doc_id INT IDENTITY(1,1) PRIMARY KEY,
                task_id INT FOREIGN KEY REFERENCES ExcelTasks(task_id) ON DELETE CASCADE,
                doc_id INT FOREIGN KEY REFERENCES Documents(doc_id),
                uploaded_at DATETIME DEFAULT GETDATE()
            )
        END
        """)
        
        # Task Answers table 
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TaskAnswers')
        BEGIN
            CREATE TABLE TaskAnswers (
                answer_id INT IDENTITY(1,1) PRIMARY KEY,
                task_id INT FOREIGN KEY REFERENCES ExcelTasks(task_id) ON DELETE CASCADE,
                question_text NVARCHAR(MAX) NOT NULL,
                answer_text NVARCHAR(MAX) NOT NULL,
                confidence_score FLOAT,
                source_pages NVARCHAR(255),
                source_doc_names NVARCHAR(500),
                created_at DATETIME DEFAULT GETDATE(),
                is_correct BIT DEFAULT 0,
                is_edited BIT DEFAULT 0
            )
        END
        """)

        conn.commit()
        print("All tables created successfully.")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating tables: {e}")

def initialize_database():
    """Initialize complete database"""
    create_database()
    create_tables()

if __name__ == "__main__":
    initialize_database()