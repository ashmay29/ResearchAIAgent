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
    def analyze_all_sections(self, text: str, style: str = "medium", context: str = "") -> Dict[str, any]:
        """
        Consolidated method that makes ONE Gemini call per chunk to generate all sections.
        Reduces API calls from 4+ per chunk to 1 per chunk.
        
        Returns dict with keys: summary, critique, key_findings (list), citations (list)
        """
        global _api_call_counter
        analysis_start = time.time()
        initial_call_count = _api_call_counter
        
        logger.info(f"[CONSOLIDATED_ANALYSIS_START] Beginning consolidated analysis with style='{style}'")
        
        # Truncate context to safe size
        safe_context = _truncate_bytes(context, settings.gemini_max_context_bytes)
        
        # Build structured prompt template
        prompt_template = """You are analyzing a research paper. Based on the excerpt below and the provided context, generate a comprehensive analysis with the following sections:

**Style for summary**: {style} (concise/detailed/comprehensive)

**Context from paper**:
{context}

**Paper Excerpt**:
{chunk}

Please provide your analysis in this EXACT format with clear delimiters:

=== SUMMARY ===
[Write a {style} summary of this excerpt, focusing on the main contributions and methodology]

=== CRITIQUE ===
[Provide critical analysis: What are the strengths? What are potential limitations or weaknesses in methodology, assumptions, or claims?]

=== KEY FINDINGS ===
- [Key finding 1]
- [Key finding 2]
- [Key finding 3]
[List 3-5 main discoveries or results from this excerpt]

=== CITATIONS ===
- [Citation 1]
- [Citation 2]
[List important references or works cited in this excerpt]

Ensure each section is clearly separated by the delimiter lines."""
        
        # Calculate safe chunk size
        base_prompt = prompt_template.format(style=style, context=safe_context, chunk="")
        max_total = settings.gemini_max_total_bytes
        safe_chunk_size = _calculate_safe_chunk_size(base_prompt, safe_context, max_total)
        
        # Chunk the text
        chunks = _chunk_bytes(text, safe_chunk_size)
        total_chunks = len(chunks)
        
        logger.info(f"Text split into {total_chunks} chunks of ~{safe_chunk_size} bytes each")
        
        # Aggregate results across chunks
        all_summaries = []
        all_critiques = []
        all_findings = []
        all_citations = []
        
        for chunk_idx, chunk in enumerate(chunks, 1):
            # Build prompt for this chunk
            prompt = prompt_template.format(
                style=style,
                context=safe_context if chunk_idx == 1 else "",  # Only include context in first chunk
                chunk=chunk
            )
            
            parts = [{"text": prompt}]
            call_info = f"for chunk {chunk_idx}/{total_chunks}"
            
            # Make single consolidated API call
            response_text = _gen_with_retry(
                parts, 
                max_output_tokens=settings.gemini_max_output_tokens,
                call_info=call_info
            )
            
            # Parse structured response
            parsed = _parse_structured_response(response_text)
            
            # Aggregate results
            if parsed["summary"]:
                all_summaries.append(parsed["summary"])
            if parsed["critique"]:
                all_critiques.append(parsed["critique"])
            if parsed["key_findings"]:
                all_findings.extend(parsed["key_findings"])
            if parsed["citations"]:
                all_citations.extend(parsed["citations"])
        
        # Deduplicate findings and citations while preserving order
        unique_findings = []
        seen_findings = set()
        for f in all_findings:
            f_lower = f.lower()
            if f_lower not in seen_findings:
                seen_findings.add(f_lower)
                unique_findings.append(f)
        
        unique_citations = []
        seen_citations = set()
        for c in all_citations:
            c_lower = c.lower()
            if c_lower not in seen_citations:
                seen_citations.add(c_lower)
                unique_citations.append(c)
        
        # Limit to top results
        final_findings = unique_findings[:5]
        final_citations = unique_citations[:5]
        
        # Combine summaries and critiques
        final_summary = "\n\n".join(all_summaries)
        final_critique = "\n\n".join(all_critiques)
        
        total_duration = time.time() - analysis_start
        total_calls = _api_call_counter - initial_call_count
        
        logger.info(f"[CONSOLIDATED_ANALYSIS_COMPLETE] Total Gemini API calls: {total_calls}, Total duration: {total_duration:.2f}s")
        logger.info(f"Generated summary: {len(final_summary)} chars, critique: {len(final_critique)} chars, findings: {len(final_findings)}, citations: {len(final_citations)}")
        
        return {
            "summary": final_summary,
            "critique": final_critique,
            "key_findings": final_findings,
            "citations": final_citations
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
