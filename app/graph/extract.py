#Turns raw text into GraphDocument objects using LLMGraphTransformer.


from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from app.services.llm import get_llm
from app.graph.schema import NODE_LABELS, RELATIONSHIP_TYPES
from app.core.config import settings
CHUNK_SIZE = 4000
CHUNK_OVERLAP = 200

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

_extraction_llm = ChatOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    model="nvidia/nemotron-3-super-120b-a12b:free",     # faster, higher TPM
    temperature=0,
    max_retries=3
)

_transformer = LLMGraphTransformer(
    llm=_extraction_llm,
    allowed_nodes=NODE_LABELS,
    allowed_relationships=RELATIONSHIP_TYPES,
    strict_mode=False,   # Allow some flexibility
    ignore_tool_usage=True,     # <-- The critical fix: force JSON parsing mode
)


def split_text(text: str, ticker: str) -> list[Document]:
    doc = Document(page_content=text, metadata={"ticker": ticker})
    chunks = _splitter.split_documents([doc])
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["source"] = f"{ticker}_10-K"
    return chunks


def extract_graph_documents(chunks: list[Document]):
    return _transformer.convert_to_graph_documents(chunks)