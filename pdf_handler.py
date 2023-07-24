from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from chains import load_vector, create_embeddings
import pypdfium2
from concurrent.futures import ThreadPoolExecutor, as_completed

__embeddings = None
_vector_db = None


def get_embeddings_instance():
    global __embeddings
    if __embeddings is None:
        __embeddings = create_embeddings()
    return __embeddings


def get_vector_db_instance():
    global _vector_db
    if _vector_db is None:
        _vector_db = load_vector(get_embeddings_instance())
    return _vector_db


# Extract text from a list of PDF byte arrays
def get_text(pdf_bytes_list):
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(extract_text_from_pdf, pdf_bytes_list))
    return results


# Extract text from a single PDF byte array
def extract_text_from_pdf(pdf_bytes):
    try:
        file = pypdfium2.PdfDocument(pdf_bytes)
        return "\n".join(file.get_page(page_number).get_textpage().get_text_range() for page_number in range(len(file)))
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


# Split text into chunks
def pdf_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=50, separators=["\n", "\n\n"])
    return splitter.split_text(text)


# Get document chunks from a list of texts
def get_document_chunks(texts):
    documents = []
    for text in texts:
        chunks = pdf_chunks(text)
        for chunk in chunks:
            documents.append(Document(page_content=chunk))
    return documents


# Add documents to the vector database
def add_documents_to_db(pdfs_bytes):
    texts = get_text(pdfs_bytes)
    documents = get_document_chunks(texts)
    vector_db = get_vector_db_instance()
    vector_db.add_documents(documents)
