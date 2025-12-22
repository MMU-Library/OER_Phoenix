# resources/services/metadata_enricher.py

import logging
from dataclasses import dataclass
from typing import List, Optional

from django.conf import settings
from django.utils.text import Truncator

from resources.models import OERResource
from resources.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    resource: OERResource
    updated_fields: List[str]
    skipped: bool
    error: Optional[str] = None


def _basic_keyword_extraction(text: str, max_keywords: int = 8) -> List[str]:
    if not text:
        return []
    stopwords = {"the", "and", "for", "with", "this", "that", "from", "into", "about", "using"}
    words: List[str] = []
    for raw in text.replace("\n", " ").split():
        w = "".join(ch for ch in raw if ch.isalnum() or ch in "-_/").strip().lower()
        if len(w) < 4 or w in stopwords:
            continue
        if w not in words:
            words.append(w)
    return words[:max_keywords]


def _build_llm_prompt(resource: OERResource) -> str:
    title = resource.title or "Untitled resource"
    description = resource.description or ""
    resource_type = resource.resource_type or "learning resource"
    subject = resource.subject or ""
    level = resource.level or ""
    language = resource.language or "Unknown"

    desc_short = Truncator(description).chars(400)

    parts = [
        f"Title: {title}",
        f"Type: {resource_type}",
        f"Subject: {subject}" if subject else "",
        f"Level: {level}" if level else "",
        f"Language: {language}",
        "",
        "Existing description:",
        desc_short or "(no description provided)",
        "",
        (
            "Act as a librarian creating discovery metadata for an Open Educational Resource. "
            "Based ONLY on the information above, produce improved metadata. "
            "Return ONLY valid JSON with keys: "
            "description (string), keywords (list of strings), subjects (list of strings), language (string or null)."
        ),
    ]
    return "\n".join(p for p in parts if p)


def _try_llm_metadata(resource: OERResource) -> dict:
    """
    Attempt to use the local LLM; raise or return {} on failure.

    Controlled by ENABLE_LLM_ENRICHMENT.
    """
    if not getattr(settings, "ENABLE_LLM_ENRICHMENT", True):
        return {}

    client = LLMClient()
    prompt = _build_llm_prompt(resource)
    return client.complete_json(prompt=prompt, max_tokens=512)


def enrich_resource_metadata(resource: OERResource) -> EnrichmentResult:
    """
    Try LLM-based enrichment if available; otherwise fall back to heuristics.

    Only fills missing/weak fields; never overwrites clearly good values.
    """
    updated_fields: List[str] = []

    try:
        title = resource.title or ""
        description = resource.description or ""

        # Skip if already rich
        if (
            description
            and len(description) > 120
            and resource.keywords
            and resource.subject
        ):
            return EnrichmentResult(resource=resource, updated_fields=[], skipped=True)

        data: dict = {}
        try:
            data = _try_llm_metadata(resource)
        except Exception as e:
            logger.warning(
                "LLM enrichment failed for resource %s, falling back to heuristics: %s",
                getattr(resource, "id", "?"),
                e,
            )
            data = {}

        # Start from current values or LLM output
        new_description = (data.get("description") or "").strip()
        new_keywords = data.get("keywords") or []
        new_subjects = data.get("subjects") or []
        new_language = (data.get("language") or "").strip()

        # Fallbacks if LLM produced nothing useful
        if not new_description:
            clean_description = description.strip()
            if not clean_description and title:
                res_type = resource.resource_type or "learning resource"
                clean_description = f"{title} – {res_type} for teaching and learning."
            new_description = Truncator(clean_description).chars(600) if clean_description else ""

        if not new_keywords:
            base_text = f"{title} {description}"
            new_keywords = _basic_keyword_extraction(base_text)

        if not new_subjects:
            base_text = f"{title} {description}"
            new_subjects = _basic_keyword_extraction(base_text, max_keywords=3)

        # Apply conservative updates
        if new_description and (not resource.description or len(resource.description) < 60):
            resource.description = new_description
            updated_fields.append("description")

        if new_keywords and not resource.keywords:
            resource.keywords = ", ".join(new_keywords)
            updated_fields.append("keywords")

        if new_subjects and not resource.subject:
            resource.subject = " / ".join(new_subjects)[:255]
            updated_fields.append("subject")

        if new_language and not resource.language:
            resource.language = new_language[:50]
            updated_fields.append("language")

        if updated_fields:
            resource.save(update_fields=updated_fields)

        return EnrichmentResult(resource=resource, updated_fields=updated_fields, skipped=False)

    except Exception as e:
        logger.error("Metadata enrichment failed for resource %s: %s", getattr(resource, "id", "?"), e)
        return EnrichmentResult(resource=resource, updated_fields=[], skipped=False, error=str(e))


def enrich_queryset(qs) -> List[EnrichmentResult]:
    return [enrich_resource_metadata(res) for res in qs]


def enrich_resource_with_extracted_text(resource: OERResource, text: str) -> EnrichmentResult:
    """
    Enrich resource using a snippet of extracted text (preferable to short descriptions).
    """
    updated_fields: List[str] = []
    try:
        if not text:
            return EnrichmentResult(resource=resource, updated_fields=[], skipped=True)

        # Build prompt that includes an excerpt of the extracted text
        excerpt = Truncator(text).chars(4000)
        client = LLMClient()
        prompt_parts = [
            f"Title: {resource.title}",
            f"URL: {resource.url}",
            "",
            "Passage from resource:",
            excerpt,
            "",
            (
                "Act as a librarian. Based on the passage above, produce improved metadata. "
                "Return ONLY valid JSON with keys: description (string), keywords (list), subjects (list), language (string or null)."
            ),
        ]
        prompt = "\n".join(p for p in prompt_parts if p)

        data = {}
        try:
            data = client.complete_json(prompt=prompt, max_tokens=1024)
        except Exception as e:
            logger.warning("LLM call failed during extracted-text enrichment for %s: %s", getattr(resource, 'id', '?'), e)
            data = {}

        new_description = (data.get('description') or '').strip()
        new_keywords = data.get('keywords') or []
        new_subjects = data.get('subjects') or []
        new_language = (data.get('language') or '').strip()

        # Apply conservative updates
        if new_description and (not resource.description or len(resource.description) < 120):
            resource.description = new_description
            updated_fields.append('description')

        if new_keywords and not resource.keywords:
            resource.keywords = new_keywords
            updated_fields.append('keywords')

        if new_subjects and not resource.subject:
            resource.subject = " / ".join(new_subjects)[:255]
            updated_fields.append('subject')

        if new_language and not resource.language:
            resource.language = new_language[:50]
            updated_fields.append('language')

        if updated_fields:
            resource.save(update_fields=updated_fields)

        return EnrichmentResult(resource=resource, updated_fields=updated_fields, skipped=False)

    except Exception as e:
        logger.exception('Extracted-text enrichment failed for %s: %s', getattr(resource, 'id', '?'), e)
        return EnrichmentResult(resource=resource, updated_fields=[], skipped=False, error=str(e))
