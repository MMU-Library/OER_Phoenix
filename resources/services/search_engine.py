"""
Enhanced OER Search Engine
Unified search system with semantic + keyword hybrid search,
quality-based ranking, and filtering capabilities
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from django.db.models import Q, QuerySet
from resources.models import OERResource
from resources.services.ai_utils import get_embedding_model
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Structured search result with scoring"""
    resource: OERResource
    similarity_score: float = 0.0
    quality_boost: float = 0.0
    final_score: float = 0.0
    match_reason: str = ""

class OERSearchEngine:
    """
    Unified search engine for OER resources,
    using semantic similarity, keyword matching, and quality metrics.
    """
    def __init__(self):
        self.embedding_model = get_embedding_model()
        self.similarity_threshold = 0.45
        self.quality_weight = 0.3
        self.keyword_weight = 0.7

    def _get_resource_quality_score(self, resource: OERResource) -> float:
        # Primary: field on model
        score = getattr(resource, 'overall_quality_score', None)
        if score is not None:
            return float(score)
        # Fallback: check for JSONField, e.g., quality_scores
        if hasattr(resource, 'quality_scores'):
            val = resource.quality_scores.get('overall', 0.0)
            return float(val) if val else 0.0
        return 0.0

    def _cosine_similarity(self, a: Any, b: Any) -> float:
        # Convert to arrays and compute numpy-cosine
        a = np.array(a).astype(float)
        b = np.array(b).astype(float)
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def semantic_search(
        self, query: str, filters: Optional[Dict] = None, limit: int = 20, include_inactive: bool = False
    ) -> List[SearchResult]:
        try:
            logger.info(f"AI Search: Query = '{query}'")
            query_embedding = self.embedding_model.encode([query])[0]
            # Candidates with valid embeddings only
            qs = OERResource.objects.all()
            if not include_inactive:
                qs = qs.filter(is_active=True)
            if filters:
                qs = self._apply_filters(qs, filters)
            candidates = [r for r in qs if getattr(r, "content_embedding", None) is not None]
            logger.info(f"AI Search: {len(candidates)} resources with embeddings")
            results = []
            for res in candidates:
                emb = res.content_embedding
                if not isinstance(emb, (list, np.ndarray)):
                    emb = list(emb) if hasattr(emb, 'tolist') else emb
                try:
                    sim = self._cosine_similarity(query_embedding, emb)
                except Exception as e:
                    logger.warning(f"Cosine similarity error for resource {res.id}: {e}")
                    sim = 0.0
                quality_score = self._get_resource_quality_score(res)
                quality_boost = (quality_score / 5.0) * self.quality_weight
                final = sim + quality_boost
                results.append(SearchResult(
                    resource=res,
                    similarity_score=sim,
                    quality_boost=quality_boost,
                    final_score=final,
                    match_reason="semantic"
                ))
            results.sort(key=lambda x: x.final_score, reverse=True)
            return results[:limit]
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    def _keyword_search(
        self, query: str, filters: Optional[Dict] = None, limit: int = 20
    ) -> List[SearchResult]:
        qs = OERResource.objects.filter(is_active=True)
        if filters:
            qs = self._apply_filters(qs, filters)
        keywords = query.lower().split()
        qobj = Q()
        for kw in keywords:
            qobj |= (
                Q(title__icontains=kw) |
                Q(description__icontains=kw) |
                Q(keywords__icontains=kw) |
                Q(subject__icontains=kw)
            )
        qs = qs.filter(qobj).distinct()
        results = []
        for res in qs[:limit]:
            title_hits = sum(1 for kw in keywords if kw in res.title.lower())
            desc_hits = sum(1 for kw in keywords if kw in res.description.lower())
            score = (title_hits * 0.6 + desc_hits * 0.4) / max(1, len(keywords))
            quality_score = self._get_resource_quality_score(res)
            quality_boost = (quality_score / 5.0) * self.quality_weight
            final = score * self.keyword_weight + quality_boost
            results.append(SearchResult(
                resource=res,
                similarity_score=score,
                quality_boost=quality_boost,
                final_score=final,
                match_reason="keyword"
            ))
        return results

    def hybrid_search(
        self, query: str, filters: Optional[Dict] = None, limit: int = 20
    ) -> List[SearchResult]:
        semantic_hits = self.semantic_search(query, filters, limit)
        keyword_hits = self._keyword_search(query, filters, limit)
        # Deduplicate by resource ID, merge scores and reasons
        merged = {}
        for entry in (semantic_hits + keyword_hits):
            rid = getattr(entry.resource, "id", None)
            if rid in merged:
                merged[rid].final_score = max(merged[rid].final_score, entry.final_score)
                merged[rid].match_reason += "|hybrid"
            else:
                merged[rid] = entry
        sorted_results = sorted(merged.values(), key=lambda x: x.final_score, reverse=True)
        return sorted_results[:limit]

    def _apply_filters(self, qs: QuerySet, filters: Dict) -> QuerySet:
        field_map = {
            'subject_area': 'subject',
            'subject': 'subject',
            'educational_level': 'level',
            'level': 'level',
            'license': 'license',
            'source': 'source',
        }
        for key, val in filters.items():
            model_field = field_map.get(key)
            if model_field and model_field in [f.name for f in OERResource._meta.get_fields()]:
                if model_field == 'source':
                    qs = qs.filter(source=val)
                else:
                    qs = qs.filter(**{f"{model_field}__iexact": val})
        if 'min_quality' in filters:
            qs = qs.filter(overall_quality_score__gte=filters['min_quality'])
        return qs

    def get_facets(self, query: str = None) -> Dict:
        qs = OERResource.objects.filter(is_active=True)
        facets = {
            'subject_areas': list(qs.exclude(subject='').values_list('subject', flat=True).distinct()),
            'educational_levels': [choice[0] for choice in OERResource._meta.get_field('level').choices],
            'licenses': list(qs.values_list('license', flat=True).distinct()),
            'sources': list(qs.values_list('source__name', flat=True).distinct()),
        }
        return facets

    def search_by_course(
        self, course_code: str, institution: str = None
    ) -> List[SearchResult]:
        from resources.models import CourseMapping
        qs = CourseMapping.objects.filter(course_code=course_code, is_active=True)
        if institution:
            qs = qs.filter(institution=institution)
        results = []
        for mapping in qs.select_related('resource'):
            resource = mapping.resource
            quality_score = self._get_resource_quality_score(resource)
            results.append(SearchResult(
                resource=resource,
                similarity_score=mapping.match_confidence,
                quality_boost=(quality_score / 5.0) * self.quality_weight,
                final_score=mapping.match_confidence,
                match_reason="course_mapping"
            ))
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results
