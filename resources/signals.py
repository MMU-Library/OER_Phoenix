from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OERResource
from .tasks import generate_embedding_for_resource



@receiver(post_save, sender=OERResource)
def enqueue_embedding_on_save(sender, instance, created, **kwargs):
    """When an OERResource is created or updated, enqueue a task to compute its embedding.

    If `content_embedding` is already present and the instance was not just created,
    we only enqueue if the field is empty (conservative behavior).
    """
    try:
        if created:
            # New resource -> compute embedding
            generate_embedding_for_resource.delay(instance.id)
        else:
            # Updated resource: compute only if missing embedding
            if not instance.content_embedding:
                generate_embedding_for_resource.delay(instance.id)
    except Exception:
        # Avoid raising from signals
        pass
