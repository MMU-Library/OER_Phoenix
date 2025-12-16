# resources/services/subject_enrichment.py
from typing import List
from resources.models import OERResource
from resources.services.ai_utils import get_chat_model  # adjust to your actual helper

CONTROLLED_SUBJECTS = [
    "Education", "Sociology", "Mathematics", "Statistics", "Computer Science",
    "Research Methods", "Biology", "Business", "Psychology", "Humanities",
]

def suggest_subjects_for_resource(resource: OERResource) -> List[str]:
    """Return 1–3 broad subjects from CONTROLLED_SUBJECTS."""
    model = get_chat_model()
    existing = ", ".join(resource.subjects_raw or []) if isinstance(resource.subjects_raw, list) else str(resource.subjects_raw or "")
    prompt = (
        "You are helping classify open educational resources into broad subject areas.\n"
        f"Title: {resource.title}\n"
        f"Description: {(resource.description or '')[:800]}\n"
        f"Existing subjects: {existing}\n"
        f"Choose 1–3 subjects from this controlled list only: {', '.join(CONTROLLED_SUBJECTS)}.\n"
        "Return them as a comma-separated list, no explanations."
    )
    text = model.generate(prompt)  # adapt to your AI wrapper
    parts = [p.strip() for p in str(text).split(",") if p.strip()]
    return [p for p in parts if p in CONTROLLED_SUBJECTS]
