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

        # 3) Retrieve small contexts to assist generation
        # Tailor retrieval by focus area
        opt = options if isinstance(options, AnalysisOptions) else AnalysisOptions(**(options or {}))
        focus_prompts = self._focus_prompts(opt.focus_area)
        q_overview = "What is this paper about? Summarize the main contributions."
        q_focus = " ".join(focus_prompts)
        # Reduced k from 5 to 2 for each query to limit context size
        logger.info(f"Retrieving context from vector store with k=2 for overview and focus")
        ctx_over = store.query(q_overview, k=2, filter={"doc_id": {"$eq": doc_id}})
        ctx_focus = store.query(q_focus, k=2, filter={"doc_id": {"$eq": doc_id}})
        
        logger.info(f"Retrieved {len(ctx_over)} overview contexts and {len(ctx_focus)} focus contexts")
        
        # Concatenate and cap context at max bytes
        raw_context = "\n\n".join([m["text"] for m in (ctx_over + ctx_focus)])
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
        
        # Use consolidated method - ONE call per chunk instead of 4+ calls
        analysis_results = llm_client.analyze_all_sections(
            text=text,
            style=style,
            context=rich_context
        )
        
        overview = analysis_results["summary"]
        critique = analysis_results["critique"]
        findings = analysis_results["key_findings"]
        cites = analysis_results["citations"]
        
        logger.info(f"LLM analysis completed. Generated summary: {len(overview)} chars, findings: {len(findings)}, citations: {len(cites)}")
        logger.info(f"[PIPELINE_COMPLETE] Saving session for paper_id={paper_id}")

        return {
            "summary_sections": [
                {"title": "Overview", "content": overview},
            ],
            "feedback": critique,
            "key_findings": findings,
            "citations": cites,
        }

pipeline = AnalysisPipeline()
