from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def star_rating(score):
    """Convert quality score to star rating display"""
    if not score or score == 0:
        return mark_safe('<span class="text-muted">Not rated</span>')
    
    stars = int(score)
    half_star = (score - stars) >= 0.5
    empty_stars = 5 - stars - (1 if half_star else 0)
    
    html = '<span class="text-warning">'
    html += '★' * stars
    if half_star:
        html += '½'
    html += '<span class="text-muted">' + '☆' * empty_stars + '</span>'
    html += f' <small>({score:.1f})</small></span>'
    return mark_safe(html)


@register.filter
def language_badge(language_code):
    """Display language badge for non-English resources"""
    if not language_code or language_code.lower() == 'en':
        return ''
    
    language_names = {
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'nl': 'Dutch',
        'pl': 'Polish',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ar': 'Arabic'
    }
    
    lang_name = language_names.get(language_code.lower(), language_code.upper())
    return mark_safe(f'<span class="badge bg-info">{lang_name}</span>')


@register.filter
def source_badge(source):
    """Display colored badge for resource source"""
    # Map sources to Bootstrap color classes
    source_colors = {
        'OAPEN': 'primary',
        'DOAB': 'success',
        'OpenStax': 'info',
        'OER Commons': 'warning',
        'MERLOT': 'secondary',
        'MIT OCW': 'danger'
    }
    
    source_name = source.display_name if hasattr(source, 'display_name') and source.display_name else source.name
    color = source_colors.get(source_name, 'secondary')
    
    return mark_safe(f'<span class="badge bg-{color}">{source_name}</span>')


@register.filter
def match_reason_badge(reason):
    """Display badge explaining why resource was matched"""
    reason_labels = {
        'semantic': ('Semantic Match', 'primary'),
        'title': ('Title Match', 'success'),
        'description': ('Description Match', 'info'),
        'keyword': ('Keyword Match', 'warning'),
        'combined': ('Combined Match', 'secondary')
    }
    
    label, color = reason_labels.get(reason.lower(), (reason, 'secondary'))
    return mark_safe(f'<span class="badge bg-{color}">{label}</span>')


@register.simple_tag
def translate_button(resource):
    """Display translation button for non-English resources"""
    if not resource or not hasattr(resource, 'needs_translation') or not resource.needs_translation():
        return ''
    
    return mark_safe(
        f'<button class="btn btn-sm btn-outline-secondary" '
        f'onclick="translateResource({resource.id})" title="Translate to English">'
        f'<i class="bi bi-translate"></i> Translate</button>'
    )


@register.filter
def link_type_button(resource):
    """
    Generate appropriate button text and icon based on link type.
    Detects PDFs, web pages, and other formats for librarian-friendly display.
    """
    if not resource or not hasattr(resource, 'url'):
        return mark_safe('<span class="btn btn-sm btn-secondary disabled">No Link</span>')
    
    url = resource.url.lower()
    format_field = resource.format.lower() if hasattr(resource, 'format') and resource.format else ''
    
    # Detect PDF downloads
    if '.pdf' in url or 'pdf' in format_field or url.endswith('.pdf'):
        icon = '📄'
        text = 'Download PDF'
        btn_class = 'btn-danger'
        title = 'Direct PDF download'
    
    # Detect EPUB/ebook formats
    elif '.epub' in url or 'epub' in format_field:
        icon = '📖'
        text = 'Download E-book'
        btn_class = 'btn-info'
        title = 'E-book format (EPUB)'
    
    # Detect video content
    elif any(vid in url or vid in format_field for vid in ['youtube.com', 'vimeo.com', 'video', '.mp4', '.webm']):
        icon = '🎬'
        text = 'View Video'
        btn_class = 'btn-dark'
        title = 'Video resource'
    
    # Detect DOI links (scholarly articles)
    elif 'doi.org' in url or 'dx.doi.org' in url:
        icon = '🔗'
        text = 'View Article (DOI)'
        btn_class = 'btn-success'
        title = 'Academic article via DOI'
    
    # Detect archive.org links
    elif 'archive.org' in url:
        icon = '📚'
        text = 'View on Archive.org'
        btn_class = 'btn-warning'
        title = 'Internet Archive resource'
    
    # Detect repository/institutional pages
    elif any(repo in url for repo in ['repository', 'oer', 'dspace', 'eprints']):
        icon = '🗃️'
        text = 'View in Repository'
        btn_class = 'btn-primary'
        title = 'Institutional repository'
    
    # Default: web page
    else:
        icon = '🌐'
        text = 'View Web Page'
        btn_class = 'btn-outline-primary'
        title = 'External web page'
    
    return mark_safe(
        f'<a href="{resource.url}" target="_blank" rel="noopener noreferrer" '
        f'class="btn btn-sm {btn_class}" title="{title}">'
        f'{icon} {text}</a>'
    )
