import csv
import io
import logging
from urllib.parse import urlparse
from resources.harvesters.utils import request_with_retry
from resources.harvesters.base_harvester import BaseHarvester


logger = logging.getLogger(__name__)


def _normalise_language(raw: str) -> str:
    """Normalise CSV language values to ISO 639-1 where possible."""
    if not raw:
        return "en"
    v = str(raw).strip().lower()
    if v in ("en", "eng", "english"):
        return "en"
    if v in ("fr", "fre", "fra", "french"):
        return "fr"
    if v in ("de", "ger", "deu", "german"):
        return "de"
    if v in ("es", "spa", "spanish"):
        return "es"
    return v


def _normalise_resource_type(raw_type: str) -> str:
    """Map CSV type strings into internal normalised_type values."""
    if not raw_type:
        return ""
    t = str(raw_type).strip().lower()
    if "chapter" in t or "section" in t or "part" in t:
        return "chapter"
    if "book" in t or "monograph" in t or "textbook" in t:
        return "book"
    if "article" in t or "journal" in t or "paper" in t:
        return "article"
    if "video" in t or "lecture" in t or "recording" in t:
        return "video"
    if "course" in t or "module" in t or "unit" in t:
        return "course"
    return "other"


class CSVHarvester(BaseHarvester):
    def __init__(self, source):
        super().__init__(source)
        self.config = self._get_config()

    def _get_config(self):
        return {
            "csv_url": getattr(self.source, "api_endpoint", None)
            or getattr(self.source, "csv_url", None),
            "headers": getattr(self.source, "request_headers", {}) or {},
            "params": getattr(self.source, "request_params", {}) or {},
        }

    def test_connection(self):
        cfg = self._get_config()
        try:
            resp = request_with_retry(
                "get",
                cfg["csv_url"],
                headers=cfg.get("headers", {}),
                timeout=10,
                max_attempts=3,
            )
            if resp.status_code != 200:
                logger.warning(
                    "CSV test connection returned status %s for %s",
                    resp.status_code,
                    cfg["csv_url"],
                )
            return resp.status_code == 200
        except Exception:
            return False

    def _flexible_csv_reader(self, content):
        # Try to sniff dialect, fallback to excel
        try:
            sample = content[:8192]
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
        except Exception:
            dialect = csv.excel
        text_io = io.StringIO(content)
        reader = csv.DictReader(text_io, dialect=dialect)
        return list(reader)

    def fetch_and_process_records(self):
        cfg = self._get_config()
        url = cfg["csv_url"]
        headers = cfg.get("headers", {}) or {}
        params = cfg.get("params", {}) or {}

        try:
            resp = self.request(
                "get", url, headers=headers, params=params, timeout=30, max_attempts=4
            )
        except Exception as e:
            logger.error(f"CSV fetch failed: {e}")
            raise

        try:
            # decode content
            content = resp.content.decode("utf-8", errors="replace")
            rows = self._flexible_csv_reader(content)
        except Exception as e:
            # Log helpful debug info: status and content-type
            ct = ""
            try:
                ct = resp.headers.get("content-type", "")
            except Exception:
                pass
            logger.error(
                "CSV parse failed: %s; status=%s; content-type=%s; url=%s",
                e,
                getattr(resp, "status_code", None),
                ct,
                url,
            )
            raise

        records = []
        for r in rows:
            # best-effort mapping
            title = r.get("title") or r.get("name") or r.get("Title")
            url_val = (
                r.get("url")
                or r.get("link")
                or r.get("URL")
                or r.get("identifier")
            )
            desc = r.get("description") or r.get("summary")
            license_val = r.get("license") or r.get("rights") or r.get("License")
            publisher = r.get("publisher") or r.get("provider") or r.get("Publisher")
            author = (
                r.get("author")
                or r.get("creator")
                or r.get("owner")
                or r.get("Author")
            )
            lang_raw = (
                r.get("language")
                or r.get("Language")
                or r.get("lang")
            )
            type_raw = (
                r.get("resource_type")
                or r.get("type")
                or r.get("Type")
            )

            # NEW: subject / keywords mapping
            subject = (
                r.get("subject")
                or r.get("Subject")
                or r.get("subjects")
                or r.get("Subjects")
                or r.get("keywords")
                or r.get("Keywords")
                or r.get("category")
            )

            if not title and not url_val:
                continue

            records.append(
                {
                    "title": title,
                    "url": url_val,
                    "description": desc,
                    "license": license_val or "",
                    "publisher": publisher or "",
                    "author": author or "",
                    "language": _normalise_language(lang_raw or "en"),
                    "resource_type": type_raw or "",
                    "normalised_type": _normalise_resource_type(type_raw or ""),
                    "subject": subject or "",
                }
            )

        return records
