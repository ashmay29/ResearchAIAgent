from ..services.llm import llm_client
from ..services.rag import store
from ..services.pdf_parser import extract_text_from_pdf
from ..utils.logger import get_logger

logger = get_logger(__name__)

class AnalysisPipeline:
    def run(self, pdf_path: str, options: dict | None = None, paper_id: str | None = None) -> dict:
        # 1) Extract
        text = extract_text_from_pdf(pdf_path)

        # 2) Index in Pinecone (by doc id if provided)
        doc_id = paper_id or pdf_path
        store.add_document(doc_id=doc_id, text=text, extra_meta={"source_path": pdf_path})

        # 3) Retrieve small contexts to assist generation
        # Use broad queries to cover overview and methodology
        q_overview = "What is this paper about? Summarize the main contributions."
        q_methods = "What methodology, experiments, or datasets are used?"
        ctx_over = store.query(q_overview, k=5, filter={"doc_id": {"$eq": doc_id}})
        ctx_meth = store.query(q_methods, k=5, filter={"doc_id": {"$eq": doc_id}})
        context = "\n\n".join([m["text"] for m in (ctx_over + ctx_meth)])

        # 4) Generate with Gemini
        style = (options or {}).get("summary_length", "medium")
        overview = llm_client.summarize(text, style=style, context=context)
        critique = llm_client.critique(text, context=context)
        findings = llm_client.key_findings(text, context=context)
        cites = llm_client.citations(text)

        return {
            "summary_sections": [
                {"title": "Overview", "content": overview},
            ],
            "feedback": critique,
            "key_findings": findings,
            "citations": cites,
        }

pipeline = AnalysisPipeline()
