import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from config import Config
import os

class EmbeddingManager:
    """Manage embeddings and ChromaDB with collection isolation"""
    
    def __init__(self):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
        # Initialize ChromaDB
        os.makedirs(Config.CHROMA_PERSIST_DIR, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=Config.CHROMA_PERSIST_DIR)
    
    def get_or_create_collection(self, collection_name):
        """Get or create a specific collection"""
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return collection
        except Exception as e:
            print(f"Error getting/creating collection: {e}")
            return None
    
    def add_document_chunks(self, collection_name, doc_id, chunks_by_page):
        """Add document chunks to specific collection"""
        try:
            collection = self.get_or_create_collection(collection_name)
            if not collection:
                return False
            
            documents = []
            metadatas = []
            ids = []
            
            chunk_id = 0
            for page_num, chunks in chunks_by_page.items():
                for chunk in chunks:
                    documents.append(chunk)
                    metadatas.append({
                        'doc_id': str(doc_id),
                        'page_num': str(page_num),
                        'chunk_id': str(chunk_id)
                    })
                    ids.append(f"{collection_name}_{doc_id}_page{page_num}_chunk{chunk_id}")
                    chunk_id += 1
            
            # Add to ChromaDB
            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            return True
        except Exception as e:
            print(f"Error adding chunks to ChromaDB: {e}")
            return False
    
    def search_similar(self, collection_name, query, n_results=5):
        """Search for similar chunks in specific collection"""
        try:
            collection = self.get_or_create_collection(collection_name)
            if not collection:
                return []
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            search_results = []
            for i, doc in enumerate(results['documents'][0]):
                search_results.append({
                    'text': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else 0
                })
            
            return search_results
        except Exception as e:
            print(f"Error searching ChromaDB: {e}")
            return []
    
    def delete_collection(self, collection_name):
        """Delete a collection"""
        try:
            self.chroma_client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    def collection_exists(self, collection_name):
        """Check if collection exists"""
        try:
            collections = self.chroma_client.list_collections()
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            print(f"Error checking collection: {e}")
            return False

