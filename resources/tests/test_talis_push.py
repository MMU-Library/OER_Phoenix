from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
import csv


class TalisPushTests(TestCase):
    def setUp(self):
        # Build a simple report in session format
        self.report = [
            {'original': {'title': 'Intro', 'author': 'A'}, 'matches': [{'id': 1, 'title': 'Match', 'url': 'http://x', 'final_score': 0.9, 'source': 'S'}]}
        ]

    def test_push_without_config(self):
        session = self.client.session
        session['talis_report'] = self.report
        session.save()

        resp = self.client.post(reverse('resources:talis_push'))
        # should redirect back to upload page
        self.assertEqual(resp.status_code, 302)

    @override_settings(TALIS_API_URL='http://example.local/api/push', TALIS_API_TOKEN='tok')
    def test_push_with_config_posts(self):
        session = self.client.session
        session['talis_report'] = self.report
        session.save()

        with patch('resources.tasks.talis_push_report.delay') as p:
            resp = self.client.post(reverse('resources:talis_push'))
            self.assertEqual(resp.status_code, 302)

        # Ensure a TalisPushJob was created
        from resources.models import TalisPushJob
        jobs = TalisPushJob.objects.all()
        self.assertEqual(jobs.count(), 1)
        job = jobs.first()
        self.assertEqual(job.status, 'pending')
