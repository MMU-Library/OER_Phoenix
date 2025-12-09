# resources/services/fast_headings.py

import logging
from typing import List

import requests  # if you intend to hit the FAST API

logger = logging.getLogger(__name__)


def suggest_fast_headings_from_keywords(keywords: List[str]) -> List[dict]:
    """
    Given a list of topical keywords, return a small list of suggested FAST headings.

    This is intentionally thin; you can flesh out the actual API interaction later.
    """
    # Placeholder: structure only; implement real FAST lookup when ready.
    logger.info("FAST headings suggestion requested for keywords: %s", keywords)
    return []
