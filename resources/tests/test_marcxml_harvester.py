import unittest
from types import SimpleNamespace
from unittest.mock import patch

from resources.harvesters.marcxml_harvester import MARCXMLHarvester


class FakeResp:
    def __init__(self, content=None, status_code=200):
        self.content = content.encode('utf-8') if isinstance(content, str) else content
        self.status_code = status_code


class TestMARCXMLHarvester(unittest.TestCase):

    @patch('resources.harvesters.utils.request_with_retry')
    def test_marcxml_parses_basic_record(self, mock_req):
        xml = '''<?xml version="1.0"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
  <record>
    <leader>00000nam a2200000 a 4500</leader>
    <controlfield tag="008">200101s2020    xxu||||| |||| 00| 0 eng  </controlfield>
    <datafield tag="245" ind1="1" ind2="0"><subfield code="a">Test Book Title</subfield></datafield>
    <datafield tag="100" ind1=" " ind2=" "><subfield code="a">Doe, John</subfield></datafield>
    <datafield tag="260" ind1=" " ind2=" "><subfield code="b">Example Publisher</subfield></datafield>
    <datafield tag="856" ind1="4" ind2="0"><subfield code="u">https://example.org/book</subfield></datafield>
  </record>
</collection>'''
        mock_req.return_value = FakeResp(content=xml)
        src = SimpleNamespace(marcxml_url='https://dummy.marcxml')
        harv = MARCXMLHarvester(src)
        records = harv.fetch_and_process_records()
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r['title'], 'Test Book Title')
        self.assertEqual(r['url'], 'https://example.org/book')
        self.assertIn('Doe, John', r['author'])
        self.assertEqual(r['publisher'], 'Example Publisher')
        self.assertEqual(r['resource_type'], 'book')


if __name__ == '__main__':
    unittest.main()
