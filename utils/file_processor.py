import PyPDF2
import pdfplumber
import pandas as pd
from pathlib import Path

class FileProcessor:
    """Process PDF and Excel files"""
    
    @staticmethod
    def process_pdf(file_path):
        """Extract text from PDF"""
        try:
            text_by_page = {}
            
            # pdfplumber 
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_by_page[page_num] = text
            
            return text_by_page, len(text_by_page)
        except Exception as e:
            print(f"Error processing PDF: {e}")
            # Fallback to PyPDF2
            try:
                text_by_page = {}
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text:
                            text_by_page[page_num + 1] = text
                
                return text_by_page, len(text_by_page)
            except Exception as e2:
                print(f"Error with PyPDF2: {e2}")
                return {}, 0
    
    @staticmethod
    def process_excel(file_path):
        """Extract questions from Excel"""
        try:
            df = pd.read_excel(file_path)
            
            # Try to find question column
            question_col = None
            for col in df.columns:
                if 'question' in col.lower() or 'query' in col.lower():
                    question_col = col
                    break
            
            if question_col is None:
                # Use first column as questions
                question_col = df.columns[0]
            
            questions = df[question_col].dropna().tolist()
            return questions
        except Exception as e:
            print(f"Error processing Excel: {e}")
            return []
    
    @staticmethod
    def chunk_text(text, chunk_size=500, overlap=50):
        """Split text into chunks"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks