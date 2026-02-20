

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import time
from datetime import datetime

# Import local modules
from config import Config
from database.models import User, DatabaseManager
from utils.file_processor import FileProcessor
from utils.embeddings import EmbeddingManager
from utils.llm_handler import LLMHandler

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize utilities
embedding_manager = EmbeddingManager()
llm_handler = LLMHandler()
file_processor = FileProcessor()

# Create upload folder
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# AUTHENTICATION ROUTES 


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('register.html')
        
        if User.create_user(username, email, password):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


# MAIN APPLICATION ROUTES


@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent chat sessions (limit 5)
    chat_sessions = DatabaseManager.get_user_chat_sessions(current_user.id)[:5]
    
    # Get recent Excel tasks (limit 5)
    excel_tasks = DatabaseManager.get_user_excel_tasks(current_user.id)[:5]
    
    # Get all user documents for stats
    all_documents = DatabaseManager.get_user_documents(current_user.id)
    
    stats = {
        'total_chats': len(DatabaseManager.get_user_chat_sessions(current_user.id)),
        'total_excel_tasks': len(DatabaseManager.get_user_excel_tasks(current_user.id)),
        'total_documents': len(all_documents),
        'pdf_count': sum(1 for d in all_documents if d['file_type'] == 'pdf')
    }
    
    return render_template('dashboard.html', 
                         chat_sessions=chat_sessions,
                         excel_tasks=excel_tasks,
                         stats=stats)

# CHAT ROUTES


@app.route('/chat')
@login_required
def chat_list():
    """Show list of all chat sessions"""
    sessions = DatabaseManager.get_user_chat_sessions(current_user.id)
    return render_template('chat_list.html', sessions=sessions)

@app.route('/chat/new', methods=['POST'])
@login_required
def create_chat():
    """Create a new chat session"""
    session_id, collection_name = DatabaseManager.create_chat_session(current_user.id)
    if session_id:
        return redirect(url_for('chat_session', session_id=session_id))
    else:
        flash('Error creating chat session', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/chat/<int:session_id>')
@login_required
def chat_session(session_id):
    """View and interact with a chat session"""
    # Get session documents
    session_docs = DatabaseManager.get_session_documents(session_id)
    
    # Get chat messages
    messages = DatabaseManager.get_chat_messages(session_id)
    
    # Get all user documents for reuse option
    all_docs = DatabaseManager.get_user_documents(current_user.id)
    
    # Get session info
    sessions = DatabaseManager.get_user_chat_sessions(current_user.id)
    current_session = next((s for s in sessions if s['session_id'] == session_id), None)
    
    return render_template('chat_session.html',
                         session_id=session_id,
                         session=current_session,
                         session_docs=session_docs,
                         messages=messages,
                         all_docs=all_docs)

@app.route('/chat/<int:session_id>/upload', methods=['POST'])
@login_required
def upload_to_chat(session_id):
    """Upload document to chat session"""
    try:
        print(f"Upload request received for session {session_id}")
        
        # Check if it's a new upload or reuse existing
        reuse_doc_id = request.form.get('reuse_doc_id')
        
        if reuse_doc_id:
            print(f"Reusing document {reuse_doc_id}")
            # Reuse existing document
            doc_id = int(reuse_doc_id)
            
            # Get document info
            all_docs = DatabaseManager.get_user_documents(current_user.id)
            doc = next((d for d in all_docs if d['doc_id'] == doc_id), None)
            
            if not doc:
                print("Document not found")
                return jsonify({'success': False, 'message': 'Document not found'})
            
            # Add to session
            DatabaseManager.add_document_to_session(session_id, doc_id)
            
            # Get collection name and add to ChromaDB
            collection_name = DatabaseManager.get_session_collection_name(session_id)
            
            if doc['file_type'] == 'pdf':
                text_by_page, _ = file_processor.process_pdf(doc['file_path'])
                chunks_by_page = {}
                for page_num, text in text_by_page.items():
                    chunks = file_processor.chunk_text(text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
                    chunks_by_page[page_num] = chunks
                
                embedding_manager.add_document_chunks(collection_name, doc_id, chunks_by_page)
            
            return jsonify({
                'success': True,
                'doc_id': doc_id,
                'filename': doc['filename'],
                'total_pages': doc.get('total_pages')
            })
        
        else:
            # New file upload
            files = request.files.getlist('pdf_files')
            
            if not files or not files[0].filename:
                print("No files provided")
                return jsonify({'success': False, 'message': 'No files provided'})
            
            uploaded_docs = []
            collection_name = DatabaseManager.get_session_collection_name(session_id)
            
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = str(int(time.time()))
                    name, ext = os.path.splitext(filename)
                    filename = f"{name}_{timestamp}{ext}"
                    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                    
                    file.save(file_path)
                    
                    # Process PDF
                    text_by_page, total_pages = file_processor.process_pdf(file_path)
                    
                    # Save to database
                    doc_id = DatabaseManager.save_document(
                        current_user.id,
                        filename,
                        'pdf',
                        file_path,
                        total_pages
                    )
                    
                    # Add to session
                    DatabaseManager.add_document_to_session(session_id, doc_id)
                    
                    # Process and add to ChromaDB
                    chunks_by_page = {}
                    for page_num, text in text_by_page.items():
                        chunks = file_processor.chunk_text(text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
                        chunks_by_page[page_num] = chunks
                    
                    embedding_manager.add_document_chunks(collection_name, doc_id, chunks_by_page)
                    
                    uploaded_docs.append({
                        'doc_id': doc_id,
                        'filename': filename,
                        'total_pages': total_pages
                    })
            
            if len(uploaded_docs) == 0:
                return jsonify({
                    'success': False,
                    'message': 'No valid PDF files uploaded'
                })
            
            # If only one file was uploaded, return it directly
            if len(uploaded_docs) == 1:
                return jsonify({
                    'success': True,
                    'filename': uploaded_docs[0]['filename'],
                    'total_pages': uploaded_docs[0]['total_pages'],
                    'doc_id': uploaded_docs[0]['doc_id']
                })
            
            # Multiple files uploaded, return as array
            return jsonify({
                'success': True,
                'documents': uploaded_docs,
                'message': f'{len(uploaded_docs)} file(s) uploaded successfully'
            })
    
    except Exception as e:
        print(f"Error in upload_to_chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/chat/<int:session_id>/ask', methods=['POST'])
@login_required
def ask_question(session_id):
    """Ask a question in chat session"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'message': 'No question provided'})
        
        # Save user message
        DatabaseManager.save_chat_message(session_id, 'user', question)
        
        # Get collection name
        collection_name = DatabaseManager.get_session_collection_name(session_id)
        
        # Search for relevant chunks
        relevant_chunks = embedding_manager.search_similar(collection_name, question, n_results=5)
        
        # Generate answer
        result = llm_handler.generate_answer(question, relevant_chunks)
        
        # Save AI response
        DatabaseManager.save_chat_message(
            session_id,
            'ai',
            result['answer'],
            result['confidence'],
            result['source_pages'],
            result.get('source_doc_names')
        )
        
        # Update session timestamp
        DatabaseManager.update_session_timestamp(session_id)
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'confidence': result['confidence'],
            'source_pages': result['source_pages'],
            'source_doc_names': result.get('source_doc_names')
        })
    
    except Exception as e:
        print(f"Error in ask_question: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/chat/<int:session_id>/rename', methods=['POST'])
@login_required
def rename_chat(session_id):
    """Rename chat session"""
    try:
        data = request.get_json()
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return jsonify({'success': False, 'message': 'Name cannot be empty'})
        
        success = DatabaseManager.update_session_name(session_id, new_name)
        
        return jsonify({
            'success': success,
            'message': 'Chat renamed' if success else 'Failed to rename chat'
        })
    
    except Exception as e:
        print(f"Error renaming chat: {e}")
        return jsonify({'success': False, 'message': str(e)})


# EXCEL Q&A ROUTES


@app.route('/excel_qa', methods=['GET', 'POST'])
@login_required
def excel_qa():
    if request.method == 'POST':
        try:
            print("Excel Q&A upload started")
            
            # Get files
            excel_file = request.files.get('excel_file')
            pdf_files = request.files.getlist('pdf_files')
            reuse_doc_ids = request.form.getlist('reuse_doc_ids')
            
            if not excel_file or not allowed_file(excel_file.filename):
                flash('Please upload a valid Excel file', 'danger')
                return redirect(request.url)
            
            if not pdf_files and not reuse_doc_ids:
                flash('Please upload at least one PDF or select existing PDFs', 'danger')
                return redirect(request.url)
            
            # Save Excel file
            timestamp = str(int(time.time()))
            excel_filename = secure_filename(excel_file.filename)
            name, ext = os.path.splitext(excel_filename)
            excel_filename = f"{name}_{timestamp}{ext}"
            excel_path = os.path.join(Config.UPLOAD_FOLDER, excel_filename)
            excel_file.save(excel_path)
            
            # Save Excel to database
            excel_doc_id = DatabaseManager.save_document(
                current_user.id,
                excel_filename,
                'xlsx',
                excel_path
            )
            
            # Create task
            task_name = f"Excel Q&A - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            task_id, collection_name = DatabaseManager.create_excel_task(
                current_user.id,
                task_name,
                excel_doc_id
            )
            
            # Process PDF uploads (new files)
            pdf_doc_ids = []
            for pdf_file in pdf_files:
                if pdf_file.filename:
                    pdf_filename = secure_filename(pdf_file.filename)
                    name, ext = os.path.splitext(pdf_filename)
                    pdf_filename = f"{name}_{timestamp}{ext}"
                    pdf_path = os.path.join(Config.UPLOAD_FOLDER, pdf_filename)
                    pdf_file.save(pdf_path)
                    
                    # Process PDF
                    text_by_page, total_pages = file_processor.process_pdf(pdf_path)
                    
                    # Save to database
                    doc_id = DatabaseManager.save_document(
                        current_user.id,
                        pdf_filename,
                        'pdf',
                        pdf_path,
                        total_pages
                    )
                    
                    pdf_doc_ids.append(doc_id)
                    
                    # Add to task
                    DatabaseManager.add_document_to_task(task_id, doc_id)
                    
                    # Process and add to ChromaDB
                    chunks_by_page = {}
                    for page_num, text in text_by_page.items():
                        chunks = file_processor.chunk_text(text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
                        chunks_by_page[page_num] = chunks
                    
                    embedding_manager.add_document_chunks(collection_name, doc_id, chunks_by_page)
            
            # Add reused documents
            for reuse_id in reuse_doc_ids:
                if reuse_id:
                    doc_id = int(reuse_id)
                    DatabaseManager.add_document_to_task(task_id, doc_id)
                    
                    # Get document and add to ChromaDB
                    all_docs = DatabaseManager.get_user_documents(current_user.id)
                    doc = next((d for d in all_docs if d['doc_id'] == doc_id), None)
                    
                    if doc and doc['file_type'] == 'pdf':
                        text_by_page, _ = file_processor.process_pdf(doc['file_path'])
                        chunks_by_page = {}
                        for page_num, text in text_by_page.items():
                            chunks = file_processor.chunk_text(text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
                            chunks_by_page[page_num] = chunks
                        
                        embedding_manager.add_document_chunks(collection_name, doc_id, chunks_by_page)
            
            # Extract questions from Excel
            questions = file_processor.process_excel(excel_path)
            
            if not questions:
                flash('No questions found in Excel file', 'warning')
                return redirect(url_for('excel_qa'))
            
            # Process each question
            for question in questions:
                # Search for relevant chunks
                relevant_chunks = embedding_manager.search_similar(collection_name, question, n_results=5)
                
                # Generate answer
                result = llm_handler.generate_answer(question, relevant_chunks)
                
                # Save answer
                DatabaseManager.save_task_answer(
                    task_id,
                    question,
                    result['answer'],
                    result['confidence'],
                    result['source_pages'],
                    result.get('source_doc_names') 
                )
            
            flash(f'Successfully processed {len(questions)} questions!', 'success')
            return redirect(url_for('view_excel_task', task_id=task_id))
        
        except Exception as e:
            print(f"Error in excel_qa: {e}")
            flash(f'Error processing Excel file: {str(e)}', 'danger')
            return redirect(request.url)
    
    # GET request
    all_docs = DatabaseManager.get_user_documents(current_user.id)
    pdf_docs = [d for d in all_docs if d['file_type'] == 'pdf']
    
    return render_template('excel_qa.html', pdf_docs=pdf_docs)

@app.route('/excel_task/<int:task_id>')
@login_required
def view_excel_task(task_id):
    """View Excel task results"""
    answers = DatabaseManager.get_task_answers(task_id)
    tasks = DatabaseManager.get_user_excel_tasks(current_user.id)
    current_task = next((t for t in tasks if t['task_id'] == task_id), None)
    
    return render_template('excel_task_view.html',
                         task=current_task,
                         answers=answers,
                         task_id=task_id)


# HISTORY ROUTE 


@app.route('/history')
@login_required
def history():
    """Show all history including all Q&A processed"""
    # Get all chat sessions
    chat_sessions = DatabaseManager.get_user_chat_sessions(current_user.id)
    
    # Get all Excel tasks
    excel_tasks = DatabaseManager.get_user_excel_tasks(current_user.id)
    
    # Get all documents
    documents = DatabaseManager.get_user_documents(current_user.id)
    
    # Get all Q&A (from both chats and excel tasks)
    all_qa = DatabaseManager.get_all_user_qa(current_user.id)
    
    # Get date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Filter Q&A by date if provided
    if start_date or end_date:
        all_qa = DatabaseManager.filter_qa_by_date(all_qa, start_date, end_date)
    
    return render_template('history.html',
                         chat_sessions=chat_sessions,
                         excel_tasks=excel_tasks,
                         documents=documents,
                         all_qa=all_qa)


# ROUTES FOR PDF VIEWING AND FEEDBACK


@app.route('/document/view/<int:doc_id>')
@login_required
def view_document(doc_id):
    """View/download a document"""
    try:
        doc = DatabaseManager.get_document_by_id(doc_id)
        if not doc:
            flash('Document not found', 'danger')
            return redirect(url_for('history'))
        
        # Check if user owns this document
        user_docs = DatabaseManager.get_user_documents(current_user.id)
        if not any(d['doc_id'] == doc_id for d in user_docs):
            flash('Access denied', 'danger')
            return redirect(url_for('history'))
        
        return send_file(
            doc['file_path'],
            as_attachment=False,
            download_name=doc['filename']
        )
    except Exception as e:
        print(f"Error viewing document: {e}")
        flash('Error opening document', 'danger')
        return redirect(url_for('history'))

@app.route('/chat/message/<int:message_id>/feedback', methods=['POST'])
@login_required
def chat_message_feedback(message_id):
    """Handle feedback for chat message"""
    try:
        data = request.get_json()
        is_correct = data.get('is_correct', False)
        edited_content = data.get('edited_content')
        
        success = DatabaseManager.update_chat_message_feedback(
            message_id, 
            is_correct, 
            edited_content
        )
        
        return jsonify({
            'success': success,
            'message': 'Feedback saved' if success else 'Failed to save feedback'
        })
    
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/task/answer/<int:answer_id>/feedback', methods=['POST'])
@login_required
def task_answer_feedback(answer_id):
    """Handle feedback for task answer"""
    try:
        data = request.get_json()
        is_correct = data.get('is_correct', False)
        edited_answer = data.get('edited_answer')
        
        success = DatabaseManager.update_task_answer_feedback(
            answer_id, 
            is_correct, 
            edited_answer
        )
        
        return jsonify({
            'success': success,
            'message': 'Feedback saved' if success else 'Failed to save feedback'
        })
    
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return jsonify({'success': False, 'message': str(e)})


# ERROR HANDLERS

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


# MAIN


if __name__ == '__main__':
    from database.db_setup import initialize_database
    print("Initializing database...")
    initialize_database()
    print("Database initialized!")
    
    print("\n" + "="*60)
    print("MediQuery AI - Document-Based Q&A System")
    print("="*60)
    print("\nStarting server...")
    print("Access the application at: http://127.0.0.1:5000")
  
    
    app.run(debug=True, host='0.0.0.0', port=5000)