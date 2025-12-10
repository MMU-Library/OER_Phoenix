import logging
import io
from django.utils import timezone
from resources.harvesters.base_harvester import BaseHarvester

logger = logging.getLogger(__name__)


def _normalise_url(raw: str) -> str:
    """
    Return a safe external URL or empty string.

    - Only accept values starting with http:// or https://.
    - Everything else (ISBNs, ONIX filenames, bare IDs) is treated as missing.
    """
    if not raw:
        return ""
    raw = raw.strip()
    if raw.lower().startswith(("http://", "https://")):
        return raw
    return ""


class MARCXMLHarvester(BaseHarvester):
    """MARCXML harvester that uses `pymarc` when available for robust parsing,
    falling back to a lightweight ElementTree parser when not present.
    """

    def _get_marcxml_content(self):
        marcxml_url = getattr(self.source, 'marcxml_url', None)
        if not marcxml_url:
            raise ValueError('No MARCXML URL configured for source')

        resp = self.request('GET', marcxml_url, headers={'Accept': 'application/xml'})
        return resp.content if hasattr(resp, 'content') else resp

    def _parse_with_pymarc(self, content):
        try:
            from pymarc import parse_xml_to_array
        except Exception:
            return None

        try:
            records = []
            marc_records = parse_xml_to_array(io.BytesIO(content))
            for mr in marc_records:
                title = mr.title() if hasattr(mr, 'title') else ''

                # authors: gather 100 and 700 subfield a
                authors = []
                for f in mr.get_fields('100', '700'):
                    subs = f.get_subfields('a')
                    if subs:
                        authors.append(' '.join(subs))

                # publisher
                publisher = ''
                for tag in ('264', '260'):
                    for f in mr.get_fields(tag):
                        subs = f.get_subfields('b') or f.get_subfields('c')
                        if subs:
                            publisher = ' '.join(subs)
                            break
                    if publisher:
                        break

                # url - 856$u
                url = ''
                for f in mr.get_fields('856'):
                    us = f.get_subfields('u')
                    if us:
                        url = us[0]
                        break

                # isbn 020$a
                isbn = ''
                for f in mr.get_fields('020'):
                    isb = f.get_subfields('a')
                    if isb:
                        isbn = isb[0]
                        break

                # description 520$a
                description = ''
                for f in mr.get_fields('520'):
                    ds = f.get_subfields('a')
                    if ds:
                        description = ds[0]
                        break

                language = mr.language() if hasattr(mr, 'language') else ''

                records.append({
                    'title': title or isbn or 'Untitled',
                    # changed: only accept real http(s) URLs, never fall back to ISBN
                    'url': _normalise_url(url),
                    'description': description,
                    'author': ', '.join(authors) if authors else '',
                    'publisher': publisher,
                    'language': language or 'en',
                    'resource_type': 'book',
                })

            return records
        except Exception:
            logger.exception('pymarc parsing failed; falling back')
            return None

    def _parse_with_elementtree(self, content):
        # lightweight fallback simple parser
        try:
            from xml.etree import ElementTree as ET
            ns = {'marc': 'http://www.loc.gov/MARC21/slim'}
            root = ET.fromstring(content)
            records = []
            for rec_el in root.findall('.//marc:record', ns):
                def find_datafields(tag):
                    return rec_el.findall(f".//marc:datafield[@tag='{tag}']", ns)

                def subfield_text(df, code):
                    sf = df.find(f"marc:subfield[@code='{code}']", ns)
                    return ''.join(sf.itertext()).strip() if sf is not None else ''

                title = ''
                for df in find_datafields('245'):
                    title = subfield_text(df, 'a') or title
                    if title:
                        break

                authors = []
                for tag in ('100', '700'):
                    for df in find_datafields(tag):
                        name = subfield_text(df, 'a')
                        if name:
                            authors.append(name)

                publisher = ''
                for tag in ('264', '260'):
                    for df in find_datafields(tag):
                        pub = subfield_text(df, 'b') or subfield_text(df, 'c')
                        if pub:
                            publisher = pub
                            break
                    if publisher:
                        break

                url = ''
                for df in find_datafields('856'):
                    u = subfield_text(df, 'u')
                    if u:
                        url = u
                        break

                isbn = ''
                for df in find_datafields('020'):
                    i = subfield_text(df, 'a')
                    if i:
                        isbn = i
                        break

                description = ''
                for df in find_datafields('520'):
                    d = subfield_text(df, 'a')
                    if d:
                        description = d
                        break

                controlfield_008 = rec_el.find(".//marc:controlfield[@tag='008']", ns)
                language = ''
                if controlfield_008 is not None and controlfield_008.text and len(controlfield_008.text) >= 40:
                    language = controlfield_008.text[35:38]

                records.append({
                    'title': title or isbn or 'Untitled',
                    # changed: only accept real http(s) URLs, never fall back to ISBN
                    'url': _normalise_url(url),
                    'description': description,
                    'author': ', '.join(authors) if authors else '',
                    'publisher': publisher,
                    'language': language or 'en',
                    'resource_type': 'book',
                })

            return records
        except Exception:
            logger.exception('ElementTree MARCXML parsing failed')
            return []

    def fetch_and_process_records(self):
        content = self._get_marcxml_content()

        # Try pymarc first
        records = self._parse_with_pymarc(content)
        if records is None:
            # pymarc not available or failed - use ElementTree fallback
            records = self._parse_with_elementtree(content)

        return records or []

    def test_connection(self):
        """Test that the MARCXML URL is reachable and looks like MARCXML."""
        try:
            url = getattr(self.source, 'marcxml_url', None)
            if not url:
                return False
            # try a lightweight HEAD first
            try:
                resp = self.request('head', url, timeout=10, max_attempts=2)
                if getattr(resp, 'status_code', None) == 200:
                    ct = ''
                    try:
                        ct = resp.headers.get('content-type', '')
                    except Exception:
                        pass
                    if 'xml' in (ct or '').lower() or 'text' in (ct or '').lower():
                        return True
            except Exception:
                # fallback to GET and check content
                pass

            resp = self.request('get', url, timeout=15, max_attempts=2)
            if getattr(resp, 'status_code', None) != 200:
                return False
            content = resp.content if hasattr(resp, 'content') else resp
            if isinstance(content, (bytes, bytearray)):
                lower = content[:4096].lower()
                if b'<record' in lower or b'<collection' in lower or b'<marc' in lower:
                    return True
            else:
                txt = str(content).lower()
                if '<record' in txt or '<collection' in txt or '<marc' in txt:
                    return True
            return False
        except Exception:
            return False
