from typing import Union, List
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import FAISS, Chroma
from langchain.retrievers import BM25Retriever, TFIDFRetriever, EnsembleRetriever
from sentence_transformers import SentenceTransformer
from torch import embedding
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch


class SentenceTransformerEmbeddings(Embeddings):
    """Custom wrapper for SentenceTransformer to make it compatible with LangChain."""
    
    def __init__(self, model_name="hiieu/halong_embedding"):
        """Initialize the SentenceTransformer model."""
        self.model = SentenceTransformer(model_name)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using the SentenceTransformer model."""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a query using the SentenceTransformer model."""
        embedding = self.model.encode([text])[0]
        return embedding.tolist()
        

class VectorDB:
    def __init__(self, documents=None, vector_db: Union[Chroma, FAISS]=Chroma, embeddings="hf", embedding_model="hiieu/halong_embedding", model_rank="itdainb/PhoRanker"):
        self.vector_db = vector_db
        if embeddings == "hf":
            self.embeddings = HuggingFaceEmbeddings()
        else:
            # Use our custom wrapper for SentenceTransformer
            self.embeddings = SentenceTransformerEmbeddings(model_name=embedding_model)
        
        self.db = self.build_db(documents)
        self.bm25_retriever = self.build_retrievers(documents)
        self.ranker_model = AutoModelForSequenceClassification.from_pretrained(model_rank)
        self.ranker_tokenizer = AutoTokenizer.from_pretrained(model_rank)        


    def build_db(self, documents):
        db = self.vector_db.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        return db

    def build_retrievers(self, documents, top_k=5):
        bm25 = BM25Retriever.from_documents(documents, k=top_k)
        return bm25

    def ranker_docs(self, query, docs, top_k=5, MAX_LENGTH=256):
        # Create query-document pairs
        tokenized_pairs = [self.ranker_tokenizer(query, 
                                                 doc.page_content, 
                                                 padding=True, 
                                                 truncation="longest_first", 
                                                 return_tensors="pt", 
                                                 max_length=MAX_LENGTH) 
                            for doc in docs]

        # Ensure model is in evaluation mode
        self.ranker_model.eval()

        # Run inference
        scores = []
        with torch.no_grad():
            for features in tokenized_pairs:
                model_predictions = self.ranker_model(**features, return_dict=True)
                logits = model_predictions.logits
                probs = torch.sigmoid(logits)  # Apply sigmoid activation
                scores.append(probs[0][0].item())  # Extract score
                
        # Pair documents with their scores
        doc_score_pairs = list(zip(docs, scores))

        # Sort by score in descending order (highest score first)
        sorted_doc_score_pairs = sorted(doc_score_pairs, key=lambda x: x[1], reverse=True)

        # Get top-k (you can change this)
        top_docs = sorted_doc_score_pairs[:top_k]
        return [doc for i, (doc, score) in enumerate(top_docs)]

    
    def get_retriever(self, search_type="similarity", search_kwargs:dict = {"k": 5}):
        retriever_base = self.db.as_retriever(
            search_type=search_type, 
            search_kwargs=search_kwargs
        )
        ensemble_retriever = EnsembleRetriever(retrievers=[retriever_base, self.bm25_retriever])
        return ensemble_retriever

