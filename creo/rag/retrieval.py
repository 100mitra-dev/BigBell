from creo.rag.vector_store import VectorStoreManager
from creo.rag.document_loader import load_faq_documents


class FAQRetriever:
    def __init__(self):
        self._initialized = False
        self.vs_manager = VectorStoreManager()

    def initialize(self):
        if not self._initialized:
            store = self.vs_manager.get_vector_store()
            if store._collection.count() == 0:
                docs = load_faq_documents()
                if docs:
                    self.vs_manager.add_documents(docs)
            self._initialized = True

    def search(self, query: str, k: int = 5) -> list:
        try:
            self.initialize()
            retriever = self.vs_manager.get_retriever(k=k)
            return retriever.invoke(query)
        except Exception:
            return []

    def search_by_category(self, query: str, category: str, k: int = 5) -> list:
        try:
            self.initialize()
            store = self.vs_manager.get_vector_store()
            return store.similarity_search(
                query, k=k, filter={"category": category}
            )
        except Exception:
            return []
