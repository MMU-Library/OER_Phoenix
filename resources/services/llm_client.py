import json
import logging
from dataclasses import dataclass
from typing import Any, Dict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    raw: Dict[str, Any]
    text: str


class LLMClient:
    def __init__(self) -> None:
        self.base_url = getattr(settings, "LOCAL_LLM_URL", "http://localhost:11434")
        self.model_name = getattr(settings, "LOCAL_LLM_MODEL", "deepseek-r1:32b")
        self.timeout = getattr(settings, "LOCAL_LLM_TIMEOUT", 20)

    def complete(self, prompt: str, max_tokens: int = 512) -> LLMResponse:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "stream": False,
        }
        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("response") or data.get("text") or ""
        return LLMResponse(raw=data, text=text.strip())

    def complete_json(self, prompt: str, max_tokens: int = 512) -> Dict[str, Any]:
        response = self.complete(prompt, max_tokens=max_tokens)
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            logger.warning("LLM did not return valid JSON, falling back to empty dict.")
            return {}