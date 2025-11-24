from django.test import TestCase
from django.urls import reverse

class SearchExportTests(TestCase):
    def test_export_without_results_redirects(self):
        resp = self.client.post(reverse('resources:search_export_talis'))
        self.assertEqual(resp.status_code, 302)

    def test_export_with_session_results_returns_csv(self):
        session = self.client.session
        session['last_search_results'] = [
            {'id': 1, 'title': 'Matched 1', 'url': 'http://x', 'final_score': 0.8, 'source': 'S'},
            {'id': 2, 'title': 'Matched 2', 'url': 'http://y', 'final_score': 0.7, 'source': 'S2'},
        ]
        session.save()

        resp = self.client.post(reverse('resources:search_export_talis'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn('Matched 1', content)
        self.assertIn('Matched 2', content)
