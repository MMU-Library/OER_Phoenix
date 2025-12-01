# resources/services/talis.py

import os
import csv
import logging
from dataclasses import dataclass, field
from typing import List, Optional, TextIO

import requests
from django.conf import settings
from resources.models import OERResource

logger = logging.getLogger(__name__)

TALIS_API_URL = "https://rl.talis.com/3/"


class TalisClient:
    """
    Export-only client for pushing OERResource collections into Talis lists.
    """

    def __init__(self):
        self.tenant = os.getenv("TALIS_TENANT")
        self.client_id = os.getenv("TALIS_CLIENT_ID")
        self.client_secret = os.getenv("TALIS_CLIENT_SECRET")
        self.access_token = None

    def authenticate(self):
        url = "https://users.talis.com/oauth/tokens"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://rl.talis.com/3/",
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()
        self.access_token = response.json()["access_token"]
        return self.access_token

    def _headers(self):
        if not self.access_token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/vnd.api+json",
        }

    def create_reading_list(self, title, description, resources):
        """
        Create a Talis list and push a set of OERResource items into it.
        """
        headers = self._headers()

        list_data = {
            "data": {
                "type": "lists",
                "attributes": {
                    "title": title,
                    "description": description,
                    "visibility": "PUBLIC",
                },
            }
        }
        list_url = f"{TALIS_API_URL}{self.tenant}/lists"
        list_response = requests.post(list_url, json=list_data, headers=headers)
        list_response.raise_for_status()
        list_id = list_response.json()["data"]["id"]

        items_url = f"{TALIS_API_URL}{self.tenant}/lists/{list_id}/items"
        for resource in resources:
            item_data = {
                "data": {
                    "type": "items",
                    "attributes": {
                        "uri": resource.url,
                        "meta": {
                            "title": resource.title,
                            "abstract": (resource.description or "")[:500],
                        },
                    },
                }
            }
            item_response = requests.post(items_url, json=item_data, headers=headers)
            item_response.raise_for_status()

        return list_id


# ---- New: types + helpers for import/analysis ----

@dataclass
class TalisItem:
    position: int
    section: Optional[str]
    importance: Optional[str]
    item_type: Optional[str]
    title: str
    authors: Optional[str]
    isbn: Optional[str]
    doi: Optional[str]
    url: Optional[str]
    notes: Optional[str] = None


@dataclass
class TalisList:
    identifier: str
    title: Optional[str]
    module_code: Optional[str]
    academic_year: Optional[str]
    source_type: str        # "csv" or "api"
    items: List[TalisItem] = field(default_factory=list)
    raw_payload_ref: Optional[str] = None


def parse_csv_to_talis_list(file_obj: TextIO) -> TalisList:
    """
    CSV → TalisList normalisation for dashboard workflow A. [web:49][web:52]
    """
    reader = csv.DictReader(
        (line.decode("utf-8") if isinstance(line, bytes) else line for line in file_obj)
    )

    items: List[TalisItem] = []
    list_title: Optional[str] = None
    module_code: Optional[str] = None
    academic_year: Optional[str] = None

    for idx, row in enumerate(reader, start=1):
        title = (row.get("Title") or row.get("Item Title") or "").strip()
        if not title:
            continue

        items.append(
            TalisItem(
                position=idx,
                section=(row.get("Section") or "").strip() or None,
                importance=(row.get("Importance") or "").strip() or None,
                item_type=(row.get("Resource type") or row.get("Type") or "").strip() or None,
                title=title,
                authors=(row.get("Author") or row.get("Authors") or "").strip() or None,
                isbn=(row.get("ISBN") or "").strip() or None,
                doi=(row.get("DOI") or "").strip() or None,
                url=(row.get("Web address") or row.get("URL") or "").strip() or None,
                notes=(row.get("Note for Student") or row.get("Notes") or "").strip() or None,
            )
        )

        if not list_title:
            list_title = (row.get("List name") or row.get("Reading list") or "").strip() or None
        if not module_code:
            module_code = (row.get("Module code") or row.get("Course code") or "").strip() or None
        if not academic_year:
            academic_year = (row.get("Year") or row.get("Academic year") or "").strip() or None

    talis_list = TalisList(
        identifier="csv_import",
        title=list_title,
        module_code=module_code,
        academic_year=academic_year,
        source_type="csv",
        items=items,
    )
    logger.info("Parsed CSV into TalisList with %s items", len(items))
    return talis_list


def fetch_list_from_url(list_url: str) -> TalisList:
    """
    API/Linked Data → TalisList for dashboard workflow B. [web:44][web:45][web:38]
    """
    response = requests.get(list_url, timeout=15)
    response.raise_for_status()
    data = response.json()

    title = data.get("title") or data.get("name")
    module_code = None
    academic_year = None

    items: List[TalisItem] = []
    for idx, entry in enumerate(data.get("items", []), start=1):
        item_title = (entry.get("title") or entry.get("citation_title") or "").strip()
        if not item_title:
            continue

        identifiers = entry.get("identifiers") or {}
        items.append(
            TalisItem(
                position=idx,
                section=(entry.get("section") or "").strip() or None,
                importance=(entry.get("importance") or "").strip() or None,
                item_type=(entry.get("resource_type") or "").strip() or None,
                title=item_title,
                authors=(entry.get("authors") or "").strip() or None,
                isbn=(identifiers.get("isbn") or "").strip() or None,
                doi=(identifiers.get("doi") or "").strip() or None,
                url=(entry.get("url") or "").strip() or None,
                notes=(entry.get("note") or "").strip() or None,
            )
        )

    talis_list = TalisList(
        identifier=data.get("id") or list_url,
        title=title,
        module_code=module_code,
        academic_year=academic_year,
        source_type="api",
        items=items,
        raw_payload_ref=list_url,
    )
    logger.info("Fetched Talis list from API with %s items", len(items))
    return talis_list
