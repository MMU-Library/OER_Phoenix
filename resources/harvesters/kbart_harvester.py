"""
KBART harvester
Parses KBART (tab-separated) files and creates/updates OERResource rows.

Usage: instantiate KBARTHarvester and call `harvest_from_path(source, path_or_url)`
"""
from __future__ import annotations

import csv
import io
import logging
from typing import Optional

import requests

from django.utils import timezone

from resources.models import OERResource, HarvestJob

logger = logging.getLogger(__name__)


class KBARTHarvester:
    """Simple KBART parser that maps common KBART columns to OERResource fields.

    This is intentionally conservative: it will attempt to match by `url` first,
    then by `title`+`source` to avoid creating duplicates.
    """

    # common KBART column names we expect (lowercased)
    TITLE_COLS = ["publication_title", "title", "article_title"]
    URL_COLS = ["title_url", "title_url", "online_identifier", "url"]
    AUTHOR_COLS = ["first_author", "first_editor", "first_author"]
    PUBLISHER_COLS = ["publisher_name", "publisher"]
    ISBN_COLS = ["print_identifier", "print_isbn", "isbn"]
    ONLINE_ID_COLS = ["online_identifier", "doi"]
    TYPE_COLS = ["publication_type", "publication_type" ]

    def __init__(self):
        self.session = requests.Session()

    def _open(self, path_or_url: str) -> io.StringIO:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            r = self.session.get(path_or_url, timeout=30)
            r.raise_for_status()
            text = r.text
        else:
            with open(path_or_url, "r", encoding="utf-8") as fh:
                text = fh.read()
        return io.StringIO(text)

    def _get_first(self, row: dict, keys: list[str]) -> Optional[str]:
        for k in keys:
            v = row.get(k)
            if v:
                return v.strip()
        # try case-insensitive fallback
        for k, v in row.items():
            if k.lower() in [x.lower() for x in keys] and v:
                return v.strip()
        return None

    def _infer_resource_type(self, row: dict) -> str:
        v = self._get_first(row, self.TYPE_COLS)
        if not v:
            return "other"
        v = v.lower()
        if "monograph" in v or "book" in v:
            return "book"
        if "article" in v or "journal" in v:
            return "article"
        return "other"

    def harvest_from_path(self, source, path_or_url: str) -> HarvestJob:
        """Harvest KBART rows from a local path or URL and attach them to `source`.

        Returns the created HarvestJob instance with counters populated.
        """
        job = HarvestJob.objects.create(source=source, status="running", started_at=timezone.now())
        created = updated = skipped = failed = 0
        try:
            fh = self._open(path_or_url)
            # KBART is tab-separated with header row
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                job.pages_processed += 1
                try:
                    title = self._get_first(row, self.TITLE_COLS) or ""
                    url = self._get_first(row, self.URL_COLS) or self._get_first(row, self.ONLINE_ID_COLS) or ""
                    author = self._get_first(row, self.AUTHOR_COLS) or ""
                    publisher = self._get_first(row, self.PUBLISHER_COLS) or ""
                    isbn = self._get_first(row, self.ISBN_COLS) or ""
                    normalised_type = self._infer_resource_type(row)

                    # find existing resource by URL first
                    resource = None
                    if url:
                        try:
                            resource = OERResource.objects.get(url=url, source=source)
                        except OERResource.DoesNotExist:
                            resource = None

                    if not resource and title:
                        resource_qs = OERResource.objects.filter(title=title, source=source)
                        if resource_qs.exists():
                            resource = resource_qs.first()

                    defaults = {
                        "title": title or url or "(untitled)",
                        "description": row.get("coverage", "") or row.get("notes", "") or "",
                        "url": url or "",
                        "author": author,
                        "publisher": publisher,
                        "isbn": isbn,
                        "normalised_type": normalised_type,
                    }

                    if resource:
                        for k, v in defaults.items():
                            if v:
                                setattr(resource, k, v)
                        resource.updated_at = timezone.now()
                        resource.save()
                        updated += 1
                    else:
                        resource = OERResource.objects.create(source=source, **defaults)
                        created += 1

                    job.resources_found += 1
                except Exception as e:
                    logger.exception("Failed to process KBART row: %s", e)
                    job.resources_failed += 1
                    failed += 1
            # done
            job.resources_created = created
            job.resources_updated = updated
            job.resources_skipped = skipped
            job.resources_failed = failed
            job.status = "completed" if failed == 0 else ("partial" if created or updated else "failed")
            job.completed_at = timezone.now()
            job.save()
            # update source counts
            source.total_harvested = source.total_harvested + job.resources_created
            source.last_harvest_at = timezone.now()
            source.save()
            return job
        except Exception:
            job.status = "failed"
            job.error_message = "Unexpected error during KBART harvest"
            job.error_details = {"exc": "see logs"}
            job.completed_at = timezone.now()
            job.save()
            raise

    def harvest_from_fileobj(self, source, fileobj) -> HarvestJob:
        """Harvest from an uploaded file-like object (Django UploadedFile).

        Reads content and processes as KBART TSV.
        """
        text = None
        # Django InMemoryUploadedFile or TemporaryUploadedFile
        try:
            # fileobj may be InMemoryUploadedFile; ensure text
            if hasattr(fileobj, 'read'):
                # If fileobj provides bytes, decode
                raw = fileobj.read()
                if isinstance(raw, bytes):
                    text = raw.decode('utf-8')
                else:
                    text = str(raw)
            else:
                text = str(fileobj)
        finally:
            # Reset pointer if possible
            try:
                fileobj.seek(0)
            except Exception:
                pass

        fh = io.StringIO(text or "")
        # Reuse harvest_from_path logic by reading from fh directly
        job = HarvestJob.objects.create(source=source, status="running", started_at=timezone.now())
        created = updated = skipped = failed = 0
        try:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                job.pages_processed += 1
                try:
                    title = self._get_first(row, self.TITLE_COLS) or ""
                    url = self._get_first(row, self.URL_COLS) or self._get_first(row, self.ONLINE_ID_COLS) or ""
                    author = self._get_first(row, self.AUTHOR_COLS) or ""
                    publisher = self._get_first(row, self.PUBLISHER_COLS) or ""
                    isbn = self._get_first(row, self.ISBN_COLS) or ""
                    normalised_type = self._infer_resource_type(row)

                    resource = None
                    if url:
                        try:
                            resource = OERResource.objects.get(url=url, source=source)
                        except OERResource.DoesNotExist:
                            resource = None

                    if not resource and title:
                        resource_qs = OERResource.objects.filter(title=title, source=source)
                        if resource_qs.exists():
                            resource = resource_qs.first()

                    defaults = {
                        "title": title or url or "(untitled)",
                        "description": row.get("coverage", "") or row.get("notes", "") or "",
                        "url": url or "",
                        "author": author,
                        "publisher": publisher,
                        "isbn": isbn,
                        "normalised_type": normalised_type,
                    }

                    if resource:
                        for k, v in defaults.items():
                            if v:
                                setattr(resource, k, v)
                        resource.updated_at = timezone.now()
                        resource.save()
                        updated += 1
                    else:
                        resource = OERResource.objects.create(source=source, **defaults)
                        created += 1

                    job.resources_found += 1
                except Exception as e:
                    logger.exception("Failed to process KBART row: %s", e)
                    job.resources_failed += 1
                    failed += 1

            job.resources_created = created
            job.resources_updated = updated
            job.resources_skipped = skipped
            job.resources_failed = failed
            job.status = "completed" if failed == 0 else ("partial" if created or updated else "failed")
            job.completed_at = timezone.now()
            job.save()

            source.total_harvested = source.total_harvested + job.resources_created
            source.last_harvest_at = timezone.now()
            source.save()
            return job
        except Exception:
            job.status = "failed"
            job.error_message = "Unexpected error during KBART harvest"
            job.error_details = {"exc": "see logs"}
            job.completed_at = timezone.now()
            job.save()
            raise
