import graphene

from core.graph.fields import FilterInputConnectionField
from core.graph.utils import get_node_or_slug
from .filters import PageFilterInput
from .mutations import PageCreate, PageDelete, PageUpdate
from .mutations_bulk import PageBulkDelete, PageBulkPublish
from .resolvers import resolve_pages
from .sorters import PageSortingInput
from .types import Page


class PageQueries(graphene.ObjectType):
    page = graphene.Field(
        Page,
        id=graphene.Argument(graphene.ID, description="ID of the page.", required=True),
        description="Look up a page by ID or slug.",
    )
    pages = FilterInputConnectionField(
        Page,
        sort_by=PageSortingInput(description="Sort pages."),
        filter=PageFilterInput(description="Filtering options for pages."),
        description="List of the shop's pages.",
    )

    def resolve_page(self, info, id):
        return get_node_or_slug(info, id, Page)

    def resolve_pages(self, info, **kwargs):
        return resolve_pages(info, **kwargs)


class PageMutations(graphene.ObjectType):
    page_create = PageCreate.Field()
    page_update = PageUpdate.Field()
    page_delete = PageDelete.Field()
    page_bulk_publish = PageBulkPublish.Field()
    page_bulk_delete = PageBulkDelete.Field()
