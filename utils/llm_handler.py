import ollama
from config import Config

class LLMHandler:
    """Handle LLM interactions using Ollama"""
    
    def __init__(self):
        self.model = Config.OLLAMA_MODEL
    
    def generate_answer(self, question, context_chunks):
        """Generate answer using Ollama"""
        try:
            # Check if we have any relevant chunks
            if not context_chunks:
                return {
                    'answer': "No documents have been uploaded yet. Please upload some documents first.",
                    'confidence': 0,
                    'source_pages': None,
                    'source_doc_names': None
                }
            
            # Prepare context
            context = "\n\n".join([chunk['text'] for chunk in context_chunks])
            
            # Create prompt
            prompt = f"""You are a helpful AI assistant that answers questions based strictly on the provided context.

Context from uploaded documents:
{context}

Question: {question}

Instructions:
1. Answer the question based ONLY on the information provided in the context above.
2. If the context doesn't contain enough information to answer the question, you MUST say EXACTLY: "I don't have enough information in the provided documents to answer this question."
3. Be concise, accurate, and helpful.
4. Do not make up information or use external knowledge.
5. If you quote from the context, keep it brief and relevant.

Answer:"""
            
            # Generate response using Ollama
            response = ollama.generate(
                model=self.model,
                prompt=prompt
            )
            
            answer_text = response['response']
            
            # Calculate confidence score
            confidence = self._calculate_confidence(context_chunks, answer_text)
            
            # Get source information
            source_info = self._get_source_info(context_chunks)
            
            # If confidence is very low (answer indicates no info), set to 0
            if confidence < 20 or self._is_no_answer(answer_text):
                confidence = 0
                source_info['pages'] = None
                source_info['doc_names'] = None
            
            return {
                'answer': answer_text,
                'confidence': confidence,
                'source_pages': source_info['pages'],
                'source_doc_names': source_info['doc_names']
            }
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return {
                'answer': "Error generating answer. Please try again.",
                'confidence': 0,
                'source_pages': None,
                'source_doc_names': None
            }
    
    def _is_no_answer(self, answer):
        """Check if answer indicates no information found"""
        no_answer_phrases = [
            "don't have enough information",
            "doesn't contain enough information",
            "cannot answer",
            "not mentioned",
            "no information",
            "unclear from",
            "not provided in",
            "does not provide",
            "cannot find"
        ]
        answer_lower = answer.lower()
        return any(phrase in answer_lower for phrase in no_answer_phrases)
    
    def _calculate_confidence(self, context_chunks, answer):
        """Calculate confidence score (0-100)"""
        if not context_chunks:
            return 0
        
        # Check if answer indicates no information
        if self._is_no_answer(answer):
            return 0
        
        # Average distance from retrieved chunks 
        avg_distance = sum([chunk.get('distance', 1) for chunk in context_chunks]) / len(context_chunks)
        
        # Convert distance to similarity score
       
        similarity = max(0, 100 - (avg_distance * 50))
        
      
       
        
        # Ensure minimum threshold - if similarity is very low, set to 0
        if similarity < 20:
            similarity = 0
        
        return round(min(100, similarity), 2)
    
    def _get_source_info(self, context_chunks):
        """Extract source document and page information"""
        if not context_chunks:
            return {'pages': None, 'doc_names': None}
        
        # Get unique doc_ids and pages
        doc_ids = set()
        pages = set()
        
        for chunk in context_chunks:
            metadata = chunk.get('metadata', {})
            if 'doc_id' in metadata:
                doc_ids.add(metadata['doc_id'])
            if 'page_num' in metadata:
                pages.add(metadata['page_num'])
        
        # Get document names from doc_ids
        from database.models import DatabaseManager
        doc_names = []
        for doc_id in doc_ids:
            doc = DatabaseManager.get_document_by_id(int(doc_id))
            if doc:
                doc_names.append(doc['filename'])
        
        # Return comma-separated values
        pages_str = ', '.join(sorted(pages, key=lambda x: int(x))) if pages else None
        doc_names_str = ', '.join(doc_names) if doc_names else None
        
        return {'pages': pages_str, 'doc_names': doc_names_str}