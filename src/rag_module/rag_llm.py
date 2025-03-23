import re
from langchain import hub
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

class Str_OutputParser(StrOutputParser):
    def __init__(self):
        super().__init__()

    def parser(self, text):
        return self.extract_answer(text)
    
    def extract_answer(self, text_response,  pattern: str=r"Answer: \s*(.*)"):
        match = re.search(pattern, text_response, re.DOTALL)
        if match:
                answer_text = match.group(1).strip()
                return answer_text
        else:
                return "Answer not found"
            
            
# Create a Vietnamese version of the prompt
vietnamese_template = """Bạn là trợ lý cho các nhiệm vụ trả lời câu hỏi. Sử dụng các phần ngữ cảnh được truy xuất sau đây để trả lời câu hỏi. Nếu bạn không biết câu trả lời, chỉ cần nói rằng bạn không biết. Sử dụng tối đa ba câu và giữ câu trả lời ngắn gọn.
Câu hỏi: {question} 
Ngữ cảnh: {context} 
Câu trả lời:"""

class RagLLM():
    def __init__(self, llm) -> None:
        self.llm = llm
        # self.prompt = hub.pull("rlm/rag-prompt")
        
        # Create a new prompt template with the same structure but Vietnamese text
        self.prompt = ChatPromptTemplate.from_messages([
            HumanMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=["context", "question"],
                    template=vietnamese_template
                )
            )
        ])
        self.str_parser = Str_OutputParser()
    
    def get_chain(self, retriever, ranker=None, top_k=3):
        """
        Creates a RAG chain with optional document reranking.
        
        Args:
            retriever: Document retriever
            ranker: Instance of VectorDB with ranker_docs method
            top_k: Number of top documents to keep after reranking
        """
        def retrieve_and_rank(question):
            # First retrieve documents with the base retriever
            docs = retriever.invoke(question)
            print(docs)
            # Apply ranker if a ranker is provided
            if ranker is not None:
                docs = ranker.ranker_docs(query=question, docs=docs, top_k=top_k)
            return docs
        
        input_data = {
            "context": RunnablePassthrough() | retrieve_and_rank | self.format_docs,
            "question": RunnablePassthrough()
        }

        rag_chain = (
            input_data | self.prompt | self.llm | self.str_parser
        )
        return rag_chain
    
    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)
        