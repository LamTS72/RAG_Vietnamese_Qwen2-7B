import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from langserve import add_routes

from src.base.llm_model import get_llm
from src.rag_module.build_rag import build_rag_chain, InputQA, OutputQA

llm = get_llm(temp=0.2)
path_docs = "./docs/"

#------------------------CHAINS----------------------------------
genAI_chain = build_rag_chain(llm, data_path=path_docs, data_type="pdf")

#------------------------APP - FAST-API------------------------
app = FastAPI(
        title="LangChain Server",
        version="1.0",
        description="A simple API LangChain Server Runnable interface with advanced RAG capabilities"
)

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

#------------------------ROUTES - FAST-API---------------------
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/check")
async def check():
        return {"status":"ok"}

@app.post("/generative_ai", response_model=OutputQA)
async def generative_ai(inputs: InputQA):
        answer = genAI_chain.invoke(inputs.question)
        return {"answer": answer}


#--------LANGSERVE ROUTES - PLAYGROUND-------------
add_routes(app, genAI_chain, playground_type="default", path="/generative_ai")

