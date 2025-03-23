from typing import Any, Union, List, Literal
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import glob
from tqdm import tqdm
import multiprocessing
from langchain_core.documents import Document
import pdfplumber

def extract_text_as_documents(pdf_path):
    documents = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:  # Avoid adding empty pages
                doc = Document(page_content=text, metadata={"source": pdf_path, "page": i + 1})
                documents.append(doc)
    return documents


def get_num_cpu():
    return multiprocessing.cpu_count()

class BaseLoader():
    """
    Check cpu to handle parallel
    """
    def __init__(self):
        self.num_processors = get_num_cpu()

    def __call__(self, files: List[str], **kwargs) -> Any:
        pass

class PDFLoader(BaseLoader):
    def __init__(self):
        super().__init__()

    def __call__(self, pdf_files: List[str], **kwargs) -> Any:
        num_processors = min(self.num_processors, kwargs["workers"])
        with multiprocessing.Pool(processes=num_processors) as pool:
            doc_loader = []
            total_files = len(pdf_files)
            with tqdm(total=total_files, desc="Loading PDFs", unit="file") as pb:
                for result in pool.imap_unordered(extract_text_as_documents, pdf_files):
                    doc_loader.extend(result)
                    pb.update(1)
        return doc_loader


class TextSplitter():
    def __init__(self, separators: List[str] = ["\n\n", "\n", " ", ""], chunk_size=300, chunk_overlap=50):
        self.splitter = RecursiveCharacterTextSplitter(
            separators=separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def __call__(self, documents) -> Any:
        return self.splitter.split_documents(documents)

class Loader():
    def __init__(self, file_type: str = Literal["pdf"], split_kwargs: dict={"chunk_size":300, "chunk_overlap":0}):
        assert file_type in ["pdf"], "file_type must be pdf"
        self.file_type = file_type
        if self.file_type == "pdf":
            self.doc_loader = PDFLoader()
        else:
            raise ValueError("file_type must be pdf")

        self.doc_splitter = TextSplitter(**split_kwargs)

    def load(self, pdf_files: Union[str, List[str]], workers=1):
        if isinstance(pdf_files, str):
            pdf_files = [pdf_files]
        doc_loaded = self.doc_loader(pdf_files, workers=workers)
        doc_split = self.doc_splitter(doc_loaded)
        return doc_split

    def load_dir(self, dir_path, workers=1):
        """
        Load pdf files from a directory
        """
        if self.file_type == "pdf":
            files = glob.glob(f"{dir_path}/*.pdf")
            assert len(files) > 0, f"No {self.file_type} files found in {dir_path}"
        else:
            raise ValueError("file_type muse be pdf")
        return self.load(files, workers=workers)