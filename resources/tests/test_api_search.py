from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from resources.models import OERSource, OERResource
from resources.services.search_engine import SearchResult, OERSearchEngine
from unittest.mock import MagicMock


class _DummyModel:
    def encode(self, texts, show_progress_bar=False):
        # return fixed-size zero vectors matching embedding dim used in model
        return [[0.0] * 384 for _ in texts]


class APISearchTests(TestCase):
    def setUp(self):
        self.client = self.client
        # Patch the heavy embedding model so tests don't download it.
        # Note: search_engine imported `get_embedding_model` at module import time,
        # so patch the reference in that module as well.
        patcher = patch('resources.services.search_engine.get_embedding_model', return_value=_DummyModel())
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_empty_query_returns_empty(self):
        url = reverse('resources:api_search')
        resp = self.client.get(url + '?q=')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('results', data)
        self.assertEqual(data['results'], [])

    def test_search_returns_results(self):
        source = OERSource.objects.create(name='Test Source', source_type='API')
        resource = OERResource.objects.create(
            title='Test Title',
            description='A short description for test',
            url='http://example.com',
            source=source
        )

        sr = SearchResult(
            resource=resource,
            similarity_score=0.9,
            quality_boost=0.1,
            final_score=1.0,
            match_reason='test'
        )

        with patch.object(OERSearchEngine, 'semantic_search', return_value=[sr]):
            url = reverse('resources:api_search')
            resp = self.client.get(url + '?q=test')
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn('results', data)
            self.assertEqual(len(data['results']), 1)
            item = data['results'][0]
            self.assertEqual(item['id'], resource.id)
            self.assertEqual(item['title'], resource.title)
