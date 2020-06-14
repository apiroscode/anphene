from config.celery_app import app
from core.utils.images import create_thumbnails
from .models import Category


@app.task
def create_category_background_image_thumbnails(category_id: str):
    """Take a Product model and create the background image thumbnails for it."""
    create_thumbnails(
        pk=category_id,
        model=Category,
        size_set="background_images",
        image_attr="background_image",
    )
