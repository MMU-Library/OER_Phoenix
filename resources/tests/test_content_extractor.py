import unittest
from resources.services.content_extractor import extract_text_from_html


class ContentExtractorTests(unittest.TestCase):
    def test_extract_text_from_html_basic(self):
        html = """
        <html><head><title>Test</title><script>ignored()</script></head>
        <body><main><h1>Heading</h1><p>Paragraph one.</p><p>Paragraph two.</p></main></body></html>
        """
        text = extract_text_from_html(html)
        self.assertIn('Heading', text)
        self.assertIn('Paragraph one.', text)
        self.assertIn('Paragraph two.', text)


if __name__ == '__main__':
    unittest.main()
