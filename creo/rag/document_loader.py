from langchain_core.documents import Document

from creo.utils.json_io import load_faqs


def load_faq_documents() -> list[Document]:
    faqs = load_faqs()
    documents = []
    for faq in faqs:
        doc = Document(
            page_content=f"Q: {faq.question}\nA: {faq.answer}",
            metadata={"id": faq.id, "category": faq.category, "question": faq.question},
        )
        documents.append(doc)
    return documents
