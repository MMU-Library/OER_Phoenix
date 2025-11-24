from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.utils.html import strip_tags

from .services.search_engine import OERSearchEngine


class SearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    url = serializers.CharField(allow_null=True)
    similarity_score = serializers.FloatField()
    quality_boost = serializers.FloatField()
    final_score = serializers.FloatField()
    match_reason = serializers.CharField()
    snippet = serializers.CharField(allow_blank=True)


class SearchAPIView(APIView):
    """Simple DRF endpoint that returns `OERSearchEngine` results as JSON."""

    def get(self, request, format=None):
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({'results': []})

        try:
            limit = int(request.GET.get('limit', 20))
        except Exception:
            limit = 20

        # Basic filters support: expect a JSON-encoded filters param (optional)
        filters = None
        # TODO: add parsing of filters from request if needed

        engine = OERSearchEngine()
        results = engine.semantic_search(query, filters=filters, limit=limit)

        payload = []
        for r in results:
            snippet = ''
            try:
                snippet = strip_tags(getattr(r.resource, 'description', '') or '')[:300]
            except Exception:
                snippet = ''

            payload.append({
                'id': r.resource.id,
                'title': getattr(r.resource, 'title', ''),
                'url': getattr(r.resource, 'url', ''),
                'similarity_score': float(r.similarity_score),
                'quality_boost': float(r.quality_boost),
                'final_score': float(r.final_score),
                'match_reason': r.match_reason,
                'snippet': snippet,
            })

        serializer = SearchResultSerializer(payload, many=True)
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)
