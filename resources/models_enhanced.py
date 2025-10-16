"""
Enhanced OER Resource Models - Aligned with Educational Goals
This file contains the enhanced models to support:
- Quality assessment framework
- Course mapping system
- Faculty review functionality
- Educational context tracking
"""

from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# Choice definitions
REVIEW_STATUS_CHOICES = [
    ('pending', 'Pending Review'),
    ('in_review', 'In Review'),
    ('peer_reviewed', 'Peer Reviewed'),
    ('faculty_reviewed', 'Faculty Reviewed'),
    ('approved', 'Approved'),
]

EDUCATIONAL_LEVEL_CHOICES = [
    ('k12', 'K-12'),
    ('undergraduate', 'Undergraduate'),
    ('graduate', 'Graduate'),
    ('professional', 'Professional Development'),
    ('mixed', 'Mixed Levels'),
]

LICENSE_TYPE_CHOICES = [
    ('cc_by', 'CC BY'),
    ('cc_by_sa', 'CC BY-SA'),
    ('cc_by_nc', 'CC BY-NC'),
    ('cc_by_nc_sa', 'CC BY-NC-SA'),
    ('cc0', 'CC0 (Public Domain)'),
    ('other', 'Other Open License'),
]


class OERResource(models.Model):
    """Enhanced OER Resource model with quality metrics and educational context"""
    
    # Core Metadata
    title = models.CharField(max_length=500, db_index=True)
    description = models.TextField()
    url = models.URLField(unique=True, max_length=1000)
    license = models.CharField(max_length=100, choices=LICENSE_TYPE_CHOICES)
    source = models.CharField(max_length=100, db_index=True)  # OER Commons, OpenStax, etc.
    publisher = models.CharField(max_length=200, blank=True)
    
    # Educational Context
    subject_area = models.CharField(max_length=200, blank=True, db_index=True, 
                                   help_text="e.g., Mathematics, Biology, Computer Science")
    educational_level = models.CharField(max_length=100, choices=EDUCATIONAL_LEVEL_CHOICES, 
                                        blank=True, db_index=True)
    learning_objectives = models.TextField(blank=True, 
                                          help_text="Learning outcomes covered by this resource")
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for search")
    
    # Quality Metrics
    accessibility_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Automated accessibility compliance score (0-1)"
    )
    peer_review_status = models.CharField(
        max_length=50, 
        choices=REVIEW_STATUS_CHOICES, 
        default='pending',
        db_index=True
    )
    adoption_count = models.IntegerField(
        default=0, 
        help_text="Number of times this resource has been adopted by faculty"
    )
    metadata_quality_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Completeness and quality of metadata (0-1)"
    )
    overall_quality_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Calculated overall quality score (0-5)"
    )
    
    # Technical
    embedding = VectorField(dimensions=384, null=True, blank=True)  # 384 for MiniLM-L6-v2
    version = models.CharField(max_length=50, default="1.0")
    content_hash = models.CharField(max_length=64, blank=True, 
                                   help_text="SHA-256 hash for version tracking")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_verified = models.DateTimeField(null=True, blank=True,
                                        help_text="Last time URL was verified as working")
    
    # Administrative
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, 
                                     help_text="Highlighted as exemplary resource")
    csv_file = models.FileField(upload_to='csv_uploads/', null=True, blank=True)
    
    class Meta:
        verbose_name = "OER Resource"
        verbose_name_plural = "OER Resources"
        ordering = ['-overall_quality_score', '-adoption_count', '-created_at']
        indexes = [
            models.Index(fields=['subject_area', 'educational_level']),
            models.Index(fields=['is_active', 'overall_quality_score']),
            models.Index(fields=['source', 'last_updated']),
        ]
    
    def __str__(self):
        return self.title
    
    def calculate_metadata_quality(self):
        """Calculate metadata completeness score"""
        fields_to_check = [
            bool(self.title),
            bool(self.description and len(self.description) > 100),
            bool(self.subject_area),
            bool(self.educational_level),
            bool(self.learning_objectives),
            bool(self.keywords),
            bool(self.publisher),
        ]
        return sum(fields_to_check) / len(fields_to_check)
    
    def update_overall_quality_score(self):
        """Calculate overall quality score based on multiple factors"""
        # Weighted calculation
        weights = {
            'metadata_quality': 0.2,
            'accessibility': 0.2,
            'peer_review': 0.3,
            'adoption': 0.2,
            'faculty_reviews': 0.1,
        }
        
        # Convert peer review status to score
        review_scores = {
            'pending': 0,
            'in_review': 1,
            'peer_reviewed': 3,
            'faculty_reviewed': 4,
            'approved': 5,
        }
        
        # Normalize adoption count (cap at 100)
        normalized_adoption = min(self.adoption_count / 20.0, 5.0)
        
        # Get average faculty review score if available
        faculty_avg = 0
        if hasattr(self, 'faculty_reviews') and self.faculty_reviews.exists():
            faculty_avg = sum(r.average_score for r in self.faculty_reviews.all()) / self.faculty_reviews.count()
        
        # Calculate weighted score
        score = (
            (self.metadata_quality_score * 5 * weights['metadata_quality']) +
            (self.accessibility_score * 5 * weights['accessibility']) +
            (review_scores.get(self.peer_review_status, 0) * weights['peer_review']) +
            (normalized_adoption * weights['adoption']) +
            (faculty_avg * weights['faculty_reviews'])
        )
        
        self.overall_quality_score = round(score, 2)
        return self.overall_quality_score
    
    def save(self, *args, **kwargs):
        # Auto-calculate metadata quality score
        self.metadata_quality_score = self.calculate_metadata_quality()
        super().save(*args, **kwargs)


class CourseMapping(models.Model):
    """Map OER resources to university courses"""
    resource = models.ForeignKey(OERResource, on_delete=models.CASCADE, related_name='course_mappings')
    course_code = models.CharField(max_length=50, db_index=True, help_text="e.g., CS101, MATH200")
    course_title = models.CharField(max_length=300)
    institution = models.CharField(max_length=200, db_index=True)
    department = models.CharField(max_length=200, blank=True)
    
    # Mapping Quality
    match_confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="AI-calculated confidence in this mapping (0-1)"
    )
    manual_override = models.BooleanField(default=False, 
                                         help_text="Faculty manually confirmed this mapping")
    
    # Context
    mapped_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    mapped_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Course Mapping"
        verbose_name_plural = "Course Mappings"
        unique_together = ['resource', 'course_code', 'institution']
        ordering = ['-match_confidence', '-mapped_at']
    
    def __str__(self):
        return f"{self.course_code} ({self.institution}) → {self.resource.title}"


class FacultyReview(models.Model):
    """Faculty assessment and reviews of OER resources"""
    resource = models.ForeignKey(OERResource, on_delete=models.CASCADE, related_name='faculty_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Review Scores (1-5 scale)
    relevance_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How relevant is this to your course? (1-5)"
    )
    quality_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Overall content quality (1-5)"
    )
    accuracy_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Factual accuracy and up-to-date content (1-5)"
    )
    usability_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Ease of use and navigation (1-5)"
    )
    
    # Qualitative Feedback
    comments = models.TextField(blank=True)
    strengths = models.TextField(blank=True, help_text="What works well?")
    weaknesses = models.TextField(blank=True, help_text="What could be improved?")
    
    # Adoption Intent
    will_adopt = models.BooleanField(default=False, help_text="Will you use this in your course?")
    adoption_date = models.DateField(null=True, blank=True)
    course_context = models.CharField(max_length=300, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True, help_text="Share review with other faculty?")
    
    class Meta:
        verbose_name = "Faculty Review"
        verbose_name_plural = "Faculty Reviews"
        unique_together = ['resource', 'reviewer']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review of {self.resource.title} by {self.reviewer.username}"
    
    @property
    def average_score(self):
        """Calculate average of all numeric scores"""
        return (self.relevance_score + self.quality_score + 
                self.accuracy_score + self.usability_score) / 4.0


class SearchQuery(models.Model):
    """Track search queries for analytics and improvement"""
    query_text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Search Context
    filters_applied = models.JSONField(default=dict, blank=True)
    results_count = models.IntegerField(default=0)
    
    # User Interaction
    clicked_results = models.JSONField(default=list, blank=True, 
                                      help_text="IDs of resources clicked")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Search Query"
        verbose_name_plural = "Search Queries"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.query_text[:50]} ({self.created_at.strftime('%Y-%m-%d')})"


class ResourceAccessLog(models.Model):
    """Track resource access for analytics"""
    resource = models.ForeignKey(OERResource, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    session_id = models.CharField(max_length=100, blank=True)
    referrer = models.CharField(max_length=500, blank=True)
    
    class Meta:
        verbose_name = "Resource Access Log"
        verbose_name_plural = "Resource Access Logs"
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"{self.resource.title} accessed on {self.accessed_at.strftime('%Y-%m-%d %H:%M')}"
