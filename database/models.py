import pyodbc
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import hashlib
from datetime import datetime

class User:
    def __init__(self, user_id, username, email, password_hash):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)
    
    @staticmethod
    def create_user(username, email, password):
        """Create a new user"""
        try:
            conn = pyodbc.connect(Config.CONNECTION_STRING)
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(password)
            
            cursor.execute("""
                INSERT INTO Users (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        try:
            conn = pyodbc.connect(Config.CONNECTION_STRING)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, username, email, password_hash
                FROM Users
                WHERE username = ?
            """, (username,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                return User(row[0], row[1], row[2], row[3])
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        try:
            conn = pyodbc.connect(Config.CONNECTION_STRING)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, username, email, password_hash
                FROM Users
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                return User(row[0], row[1], row[2], row[3])
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def check_password(self, password):
        """Check if password is correct"""
        return check_password_hash(self.password_hash, password)

class DatabaseManager:
    """Helper class for database operations"""
    
    @staticmethod
    def get_connection():
        return pyodbc.connect(Config.CONNECTION_STRING)
    
    @staticmethod
    def calculate_file_hash(file_path):
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def save_document(user_id, filename, file_type, file_path, total_pages=None):
        """Save document metadata"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            file_hash = DatabaseManager.calculate_file_hash(file_path)
            
            cursor.execute("""
                INSERT INTO Documents (user_id, filename, file_type, file_path, total_pages, file_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, filename, file_type, file_path, total_pages, file_hash))
            
            cursor.execute("SELECT @@IDENTITY")
            doc_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            return doc_id
        except Exception as e:
            print(f"Error saving document: {e}")
            return None
    
    @staticmethod
    def get_user_documents(user_id):
        """Get all documents for a user"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT doc_id, filename, file_type, file_path, upload_date, total_pages, status
                FROM Documents
                WHERE user_id = ?
                ORDER BY upload_date DESC
            """, (user_id,))
            
            documents = []
            for row in cursor.fetchall():
                documents.append({
                    'doc_id': row[0],
                    'filename': row[1],
                    'file_type': row[2],
                    'file_path': row[3],
                    'upload_date': row[4],
                    'total_pages': row[5],
                    'status': row[6]
                })
            
            cursor.close()
            conn.close()
            return documents
        except Exception as e:
            print(f"Error getting documents: {e}")
            return []
    
    # Chat Session Methods
    @staticmethod
    def create_chat_session(user_id, session_name='New Chat'):
        """Create a new chat session"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ChatSessions (user_id, session_name)
                VALUES (?, ?)
            """, (user_id, session_name))
            
            cursor.execute("SELECT @@IDENTITY")
            session_id = cursor.fetchone()[0]
            
            # Generate unique collection name
            collection_name = f"chat_session_{session_id}"
            
            cursor.execute("""
                UPDATE ChatSessions
                SET chroma_collection_name = ?
                WHERE session_id = ?
            """, (collection_name, session_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return session_id, collection_name
        except Exception as e:
            print(f"Error creating chat session: {e}")
            return None, None
    
    @staticmethod
    def get_user_chat_sessions(user_id):
        """Get all chat sessions for a user"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, session_name, created_at, updated_at
                FROM ChatSessions
                WHERE user_id = ?
                ORDER BY updated_at DESC
            """, (user_id,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'session_name': row[1],
                    'created_at': row[2],
                    'updated_at': row[3]
                })
            
            cursor.close()
            conn.close()
            return sessions
        except Exception as e:
            print(f"Error getting chat sessions: {e}")
            return []
    
    @staticmethod
    def update_session_name(session_id, new_name):
        """Update chat session name"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE ChatSessions
                SET session_name = ?, updated_at = GETDATE()
                WHERE session_id = ?
            """, (new_name, session_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating session name: {e}")
            return False
    
    @staticmethod
    def update_session_timestamp(session_id):
        """Update session's last updated timestamp"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE ChatSessions
                SET updated_at = GETDATE()
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating session timestamp: {e}")
            return False
    
    @staticmethod
    def add_document_to_session(session_id, doc_id):
        """Add document to chat session"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            # Check if already exists
            cursor.execute("""
                SELECT session_doc_id FROM SessionDocuments
                WHERE session_id = ? AND doc_id = ?
            """, (session_id, doc_id))
            
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return True  # Already exists
            
            cursor.execute("""
                INSERT INTO SessionDocuments (session_id, doc_id)
                VALUES (?, ?)
            """, (session_id, doc_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding document to session: {e}")
            return False
    
    @staticmethod
    def get_session_documents(session_id):
        """Get all documents for a session"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT d.doc_id, d.filename, d.file_type, d.file_path, d.total_pages
                FROM Documents d
                INNER JOIN SessionDocuments sd ON d.doc_id = sd.doc_id
                WHERE sd.session_id = ?
                ORDER BY sd.uploaded_at DESC
            """, (session_id,))
            
            documents = []
            for row in cursor.fetchall():
                documents.append({
                    'doc_id': row[0],
                    'filename': row[1],
                    'file_type': row[2],
                    'file_path': row[3],
                    'total_pages': row[4]
                })
            
            cursor.close()
            conn.close()
            return documents
        except Exception as e:
            print(f"Error getting session documents: {e}")
            return []
    
    @staticmethod
    def save_chat_message(session_id, message_type, content, confidence_score=None, source_pages=None, source_doc_names=None):
        """Save chat message"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ChatMessages 
                (session_id, message_type, content, confidence_score, source_pages, source_doc_names)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                message_type,
                content,
                confidence_score,
                source_pages,
                source_doc_names
            ))
            
            cursor.execute("SELECT @@IDENTITY")
            message_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            return message_id
        except Exception as e:
            print(f"Error saving chat message: {e}")
            return None
    
    @staticmethod
    def get_chat_messages(session_id):
        """Get all messages for a session"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    message_id,
                    message_type,
                    content,
                    confidence_score,
                    source_pages,
                    source_doc_names,
                    created_at,
                    is_edited,
                    is_correct
                FROM ChatMessages
                WHERE session_id = ?
                ORDER BY created_at ASC
            """, (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'message_id': row[0],
                    'message_type': row[1],
                    'content': row[2],
                    'confidence_score': row[3],
                    'source_pages': row[4],
                    'source_doc_names': row[5],
                    'created_at': row[6],
                    'is_edited': row[7],
                    'is_correct': row[8]
                })
            
            cursor.close()
            conn.close()
            return messages
        except Exception as e:
            print(f"Error getting chat messages: {e}")
            return []
    
    @staticmethod
    def get_session_collection_name(session_id):
        """Get ChromaDB collection name for session"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT chroma_collection_name
                FROM ChatSessions
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return row[0] if row else None
        except Exception as e:
            print(f"Error getting session collection name: {e}")
            return None
    
    # Excel Task Methods
    @staticmethod
    def create_excel_task(user_id, task_name, excel_file_id):
        """Create new Excel task"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ExcelTasks (user_id, task_name, excel_file_id)
                VALUES (?, ?, ?)
            """, (user_id, task_name, excel_file_id))
            
            cursor.execute("SELECT @@IDENTITY")
            task_id = cursor.fetchone()[0]
            
            # Generate unique collection name
            collection_name = f"excel_task_{task_id}"
            
            cursor.execute("""
                UPDATE ExcelTasks
                SET chroma_collection_name = ?
                WHERE task_id = ?
            """, (collection_name, task_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return task_id, collection_name
        except Exception as e:
            print(f"Error creating Excel task: {e}")
            return None, None
    
    @staticmethod
    def add_document_to_task(task_id, doc_id):
        """Add document to Excel task"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO TaskDocuments (task_id, doc_id)
                VALUES (?, ?)
            """, (task_id, doc_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding document to task: {e}")
            return False
    
    @staticmethod
    def save_task_answer(
        task_id,
        question_text,
        answer_text,
        confidence_score,
        source_pages,
        source_doc_names=None
    ):
        """Save answer for Excel task"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO TaskAnswers 
                (task_id, question_text, answer_text, confidence_score, source_pages, source_doc_names)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                question_text,
                answer_text,
                confidence_score,
                source_pages,
                source_doc_names
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving task answer: {e}")
            return False
    
    @staticmethod
    def get_user_excel_tasks(user_id):
        """Get all Excel tasks for a user"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT task_id, task_name, created_at, total_questions, status
                FROM ExcelTasks
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'task_id': row[0],
                    'task_name': row[1],
                    'created_at': row[2],
                    'total_questions': row[3],
                    'status': row[4]
                })
            
            cursor.close()
            conn.close()
            return tasks
        except Exception as e:
            print(f"Error getting Excel tasks: {e}")
            return []
    
    @staticmethod
    def get_task_answers(task_id):
        """Get all answers for a task"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    answer_id,
                    question_text,
                    answer_text,
                    confidence_score,
                    source_pages,
                    source_doc_names,
                    is_correct,
                    is_edited
                FROM TaskAnswers
                WHERE task_id = ?
                ORDER BY answer_id ASC
            """, (task_id,))
            
            answers = []
            for row in cursor.fetchall():
                answers.append({
                    'answer_id': row[0],
                    'question': row[1],
                    'answer': row[2],
                    'confidence': row[3],
                    'source_pages': row[4],
                    'source_doc_names': row[5],
                    'is_correct': row[6],
                    'is_edited': row[7]
                })
            
            cursor.close()
            conn.close()
            return answers
        except Exception as e:
            print(f"Error getting task answers: {e}")
            return []
    
    @staticmethod
    def get_task_collection_name(task_id):
        """Get ChromaDB collection name for task"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT chroma_collection_name
                FROM ExcelTasks
                WHERE task_id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return row[0] if row else None
        except Exception as e:
            print(f"Error getting task collection name: {e}")
            return None

    @staticmethod
    def update_chat_message_feedback(message_id, is_correct, edited_content=None):
        """Update chat message feedback - Sets confidence to 100% ONLY when edited"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            if edited_content:
                # When edited, set confidence to 100%, mark as edited and correct
                cursor.execute("""
                    UPDATE ChatMessages
                    SET content = ?, is_edited = 1, is_correct = 1, confidence_score = 100
                    WHERE message_id = ? AND message_type = 'ai'
                """, (edited_content, message_id))
            elif is_correct:
                # Just marking as correct - keep original confidence score
                cursor.execute("""
                    UPDATE ChatMessages
                    SET is_correct = 1
                    WHERE message_id = ? AND message_type = 'ai'
                """, (message_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating message feedback: {e}")
            return False
    
    @staticmethod
    def update_task_answer_feedback(answer_id, is_correct, edited_answer=None):
        """Update task answer feedback - Sets confidence to 100% ONLY when edited"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            if edited_answer:
                # When edited, set confidence to 100%, mark as edited and correct
                cursor.execute("""
                    UPDATE TaskAnswers
                    SET answer_text = ?, is_correct = 1, is_edited = 1, confidence_score = 100
                    WHERE answer_id = ?
                """, (edited_answer, answer_id))
            else:
                # Just marking as correct - keep original confidence score
                cursor.execute("""
                    UPDATE TaskAnswers
                    SET is_correct = 1
                    WHERE answer_id = ?
                """, (answer_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating answer feedback: {e}")
            return False
    
    @staticmethod
    def get_document_by_id(doc_id):
        """Get document details by ID"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT doc_id, filename, file_type, file_path, total_pages
                FROM Documents
                WHERE doc_id = ?
            """, (doc_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                return {
                    'doc_id': row[0],
                    'filename': row[1],
                    'file_type': row[2],
                    'file_path': row[3],
                    'total_pages': row[4]
                }
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
    
    # NEW METHODS FOR ALL Q&A AND DATE FILTERING
    
    @staticmethod
    def get_all_user_qa(user_id):
        """Get all Q&A from both chat sessions and excel tasks"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            all_qa = []
            
            # Get Q&A from chat sessions
            cursor.execute("""
                SELECT 
                    cm2.message_id as id,
                    'chat' as source_type,
                    cs.session_name as source_name,
                    cm.content as question,
                    cm2.content as answer,
                    cm2.confidence_score as confidence,
                    cm2.source_pages,
                    cm2.source_doc_names,
                    cm2.is_edited,
                    cm.created_at,
                    cm2.is_correct
                FROM ChatMessages cm
                INNER JOIN ChatSessions cs ON cm.session_id = cs.session_id
                LEFT JOIN ChatMessages cm2 ON cm.session_id = cm2.session_id 
                    AND cm2.message_id = (
                        SELECT MIN(message_id) 
                        FROM ChatMessages 
                        WHERE session_id = cm.session_id 
                        AND message_type = 'ai' 
                        AND message_id > cm.message_id
                    )
                WHERE cs.user_id = ? 
                AND cm.message_type = 'user'
                AND cm2.message_id IS NOT NULL
            """, (user_id,))
            
            for row in cursor.fetchall():
                all_qa.append({
                    'id': row[0],
                    'source_type': row[1],
                    'source_name': row[2],
                    'question': row[3],
                    'answer': row[4],
                    'confidence': row[5],
                    'source_pages': row[6],
                    'source_doc_names': row[7],
                    'is_edited': row[8],
                    'created_at': row[9],
                    'is_correct': row[10]
                })
            
            # Get Q&A from Excel tasks
            cursor.execute("""
                SELECT 
                    ta.answer_id as id,
                    'excel' as source_type,
                    et.task_name as source_name,
                    ta.question_text as question,
                    ta.answer_text as answer,
                    ta.confidence_score as confidence,
                    ta.source_pages,
                    ta.source_doc_names,
                    ta.is_edited,
                    ta.created_at,
                    ta.is_correct
                FROM TaskAnswers ta
                INNER JOIN ExcelTasks et ON ta.task_id = et.task_id
                WHERE et.user_id = ?
            """, (user_id,))
            
            for row in cursor.fetchall():
                all_qa.append({
                    'id': row[0],
                    'source_type': row[1],
                    'source_name': row[2],
                    'question': row[3],
                    'answer': row[4],
                    'confidence': row[5],
                    'source_pages': row[6],
                    'source_doc_names': row[7],
                    'is_edited': row[8],
                    'created_at': row[9],
                    'is_correct': row[10]
                })
            
            cursor.close()
            conn.close()
            
            # Sort by date (most recent first)
            all_qa.sort(key=lambda x: x['created_at'], reverse=True)
            
            return all_qa
        except Exception as e:
            print(f"Error getting all Q&A: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def filter_qa_by_date(qa_list, start_date=None, end_date=None):
        """Filter Q&A list by date range"""
        try:
            if not start_date and not end_date:
                return qa_list
            
            filtered_qa = []
            
            for qa in qa_list:
                qa_date = qa['created_at'].date() if isinstance(qa['created_at'], datetime) else qa['created_at']
                
                # Convert string dates to date objects if needed
                if start_date:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date() if isinstance(start_date, str) else start_date
                    if qa_date < start:
                        continue
                
                if end_date:
                    end = datetime.strptime(end_date, '%Y-%m-%d').date() if isinstance(end_date, str) else end_date
                    if qa_date > end:
                        continue
                
                filtered_qa.append(qa)
            
            return filtered_qa
        except Exception as e:
            print(f"Error filtering Q&A by date: {e}")
            return qa_list