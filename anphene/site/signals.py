from django_cleanup.signals import cleanup_pre_delete


def delete_versatileimagefield(**kwargs):
    kwargs["file"].delete_all_created_images()


cleanup_pre_delete.connect(delete_versatileimagefield)
