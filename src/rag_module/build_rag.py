from pydantic import BaseModel, Field
from src.rag_module.file_loader import Loader
from src.rag_module.vector_db import VectorDB
from src.rag_module.rag_llm import RagLLM
from langchain_core.tracers import LangChainTracer
from langchain_core.callbacks import CallbackManager
class InputQA(BaseModel):
        question: str = Field(..., title="Question to ask model")

class OutputQA(BaseModel):
        answer: str = Field(..., title="Answer from the model")

def build_rag_chain(llm, data_path, data_type, top_k=3, project_name="rag-vietnamese"):
        # Set up LangSmith tracer
        tracer = LangChainTracer(project_name=project_name)
        callback_manager = CallbackManager([tracer])

        docs_loader = Loader(file_type=data_type).load_dir(data_path, workers=1)
        vector_db = VectorDB(documents=docs_loader, embeddings="halong")
        retriever = vector_db.get_retriever()
        rag_chain = RagLLM(llm).get_chain(retriever, ranker=vector_db, top_k=top_k)
        return rag_chain
