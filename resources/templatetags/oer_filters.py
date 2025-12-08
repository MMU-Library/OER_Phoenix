from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def star_rating(score):
    """Convert 0-5 float to star rating HTML"""
    if not score or score <= 0:
        return mark_safe('<small class="text-muted">Not rated</small>')
    
    full_stars = int(score)
    half_star = (score - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)
    
    html = '<span class="text-warning" title="{:.1f}/5.0">{}{}{}</span>'.format(
        score,
        '★' * full_stars,
        '⯨' if half_star else '',
        '☆' * empty_stars
    )
    return mark_safe(html)


@register.filter
def language_badge(lang_code):
    """Return language badge HTML"""
    if not lang_code or lang_code == 'en':
        return ''
    
    lang_names = {
        'no': 'Norwegian',
        'da': 'Danish',
        'de': 'German',
        'fr': 'French',
        'es': 'Spanish',
        'sv': 'Swedish',
        'nl': 'Dutch',
        'it': 'Italian',
        'pt': 'Portuguese',
    }
    
    lang_name = lang_names.get(lang_code.lower(), lang_code.upper())
    html = f'<span class="badge bg-info text-dark" title="Resource in {lang_name}">{lang_code.upper()}</span>'
    return mark_safe(html)


@register.filter
def source_badge(source):
    """Return colored source badge"""
    source_colors = {
        'OAPEN': 'primary',
        'DOAB': 'success',
        'OER Commons': 'warning',
        'OpenStax': 'danger',
        'Skills Commons': 'secondary',
    }
    
    display_name = source.get_display_name() if hasattr(source, 'get_display_name') else str(source)
    
    # Match color by checking if any key is in display_name
    color = 'secondary'
    for key, col in source_colors.items():
        if key.lower() in display_name.lower():
            color = col
            break
    
    html = f'<span class="badge bg-{color}">{display_name}</span>'
    return mark_safe(html)


@register.filter
def match_reason_badge(reason):
    """Return badge indicating why result matched"""
    badges = {
        'semantic': ('<span class="badge bg-primary" title="AI semantic match">🤖 AI Match</span>', 'AI semantic understanding'),
        'keyword': ('<span class="badge bg-secondary" title="Keyword match">🔍 Keyword</span>', 'Keyword in title/description'),
        'hybrid': ('<span class="badge bg-success" title="Strong match (AI + Keyword)">🎯 Strong Match</span>', 'Both AI and keyword match'),
    }
    
    if not reason:
        return ''
    
    if '|' in reason or 'hybrid' in reason:
        return mark_safe(badges['hybrid'][0])
    elif 'semantic' in reason:
        return mark_safe(badges['semantic'][0])
    else:
        return mark_safe(badges['keyword'][0])


@register.simple_tag
def translate_button(resource):
    """Return a translate button for non-English resources"""
    if resource.is_non_english() and not resource.title_en:
        html = f'''
        <button class="btn btn-sm btn-outline-secondary translate-btn" 
                data-resource-id="{resource.id}" 
                data-title="{resource.title}"
                title="Translate title to English">
            <small>Translate title</small>
        </button>
        '''
        return mark_safe(html)
    return ''
