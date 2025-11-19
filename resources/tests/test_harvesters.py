import unittest
from types import SimpleNamespace
from unittest.mock import patch

from resources.harvesters.csv_harvester import CSVHarvester
from resources.harvesters.api_harvester import APIHarvester
from resources.harvesters.oaipmh_harvester import OAIPMHHarvester


class FakeResp:
    def __init__(self, content=None, status_code=200, json_data=None):
        self.content = content.encode('utf-8') if isinstance(content, str) else content
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


class TestHarvestParsers(unittest.TestCase):

    @patch('resources.harvesters.utils.request_with_retry')
    def test_csv_parser_parses_rows(self, mock_req):
        csv_content = "title,url,description\nTest Title,https://example.org/test,desc\nSecond,https://example.org/2,desc2\n"
        mock_req.return_value = FakeResp(content=csv_content)
        src = SimpleNamespace(csv_url='https://dummy.csv')
        harv = CSVHarvester(src)
        records = harv.fetch_and_process_records()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['title'], 'Test Title')

    @patch('resources.harvesters.utils.request_with_retry')
    def test_api_parser_parses_json(self, mock_req):
        json_data = {'results': [{'title': 'API Title', 'url': 'https://api.example/1'}, {'title': 'T2', 'url': 'https://api.example/2'}]}
        mock_req.return_value = FakeResp(json_data=json_data)
        src = SimpleNamespace(api_endpoint='https://api.example', api_key=None, request_headers={}, request_params={})
        harv = APIHarvester(src)
        records = harv.fetch_and_process_records()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['title'], 'API Title')

    @patch('resources.harvesters.utils.request_with_retry')
    def test_oaipmh_parser_parses_xml(self, mock_req):
        xml = '''<?xml version="1.0"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
<ListRecords>
  <record>
    <metadata>
      <dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>OAIPMH Title</dc:title>
        <dc:identifier>https://oai.example/1</dc:identifier>
      </dc:dc>
    </metadata>
  </record>
</ListRecords>
</OAI-PMH>'''
        mock_req.return_value = FakeResp(content=xml)
        src = SimpleNamespace(oaipmh_url='https://oai.example', request_params={})
        harv = OAIPMHHarvester(src)
        records = harv.fetch_and_process_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['title'], 'OAIPMH Title')


if __name__ == '__main__':
    unittest.main()
