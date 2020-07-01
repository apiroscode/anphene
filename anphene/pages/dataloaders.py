from core.graph.dataloader import DataLoader
from .models import Page
from ..core.permissions import PagePermissions


class PageByIdLoader(DataLoader):
    context_key = "page_by_id"

    def batch_load(self, keys):
        pages = Page.objects.visible_to_user(self.user, PagePermissions.MANAGE_PAGES).in_bulk(keys)
        return [pages.get(page_id) for page_id in keys]
