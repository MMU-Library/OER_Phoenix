"""
Enhanced OER Search Engine
Unified search system with semantic + keyword hybrid search,
quality-based ranking, and filtering capabilities
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from django.db.models import Q, F, FloatField, QuerySet
from django.db.models.functions import Cast
from pgvector.django import L2Distance, CosineDistance
from resources.models import OERResource
from resources.services.ai_utils import get_embedding_model
from resources.ai_processing import get_retriever
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Structured search result with scoring"""
    resource: OERResource
    similarity_score: float
    quality_boost: float
    final_score: float
    match_reason: str


class OERSearchEngine:
    """
    Unified search engine for OER resources
    Combines semantic similarity, keyword matching, and quality metrics
    """
    
    def __init__(self):
        self.embedding_model = get_embedding_model()
        self.similarity_threshold = 0.65  # Configurable threshold
        self.quality_weight = 0.3  # Weight for quality score in ranking
        self.keyword_boost = 0.15  # Boost for keyword matches
    
    def semantic_search(
        self, 
        query: str, 
        filters: Optional[Dict] = None,
        limit: int = 20,
        include_inactive: bool = False
    ) -> List[SearchResult]:
        """
        Enhanced semantic search with filtering capabilities
        
        Args:
            query: Natural language search query
            filters: Dictionary of filters (subject_area, educational_level, license, etc.)
            limit: Maximum number of results
            include_inactive: Whether to include inactive resources
            
        Returns:
            List of SearchResult objects with scoring details
        """
        try:
            # 1. Generate query embedding
            logger.info(f"Processing search query: {query}")
            query_embedding = self.embedding_model.encode([query])[0]
            # normalize to list for DB functions
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            
            # 2. Base queryset
            queryset = OERResource.objects.all()
            if not include_inactive:
                queryset = queryset.filter(is_active=True)
            
            # 3. Apply filters
            if filters:
                queryset = self._apply_filters(queryset, filters)
            
            # 4. Perform vector similarity search using retriever (Qdrant preferred)
            retriever = get_retriever(preferred=os.environ.get('PREFERRED_RETRIEVER', 'qdrant'))
            semantic_hits = retriever.get_similar_resources(query, k=limit * 2)

            # Map hits (resource, score) into SearchResult objects
            results = []
            for resource, sim_score in semantic_hits:
                # store similarity on resource for downstream scoring
                try:
                    resource.similarity = float(sim_score)
                except Exception:
                    resource.similarity = 0.0
                result = self._calculate_final_score(resource, query)
                results.append(result)
            
            # 7. Sort by final score and limit
            results.sort(key=lambda x: x.final_score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """
        Hybrid search combining semantic and keyword approaches
        """
        # Get semantic results
        semantic_results = self.semantic_search(query, filters, limit)
        
        # Get keyword results
        keyword_results = self._keyword_search(query, filters, limit)
        
        # Merge and deduplicate
        combined = self._merge_results(semantic_results, keyword_results, limit)
        return combined
    
    def _keyword_search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """
        Traditional keyword-based search as fallback
        """
        queryset = OERResource.objects.filter(is_active=True)
        
        # Apply filters
        if filters:
            queryset = self._apply_filters(queryset, filters)
        
        # Search in multiple fields
        keywords = query.lower().split()
        q_objects = Q()
        
        for keyword in keywords:
            q_objects |= (
                Q(title__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(keywords__icontains=keyword) |
                Q(subject__icontains=keyword)
            )
        
        queryset = queryset.filter(q_objects).distinct()
        
        # Convert to SearchResult objects
        results = []
        for resource in queryset[:limit]:
            # Calculate simple relevance score
            title_matches = sum(1 for kw in keywords if kw in resource.title.lower())
            desc_matches = sum(1 for kw in keywords if kw in resource.description.lower())
            keyword_score = (title_matches * 0.6 + desc_matches * 0.4) / len(keywords)
            
            result = SearchResult(
                resource=resource,
                similarity_score=keyword_score,
                quality_boost=resource.overall_quality_score / 5.0,
                final_score=keyword_score * 0.7 + (resource.overall_quality_score / 5.0) * 0.3,
                match_reason="keyword_match"
            )
            results.append(result)
        
        return results
    
    def _apply_filters(self, queryset: QuerySet, filters: Dict) -> QuerySet:
        """
        Apply faceted filters to queryset
        """
        # Map friendly filter names to actual model fields where possible
        # Accept both 'subject_area' and 'subject' as incoming filter keys
        field_map = {
            'subject_area': 'subject',
            'subject': 'subject',
            'educational_level': 'level',
            'level': 'level',
            'license': 'license',
            'source': 'source',
        }

        for key, val in filters.items():
            if key in ('subject_area', 'subject', 'educational_level', 'level', 'license', 'source'):
                model_field = field_map.get(key)
                if model_field and model_field in [f.name for f in OERResource._meta.get_fields()]:
                    if model_field == 'source':
                        queryset = queryset.filter(source=val)
                    else:
                        queryset = queryset.filter(**{f"{model_field}__iexact": val})

        # Numeric / boolean filters - only apply if model supports them
        if 'min_quality' in filters and hasattr(OERResource, 'overall_quality_score'):
            try:
                queryset = queryset.filter(overall_quality_score__gte=filters['min_quality'])
            except Exception:
                pass

        if 'peer_reviewed' in filters and filters['peer_reviewed'] and hasattr(OERResource, 'peer_review_status'):
            try:
                queryset = queryset.filter(peer_review_status__in=['peer_reviewed', 'faculty_reviewed', 'approved'])
            except Exception:
                pass

        if 'accessible' in filters and filters['accessible'] and hasattr(OERResource, 'accessibility_score'):
            try:
                queryset = queryset.filter(accessibility_score__gte=0.8)
            except Exception:
                pass

        if 'recently_updated' in filters and filters['recently_updated'] and hasattr(OERResource, 'updated_at'):
            from datetime import timedelta
            from django.utils import timezone
            cutoff = timezone.now() - timedelta(days=365)
            try:
                queryset = queryset.filter(updated_at__gte=cutoff)
            except Exception:
                pass
        
        return queryset
    
    def _apply_keyword_boost(self, queryset: QuerySet, query: str) -> QuerySet:
        """
        Boost results that match keywords in title/description
        """
        # This is primarily for ordering; actual boosting happens in final score
        return queryset.select_related().prefetch_related('faculty_reviews', 'course_mappings')
    
    def _calculate_final_score(self, resource: OERResource, query: str) -> SearchResult:
        """
        Calculate final ranking score with quality boosting
        """
        # Get base similarity score
        similarity_score = float(getattr(resource, 'similarity', 0))
        # Calculate quality boost (guard missing field)
        overall_quality = getattr(resource, 'overall_quality_score', 0.0) or 0.0
        try:
            quality_boost = (float(overall_quality) / 5.0) * self.quality_weight
        except Exception:
            quality_boost = 0.0
        
        # Check for keyword matches (additional boost)
        keyword_boost = 0
        query_lower = query.lower()
        if query_lower in resource.title.lower():
            keyword_boost += self.keyword_boost * 0.6
        if query_lower in resource.description.lower():
            keyword_boost += self.keyword_boost * 0.4
        
        # Calculate final score
        final_score = similarity_score + quality_boost + keyword_boost
        
        # Determine match reason
        match_reason = "semantic_match"
        if keyword_boost > 0:
            match_reason = "semantic_and_keyword"
        if getattr(resource, 'is_featured', False):
            final_score *= 1.1  # 10% boost for featured resources
            match_reason += "_featured"
        
        return SearchResult(
            resource=resource,
            similarity_score=similarity_score,
            quality_boost=quality_boost,
            final_score=final_score,
            match_reason=match_reason
        )
    
    def _merge_results(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        limit: int
    ) -> List[SearchResult]:
        """
        Merge and deduplicate semantic and keyword search results
        """
        # Create dict with resource ID as key
        merged = {}
        
        for result in semantic_results:
            merged[result.resource.id] = result
        
        for result in keyword_results:
            if result.resource.id in merged:
                # Boost score if found in both
                existing = merged[result.resource.id]
                existing.final_score = max(existing.final_score, result.final_score) * 1.15
                existing.match_reason = "hybrid_match"
            else:
                merged[result.resource.id] = result
        
        # Convert back to list and sort
        final_results = list(merged.values())
        final_results.sort(key=lambda x: x.final_score, reverse=True)
        
        return final_results[:limit]
    
    def get_facets(self, query: str = None) -> Dict:
        """
        Get available facets/filters for the current query
        """
        queryset = OERResource.objects.filter(is_active=True)
        
        if query:
            # TODO: Apply query filter if needed
            pass
        
        facets = {
            'subject_areas': list(
                queryset.exclude(subject='')
                .values_list('subject', flat=True)
                .distinct()
            ),
            'educational_levels': [choice[0] for choice in OERResource._meta.get_field('level').choices],
            'licenses': list(
                queryset.values_list('license', flat=True)
                .distinct()
            ),
            'sources': list(
                queryset.values_list('source__name', flat=True)
                .distinct()
            ),
        }
        
        return facets
    
    def search_by_course(
        self,
        course_code: str,
        institution: str = None
    ) -> List[SearchResult]:
        """
        Find resources already mapped to a specific course
        """
        from resources.models import CourseMapping
        
        queryset = CourseMapping.objects.filter(
            course_code=course_code,
            is_active=True
        )
        
        if institution:
            queryset = queryset.filter(institution=institution)
        
        results = []
        for mapping in queryset.select_related('resource'):
            result = SearchResult(
                resource=mapping.resource,
                similarity_score=mapping.match_confidence,
                quality_boost=mapping.resource.overall_quality_score / 5.0,
                final_score=mapping.match_confidence,
                match_reason="course_mapping"
            )
            results.append(result)
        
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results


class SearchAnalytics:
    """Track and analyze search patterns"""
    
    @staticmethod
    def log_search(query: str, user=None, results_count: int = 0, filters: Dict = None):
        """Log a search query for analytics"""
        from resources.models import SearchQuery
        import uuid
        
        SearchQuery.objects.create(
            query_text=query,
            user=user,
            results_count=results_count,
            filters_applied=filters or {},
            session_id=str(uuid.uuid4())
        )
    
    @staticmethod
    def log_resource_click(resource_id: int, user=None, search_query_id: int = None):
        """Log when a resource is clicked from search results"""
        from resources.models import SearchQuery, ResourceAccessLog
        
        if search_query_id:
            try:
                search_query = SearchQuery.objects.get(id=search_query_id)
                clicked = search_query.clicked_results
                if resource_id not in clicked:
                    clicked.append(resource_id)
                    search_query.clicked_results = clicked
                    search_query.save()
            except SearchQuery.DoesNotExist:
                pass
        
        # Also log access
        ResourceAccessLog.objects.create(
            resource_id=resource_id,
            user=user
        )
    
    @staticmethod
    def get_popular_searches(days: int = 30, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular search queries"""
        from resources.models import SearchQuery
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        cutoff = timezone.now() - timedelta(days=days)
        
        popular = SearchQuery.objects.filter(
            created_at__gte=cutoff
        ).values('query_text').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        return [(item['query_text'], item['count']) for item in popular]
