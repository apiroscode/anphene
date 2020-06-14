from config.celery_app import app
from core.utils.images import create_thumbnails
from .models import Collection


@app.task
def create_collection_background_image_thumbnails(collection_id: str):
    """Take a Collection model and create the background image thumbnails for it."""
    create_thumbnails(
        pk=collection_id,
        model=Collection,
        size_set="background_images",
        image_attr="background_image",
    )
