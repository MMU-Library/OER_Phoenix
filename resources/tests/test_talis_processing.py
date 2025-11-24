from django.test import TestCase
from django.urls import reverse
from io import BytesIO, StringIO
import csv
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch


class TalisProcessingTests(TestCase):
    def test_process_talis_csv_creates_report_and_download(self):
        # create a simple CSV in memory
        rows = [
            {'Title': 'Intro to Biology', 'Author': 'Jane Doe'},
            {'Title': 'Calculus I', 'Author': 'John Smith'},
        ]
        s = StringIO()
        writer = csv.DictWriter(s, fieldnames=['Title', 'Author'])
        writer.writeheader()
        writer.writerows(rows)
        csv_bytes = s.getvalue().encode('utf-8')
        upload = SimpleUploadedFile('test.csv', csv_bytes, content_type='text/csv')
        # Mock the search engine to return predictable matches
        class Dummy:
            def __init__(self, resource):
                self.resource = resource
                self.final_score = 0.9
                self.match_reason = 'semantic'

        class Res:
            def __init__(self, id, title):
                self.id = id
                self.title = title
                self.url = 'http://example.com'
                self.source = type('S', (), {'name': 'TestSource'})

        def fake_hybrid_search(query, filters=None, limit=5):
            return [Dummy(Res(1, 'Matched Resource'))]

        class DummyModel:
            def encode(self, texts, show_progress_bar=False):
                return [[0.0] * 384 for _ in texts]

        with patch('resources.services.search_engine.OERSearchEngine.hybrid_search', side_effect=fake_hybrid_search):
            with patch('resources.services.search_engine.get_embedding_model', return_value=DummyModel()):
                resp = self.client.post(reverse('resources:talis_process_csv'), {'csv_file': upload}, format='multipart')
            self.assertEqual(resp.status_code, 200)
            # now test download
            dl = self.client.get(reverse('resources:talis_report_download'))
            self.assertEqual(dl.status_code, 200)
            content = dl.content.decode('utf-8')
            self.assertIn('Matched Resource', content)
