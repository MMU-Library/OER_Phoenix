from django.core.management.base import BaseCommand

from resources.ai_processing import get_retriever


class Command(BaseCommand):
    help = 'Reindex OERResource embeddings into the configured retriever (Qdrant if available).'

    def add_arguments(self, parser):
        parser.add_argument('--backend', choices=['qdrant', 'numpy'], default='qdrant')

    def handle(self, *args, **options):
        backend = options['backend']
        retriever = get_retriever(preferred=backend)
        if hasattr(retriever, 'reindex'):
            self.stdout.write(f'Reindexing using {retriever.__class__.__name__}...')
            retriever.reindex()
            self.stdout.write('Reindex completed.')
        else:
            self.stdout.write('Selected retriever does not support reindex().')
