from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.embeddings import FakeEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever

from src.core.config import VECTOR_STORE_DIR


class VectorStoreManager:
    _instance = None
    _vector_store = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_vector_store(self) -> Chroma:
        if self._vector_store is None:
            VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
            embeddings = FakeEmbeddings(size=384)
            self._vector_store = Chroma(
                collection_name="faq_store",
                embedding_function=embeddings,
                persist_directory=str(VECTOR_STORE_DIR),
            )
        return self._vector_store

    def get_retriever(self, k: int = 5) -> VectorStoreRetriever:
        return self.get_vector_store().as_retriever(search_kwargs={"k": k})

    def add_documents(self, documents: list):
        store = self.get_vector_store()
        store.add_documents(documents)

    def reset(self):
        self._vector_store = None
        if VECTOR_STORE_DIR.exists():
            import shutil
            shutil.rmtree(VECTOR_STORE_DIR)
