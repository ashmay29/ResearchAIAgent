from __future__ import annotations
from typing import List, Optional, Dict
import time
import re
import google.generativeai as genai

from ..config import settings
from ..utils.logger import get_logger, track_api_call

logger = get_logger(__name__)

# Track total API calls across all requests
_api_call_counter = 0


def _model() -> "genai.GenerativeModel":
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")
    genai.configure(api_key=settings.gemini_api_key)
    # Use gemini-pro as default (stable model name)
    # Valid options: "gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro-latest"
    name = settings.gemini_model or "gemini-pro"
    return genai.GenerativeModel(name)


def _chunk_bytes(s: str, max_bytes: int) -> List[str]:
    b = s.encode("utf-8")
    out: List[str] = []
    for i in range(0, len(b), max_bytes):
        out.append(b[i : i + max_bytes].decode("utf-8", errors="ignore"))
    return [x for x in out if x.strip()]


def _calculate_safe_chunk_size(prompt: str, context: str, max_total: int = 30000) -> int:
    """Calculate safe chunk size based on prompt and context to avoid token overflow."""
    prompt_bytes = len(prompt.encode('utf-8'))
    context_bytes = len(context.encode('utf-8'))
    safety_margin = 2000  # for tokenization overhead and response
    available = max_total - prompt_bytes - context_bytes - safety_margin
    return max(1000, available)  # minimum 1KB chunk


def _truncate_bytes(text: str, max_bytes: int) -> str:
    """Truncate text to max_bytes, ensuring valid UTF-8."""
    b = text.encode('utf-8')
    if len(b) <= max_bytes:
        return text
    return b[:max_bytes].decode('utf-8', errors='ignore')


@track_api_call("GEMINI_GENERATION")
def _gen_with_retry(parts: List[dict], max_output_tokens: int = 1024, call_info: str = "") -> str:
    global _api_call_counter
    _api_call_counter += 1
    
    max_retries = int(getattr(settings, "gemini_max_retries", 3))
    backoff = float(getattr(settings, "gemini_retry_backoff", 1.0))
    last_err: Exception | None = None
    
    # Calculate token estimates for logging
    total_bytes = sum(len(str(p.get('text', '')).encode('utf-8')) for p in parts)
    logger.info(f"Making Gemini API call #{_api_call_counter} {call_info}")
    logger.info(f"Input size: ~{total_bytes} bytes, Output tokens requested: {max_output_tokens}")
    
    start_time = time.time()
    
    for attempt in range(1, max_retries + 1):
        try:
            resp = _model().generate_content(
                parts,
                generation_config={"max_output_tokens": max_output_tokens}
            )
            duration = time.time() - start_time
            logger.info(f"API call completed in {duration:.2f}s. Total calls so far: {_api_call_counter}")
            return (resp.text or "").strip()
        except Exception as e:
            last_err = e
            error_str = str(e)
            
            # Check if it's a rate limit error (429) with retry delay
            if "429" in error_str and "retry_delay" in error_str:
                # Extract retry delay from error message if possible
                delay_match = re.search(r'retry in (\d+\.?\d*)s', error_str)
                if delay_match:
                    retry_delay = float(delay_match.group(1))
                    logger.warning(f"[RETRY] Rate limit hit on attempt {attempt}/{max_retries}. Waiting {retry_delay}s as suggested by API...")
                    time.sleep(retry_delay + 1)  # Add 1s buffer
                    continue
            
            logger.warning(f"[RETRY] Generation attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"Generation failed after {max_retries} retries: {last_err}")


def _parse_structured_response(response_text: str) -> Dict[str, any]:
    """Parse structured response with section delimiters into a dict."""
    sections = {
        "summary": "",
        "critique": "",
        "key_findings": [],
        "citations": []
    }
    
    try:
        # Split by section delimiters
        parts = re.split(r'===\s*(\w+(?:\s+\w+)*)\s*===', response_text)
        
        # parts[0] is text before first delimiter (usually empty)
        # parts[1::2] are section names, parts[2::2] are section contents
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                section_name = parts[i].strip().upper().replace(" ", "_")
                section_content = parts[i + 1].strip()
                
                if "SUMMARY" in section_name:
                    sections["summary"] = section_content
                elif "CRITIQUE" in section_name or "FEEDBACK" in section_name:
                    sections["critique"] = section_content
                elif "KEY" in section_name and "FINDING" in section_name:
                    # Extract bullet points
                    lines = section_content.splitlines()
                    findings = [
                        l.strip("- •*\t ") 
                        for l in lines 
                        if l.strip() and (l.strip().startswith("-") or l.strip().startswith("•") or l.strip().startswith("*"))
                    ]
                    sections["key_findings"] = findings
                elif "CITATION" in section_name or "REFERENCE" in section_name:
                    # Extract bullet points
                    lines = section_content.splitlines()
                    citations = [
                        l.strip("- •*\t ") 
                        for l in lines 
                        if l.strip() and (l.strip().startswith("-") or l.strip().startswith("•") or l.strip().startswith("*"))
                    ]
                    sections["citations"] = citations
        
        # Fallback: if no delimiters found, treat entire response as summary
        if not sections["summary"] and not sections["critique"]:
            logger.warning("No section delimiters found in response, using entire text as summary")
            sections["summary"] = response_text
            
    except Exception as e:
        logger.error(f"Error parsing structured response: {e}")
        # Fallback to treating entire response as summary
        sections["summary"] = response_text
    
    return sections


class LLMClient:
    def extract_key_content(self, text: str, context: str = "", max_output_tokens: int = 512) -> str:
        """
        Phase 1: Extract the most important content from the entire paper.
        Reduces large papers to ~10-15% of original size for efficient analysis.
        """
        global _api_call_counter
        
        text_bytes = len(text.encode('utf-8'))
        logger.info(f"[EXTRACT_START] Extracting key content from {text_bytes} bytes of text")
        
        prompt = f"""You are analyzing a research paper. Extract ONLY the most important content for comprehensive analysis.

**Context from paper:**
{context[:2000] if context else ""}

**Full Paper Text:**
{text}

Please extract and return:
1. Abstract/Introduction (key claims and objectives)
2. Core methodology (how they did it)
3. Main results/findings (what they discovered)
4. Key limitations or caveats mentioned
5. Conclusion/implications

Format as a condensed version preserving the most critical information. Remove:
- Redundant explanations
- Extended literature review details  
- Detailed mathematical proofs (keep only key equations if essential)
- Extensive citations (keep only seminal ones)
- Boilerplate text

Target length: 5,000-10,000 characters of the most information-dense content."""
        
        parts = [{"text": prompt}]
        
        try:
            extracted = _gen_with_retry(
                parts, 
                max_output_tokens=max_output_tokens,
                call_info="(Key Content Extraction)"
            )
            
            extracted_bytes = len(extracted.encode('utf-8'))
            reduction_pct = (extracted_bytes / text_bytes) * 100 if text_bytes > 0 else 0
            
            logger.info(f"[EXTRACT_COMPLETE] Extraction successful")
            logger.info(f"Reduced from {text_bytes} to {extracted_bytes} bytes ({reduction_pct:.1f}% of original)")
            
            return extracted
            
        except Exception as e:
            logger.error(f"[EXTRACT_FAILED] Extraction failed: {e}")
            logger.warning("Falling back to first 10KB of text")
            return text[:10000]
    
    def analyze_all_sections(
        self, 
        text: str, 
        style: str = "medium", 
        context: str = "", 
        paper_id: str | None = None
    ) -> Dict[str, any]:
        """
        OPTIMIZED: Single-pass analysis without extraction step for most papers.
        """
        global _api_call_counter
        analysis_start = time.time()
        initial_call_count = _api_call_counter

        logger.info(f"[CONSOLIDATED_ANALYSIS_START] Beginning consolidated analysis for paper_id={paper_id}, style='{style}'")

        text_size = len(text.encode('utf-8'))
        logger.info(f"Paper text size: {text_size} bytes")

        # OPTIMIZATION 1: Remove extraction step - use full text directly
        # Only truncate if exceeds absolute max
        max_input = settings.gemini_max_total_bytes
        if text_size > max_input:
            logger.warning(f"Paper exceeds max input ({text_size} > {max_input}), truncating")
            text_to_analyze = _truncate_bytes(text, max_input)
        else:
            text_to_analyze = text
        
        logger.info(f"[STRATEGY] Direct analysis without extraction (saved 1 API call)")

        # OPTIMIZATION 2: Truncate context safely
        safe_context = _truncate_bytes(context, settings.gemini_max_context_bytes)
        
        # Map style to description
        style_map = {
            "concise": "brief, focusing only on essential points",
            "medium": "balanced, covering main points with reasonable detail",
            "detailed": "comprehensive, exploring nuances and implications",
            "comprehensive": "exhaustive, covering all aspects in depth"
        }
        style_desc = style_map.get(style, style)

        # OPTIMIZATION 3: Add paper identification to prompt
        paper_identifier = f"\n**Paper ID**: {paper_id}\n" if paper_id else ""

        # Build comprehensive prompt
        prompt = f"""You are analyzing a research paper.
{paper_identifier}
**Analysis Style**: {style_desc}

**Context from paper:**
{safe_context}

**Paper Content:**
{text_to_analyze}

Please provide your analysis in this EXACT format with clear delimiters:

=== SUMMARY ===
Provide a {style_desc} summary covering:
- Main research question/objective
- Methodology approach
- Key results and findings
- Main contributions to the field

=== CRITIQUE ===
Provide critical analysis addressing:
- Strengths: What does this paper do well? Novel contributions?
- Limitations: What are the methodological limitations or assumptions?
- Validity: How strong is the evidence? Any concerns about conclusions?
- Impact: Significance and potential influence of this work

=== KEY FINDINGS ===
List 3-5 most important findings as bullet points:
- [Most important discovery or result]
- [Second key finding]
- [Additional findings...]

Focus on concrete, specific findings rather than general statements.

=== CITATIONS ===
List the most important references cited (up to 5):
- [Key citation 1 - Author(s), Year, Brief relevance]
- [Key citation 2]
- ...

Only include citations that are central to understanding this work.

Remember to use the EXACT delimiter format shown above."""
        
        parts = [{"text": prompt}]

        logger.info(f"[API_CALL_START] GEMINI_FINAL_ANALYSIS (single call strategy)")

        try:
            response_text = _gen_with_retry(
                parts,
                max_output_tokens=settings.gemini_max_output_tokens,
                call_info=f"(Final Analysis for {paper_id})"
            )

            parsed = _parse_structured_response(response_text)

            total_duration = time.time() - analysis_start
            total_calls = _api_call_counter - initial_call_count

            logger.info(f"[CONSOLIDATED_ANALYSIS_COMPLETE] Paper {paper_id}: Total Gemini API calls: {total_calls}, Total duration: {total_duration:.2f}s")
            logger.info(f"Generated summary: {len(parsed['summary'])} chars, critique: {len(parsed['critique'])} chars, findings: {len(parsed['key_findings'])}, citations: {len(parsed['citations'])}")

            return parsed

        except Exception as e:
            logger.error(f"[CONSOLIDATED_ANALYSIS_FAILED] Analysis failed for paper {paper_id}: {e}")
            return {
                "summary": f"Analysis failed for paper {paper_id}. Please try again.",
                "critique": "",
                "key_findings": [],
                "citations": []
            }
    
    def summarize(self, text: str, style: str = "medium", context: Optional[str] = None) -> str:
        prompt = (
            "You are an expert research assistant. Write a clear, structured overview of the paper. "
            f"Target length: {style}. Use bullet points where helpful."
        )
        safe_context = _truncate_bytes(context or "", settings.gemini_max_context_bytes)
        if safe_context:
            prompt += "\nUse the following relevant excerpts as context:\n" + safe_context

        # Calculate safe chunk size based on prompt and context
        max_total = settings.gemini_max_total_bytes
        safe_chunk_size = _calculate_safe_chunk_size(prompt, safe_context, max_total)
        
        parts = []
        outputs: List[str] = []
        for i, chunk in enumerate(_chunk_bytes(text, safe_chunk_size)):
            parts = [{"text": prompt}, {"text": f"\nPaper content chunk {i+1}:",}, {"text": chunk}]
            outputs.append(_gen_with_retry(parts, max_output_tokens=settings.gemini_max_output_tokens))
        return "\n\n".join([o for o in outputs if o])

    def critique(self, text: str, context: Optional[str] = None) -> str:
        prompt = (
            "Provide a balanced critique focusing on methodology, assumptions, limitations, and potential improvements."
        )
        safe_context = _truncate_bytes(context or "", settings.gemini_max_context_bytes)
        if safe_context:
            prompt += "\nUse the following relevant excerpts as context:\n" + safe_context
        
        max_total = settings.gemini_max_total_bytes
        safe_chunk_size = _calculate_safe_chunk_size(prompt, safe_context, max_total)
        
        outputs: List[str] = []
        for i, chunk in enumerate(_chunk_bytes(text, safe_chunk_size)):
            parts = [{"text": prompt}, {"text": f"\nPaper content chunk {i+1}:"}, {"text": chunk}]
            outputs.append(_gen_with_retry(parts, max_output_tokens=settings.gemini_max_output_tokens))
        return "\n\n".join([o for o in outputs if o])

    def key_findings(self, text: str, context: Optional[str] = None) -> List[str]:
        prompt = (
            "List the 5 most important key findings as concise bullet points. Return plain text bullets separated by new lines."
        )
        safe_context = _truncate_bytes(context or "", settings.gemini_max_context_bytes)
        if safe_context:
            prompt += "\nUse the following relevant excerpts as context:\n" + safe_context
        
        max_total = settings.gemini_max_total_bytes
        safe_chunk_size = _calculate_safe_chunk_size(prompt, safe_context, max_total)
        
        lines: List[str] = []
        for i, chunk in enumerate(_chunk_bytes(text, safe_chunk_size)):
            parts = [{"text": prompt}, {"text": f"\nPaper content chunk {i+1}:"}, {"text": chunk}]
            text_out = _gen_with_retry(parts, max_output_tokens=512)  # shorter for findings
            lines.extend([l.strip("- •\t ") for l in text_out.splitlines() if l.strip()])
        # dedupe while preserving order
        seen = set()
        uniq = []
        for l in lines:
            if l not in seen:
                seen.add(l)
                uniq.append(l)
        return uniq[:5]

    def citations(self, text: str) -> List[str]:
        prompt = (
            "Extract up to 5 important citations or references mentioned in the paper. "
            "Return each as a single-line citation (authors, year, title if present)."
        )
        # No context for citations, just prompt
        max_total = settings.gemini_max_total_bytes
        safe_chunk_size = _calculate_safe_chunk_size(prompt, "", max_total)
        
        lines: List[str] = []
        for i, chunk in enumerate(_chunk_bytes(text, safe_chunk_size)):
            parts = [{"text": prompt}, {"text": f"\nPaper content chunk {i+1}:"}, {"text": chunk}]
            text_out = _gen_with_retry(parts, max_output_tokens=512)  # shorter for citations
            lines.extend([l.strip("- •\t ") for l in text_out.splitlines() if l.strip()])
        # lightly trim to 5
        return lines[:5]


llm_client = LLMClient()
