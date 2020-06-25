from config.celery_app import app
from core.utils.images import create_thumbnails
from .models import ProductImage


@app.task
def create_product_thumbnails(image_id: str):
    print(image_id)
    """Take a ProductImage model and create thumbnails for it."""
    create_thumbnails(pk=image_id, model=ProductImage, size_set="products")
