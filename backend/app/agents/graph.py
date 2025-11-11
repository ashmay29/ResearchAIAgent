from ..services.llm import llm_client
from ..services.rag import store
from ..services.ingest import ingest_pdf, is_indexed, get_text
from ..utils.logger import get_logger
from ..schemas.analysis import AnalysisOptions, OutputFormat, FocusArea, AnalysisType

logger = get_logger(__name__)

class AnalysisPipeline:
    def _focus_prompts(self, focus: FocusArea) -> list[str]:
        if focus == FocusArea.METHODOLOGY:
            return [
                "Describe the methodology and experimental setup.",
                "Summarize datasets, metrics, baselines, and evaluation steps.",
            ]
        if focus == FocusArea.LITERATURE_REVIEW:
            return [
                "Summarize related work and how this paper positions itself.",
                "Highlight gaps this work addresses.",
            ]
        if focus == FocusArea.RESULTS:
            return [
                "Summarize quantitative and qualitative results and their significance.",
            ]
        if focus == FocusArea.TECH_STACK:
            return [
                "Extract implementation details: architectures, frameworks, hardware.",
            ]
        # OVERALL
        return [
            "Provide an overall context: problem, contributions, approach, and implications.",
        ]

    def _format_instruction(self, fmt: OutputFormat) -> str:
        if fmt == OutputFormat.BULLET_POINTS:
            return "Format the output strictly as concise bullet points."
        if fmt == OutputFormat.MIND_MAP:
            return (
                "Format the output as a hierarchical mind-map style outline with headings and nested bullets."
            )
        return "Write in well-structured paragraphs."

    def _analysis_instruction(self, t: AnalysisType) -> str:
        if t == AnalysisType.CRITIQUE:
            return "Focus on strengths, weaknesses, assumptions, and limitations."
        if t == AnalysisType.NOTES:
            return "Produce research notes with key terms and concise explanations."
        return "Provide a clear, neutral summary of the paper."

    def run(self, pdf_path: str, options: AnalysisOptions | dict | None = None, paper_id: str | None = None) -> dict:
        logger.info(f"[PIPELINE_START] Starting analysis pipeline for paper_id={paper_id}")
        
        # Ensure the document is ingested (extract -> chunk+embed -> upsert)
        doc_id = paper_id or pdf_path
        if not is_indexed(doc_id):
            logger.info(f"Paper not indexed, running ingestion for {doc_id}")
            ingest_pdf(doc_id, pdf_path)
        else:
            logger.info(f"Paper already indexed: {doc_id}")
        
        # Load stored plaintext for generation
        text = get_text(doc_id) or ""
        text_bytes = len(text.encode('utf-8'))
        logger.info(f"Loaded paper text: {text_bytes} bytes ({len(text)} characters)")

        # Parse options
        opt = options if isinstance(options, AnalysisOptions) else AnalysisOptions(**(options or {}))
        focus_prompts = self._focus_prompts(opt.focus_area)
        
        # OPTIMIZATION 1: Single combined query instead of 2 separate queries
        # OLD: 2 queries (overview + focus) = 2 embedding calls + 2 Pinecone calls
        # NEW: 1 query with combined intent = 1 embedding call + 1 Pinecone call
        q_overview = "What is this paper about? Summarize the main contributions."
        q_focus = " ".join(focus_prompts)
        combined_query = f"{q_overview} Additionally, focus on: {q_focus}"
        
        logger.info(f"Retrieving context from vector store with single query k=4 (was 2 queries with k=2 each)")
        ctx_all = store.query(combined_query, k=4, filter={"doc_id": {"$eq": doc_id}})
        
        logger.info(f"Retrieved {len(ctx_all)} context chunks with single query (saved 1 embedding + 1 Pinecone call)")

        # Build context
        raw_context = "\n\n".join([m["text"] for m in ctx_all])
        # Truncate to prevent context overflow
        from ..config import settings
        max_ctx_bytes = settings.gemini_max_context_bytes
        context_bytes_raw = raw_context.encode('utf-8')
        if len(context_bytes_raw) > max_ctx_bytes:
            context = context_bytes_raw[:max_ctx_bytes].decode('utf-8', errors='ignore')
            logger.info(f"Context truncated from {len(context_bytes_raw)} to {max_ctx_bytes} bytes")
        else:
            context = raw_context
        
        context_bytes = len(context.encode('utf-8'))
        logger.info(f"Total context size: {context_bytes} bytes")

        # 4) Generate with Gemini
        # map output format to style hint
        style = "medium"
        fmt_instruction = self._format_instruction(opt.output_format)
        analysis_instruction = self._analysis_instruction(opt.analysis_type)
        global_instruction = (
            f"Follow these instructions strictly:\n- {fmt_instruction}\n- {analysis_instruction}\n"
        )
        rich_context = global_instruction + "\nFocus guidance:\n- " + "\n- ".join(focus_prompts) + "\n\nContext excerpts:\n" + context
        
        logger.info(f"Calling consolidated LLM analysis. Paper text size: {text_bytes} bytes, Context size: {context_bytes} bytes")
        
        # OPTIMIZATION 2: Direct analysis without extraction (unless truly massive)
        # Pass paper_id to LLM for better identification
        analysis_results = llm_client.analyze_all_sections(
            text=text,
            style=style,
            context=rich_context,
            paper_id=paper_id  # NEW: Pass paper_id for identification
        )
        
        overview = analysis_results["summary"]
        critique = analysis_results["critique"]
        findings = analysis_results["key_findings"]
        cites = analysis_results["citations"]

        # Fallbacks: if any section is empty, derive them with lightweight single-purpose prompts
        if not (critique or "").strip():
            logger.info("Critique missing from consolidated analysis. Falling back to dedicated critique generation.")
            try:
                critique = llm_client.critique(text, context=rich_context)
            except Exception as e:
                logger.warning(f"Critique fallback failed: {e}")

        if not findings:
            logger.info("Key findings missing from consolidated analysis. Falling back to dedicated key findings generation.")
            try:
                findings = llm_client.key_findings(text, context=rich_context)
            except Exception as e:
                logger.warning(f"Key findings fallback failed: {e}")

        if not cites:
            logger.info("Citations missing from consolidated analysis. Falling back to dedicated citations extraction.")
            try:
                cites = llm_client.citations(text)
            except Exception as e:
                logger.warning(f"Citations fallback failed: {e}")
        
        logger.info(f"LLM analysis completed. Generated summary: {len(overview)} chars, findings: {len(findings)}, citations: {len(cites)}")
        logger.info(f"[PIPELINE_COMPLETE] Completed for paper_id={paper_id}")

        # OPTIMIZATION 3: Return paper_id in results for multi-paper tracking
        return {
            "paper_id": paper_id,  # NEW: Include paper ID
            "paper_path": pdf_path,  # NEW: Include path for reference
            "summary_sections": [
                {"title": "Overview", "content": overview},
            ],
            "feedback": critique,
            "key_findings": findings,
            "citations": cites,
        }

pipeline = AnalysisPipeline()
