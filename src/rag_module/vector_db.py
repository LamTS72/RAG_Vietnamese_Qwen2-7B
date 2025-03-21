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
        self.bm25_retriever, self.tf_idf_retriever = self.build_retrievers(documents)
        self.ranker_model = AutoModelForSequenceClassification.from_pretrained(model_rank)
        self.ranker_tokenizer = AutoTokenizer.from_pretrained(model_rank)        


    def build_db(self, documents):
        db = self.vector_db.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        return db

    def build_retrievers(self, documents, top_k=2):
        bm25 = BM25Retriever.from_documents(documents, k=top_k)
        tf_idf = TFIDFRetriever.from_documents(documents, k=top_k)
        return bm25, tf_idf

    def ranker_docs(self, query, docs, top_k=3):
        pairs = [query + " [SEP] " + doc.page_content for doc in docs]
        inputs = self.ranker_tokenizer(pairs, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            logits = self.ranker_model(**inputs).logits
            # Handle different model output shapes
            if logits.shape[1] > 1:  # Multi-class (has at least 2 classes)
                scores = logits[:, 1].tolist()  # Get positive class scores (index 1)
            else:  # Single output - treat as raw score
                scores = logits[:, 0].tolist()  # Get the only available score
        ranked_docs = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked_docs[:top_k]]
    
    def get_retriever(self, search_type="similarity", search_kwargs:dict = {"k": 2}):
        retriever_base = self.db.as_retriever(
            search_type=search_type, 
            search_kwargs=search_kwargs
        )
        ensemble_retriever = EnsembleRetriever(retrievers=[retriever_base, self.bm25_retriever, self.tf_idf_retriever])
        return ensemble_retriever

