# MediQuery-AI : AI-Powered Medical Document Q&A System

An intelligent document analysis system that lets you upload medical PDFs and ask questions using natural language. Built with Flask, Ollama (local AI), ChromaDB, and SQL Server.

---

## ✨ Features

### 💬 **Smart Chat Sessions**
- Upload multiple PDFs to a chat session
- Ask questions in natural language
- AI searches documents and provides answers with confidence scores
- See which pages and documents the answer came from
- Mark answers as correct or edit them
- Rename and organize chat sessions

### 📊 **Excel Batch Processing**
- Upload an Excel file with multiple questions
- AI answers all questions automatically
- Review, edit, and mark answers as correct
- Export results

### 📜 **Complete History**
- View all Q&A from both chat and Excel tasks
- Filter by date range
- See confidence scores and source citations
- Edit or mark correct any answer retroactively

### 🔐 **User Accounts**
- Secure registration and login
- Each user has isolated data
- Personal dashboard with statistics

---

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Database:** Microsoft SQL Server
- **AI Model:** Ollama (phi3:mini) — runs locally, no API costs
- **Vector Search:** ChromaDB + SentenceTransformers
- **PDF Processing:** pdfplumber, PyPDF2
- **Excel Processing:** pandas, openpyxl
- **Frontend:** HTML, Tailwind CSS, JavaScript

---

## 📋 Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher
- Microsoft SQL Server (Express or higher)
- Ollama installed ([download here](https://ollama.ai))
- 4GB+ RAM (for AI model)
- Windows, Mac, or Linux

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/Ojasvi-Pandey/healthapp.git
cd healthapp
```

### 2. Create virtual environment
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Install and start Ollama
```bash
# Download from https://ollama.ai
# Then pull the model:
ollama pull phi3:mini
ollama serve
```

### 5. Set up SQL Server
- Install SQL Server Express (free)
- Update `config.py` with your database connection details:
```python
  DB_SERVER = 'localhost\SQLEXPRESS'
  DB_NAME = 'miniproj'
```

### 6. Initialize the database
```bash
cd database
python db_setup.py
cd ..
```

### 7. Create required folders
```bash
mkdir uploads
mkdir chroma_db
```

### 8. Run the application
```bash
python app.py
```

### 9. Open in browser
```
http://127.0.0.1:5000
```

---

## 📁 Project Structure
```
HealthApp/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── database/
│   ├── __init__.py
│   ├── models.py          # Database models and queries
│   └── db_setup.py        # Database initialization
├── utils/
│   ├── __init__.py
│   ├── file_processor.py  # PDF/Excel processing
│   ├── embeddings.py      # ChromaDB vector search
│   └── llm_handler.py     # Ollama AI integration
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── chat_session.html
│   ├── excel_qa.html
│   └── history.html
├── static/
│   ├── css/style.css
│   └── js/main.js
├── uploads/               # User-uploaded files (gitignored)
└── chroma_db/             # Vector database (gitignored)
```

---

## 🎯 Usage

### Creating a Chat Session
1. Click "New Chat" on the dashboard
2. Upload one or more PDF files
3. Ask questions in natural language
4. AI provides answers with confidence scores
5. Mark answers as correct or edit them

### Excel Batch Processing
1. Go to "Excel Q&A" in the navigation
2. Upload an Excel file with questions in the first column (or column named "Question")
3. Upload PDF files to search through
4. Click "Process" and wait for AI to answer all questions
5. Review results and edit/mark correct as needed

### Viewing History
1. Click "History" in navigation
2. Use tabs to filter by Chats, Excel Tasks, Documents, or All Q&A
3. Use date filter to find specific time periods
4. Edit or mark correct any answer directly from history

---

## ⚙️ Configuration

Edit `config.py` to customize:
```python
# Database
DB_SERVER = 'localhost\SQLEXPRESS'
DB_NAME = 'miniproj'

# File uploads
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# AI Model
OLLAMA_MODEL = 'phi3:mini'  # Or llama2, mistral, etc.

# Chunking (for document splitting)
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
```

---

## 🐛 Troubleshooting

### "All uploads failed"
- Check that Ollama is running: `ollama serve`
- Ensure PDF files are not corrupted
- Check file size is under 16MB

### "Message not found" when editing
- Refresh the page
- Check database connection in `config.py`

### Low confidence scores
- Upload more relevant documents
- Ensure PDFs have clear, extractable text (not scanned images)
- Try rephrasing the question

### Database connection errors
- Verify SQL Server is running
- Check `config.py` connection string
- Ensure database exists (run `db_setup.py`)

---


## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for local AI inference
- [ChromaDB](https://www.trychroma.com/) for vector search
- [SentenceTransformers](https://www.sbert.net/) for embeddings
- [Flask](https://flask.palletsprojects.com/) for the web framework

---

## 🔮 Future Enhancements

- [ ] Support for more file types (Word, Excel data extraction)
- [ ] Export chat history as PDF
- [ ] Multi-language support
- [ ] Cloud deployment option
- [ ] Mobile app
- [ ] Voice input for questions
- [ ] Collaborative sessions (multiple users)

---

**Made with ❤️ for healthcare professionals**
