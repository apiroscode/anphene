import graphene

from core.graph.fields import FilterInputConnectionField
from core.graph.utils import get_node_or_slug
from .filters import CategoryFilterInput
from .mutations import CategoryBulkDelete, CategoryCreate, CategoryDelete, CategoryUpdate
from .resolvers import resolve_categories
from .sorters import CategorySortingInput
from .types import Category


class CategoryQueries(graphene.ObjectType):
    category = graphene.Field(
        Category,
        id=graphene.Argument(graphene.ID, description="ID of the category.", required=True),
        description="Look up a category by ID or slug.",
    )
    categories = FilterInputConnectionField(
        Category,
        filter=CategoryFilterInput(description="Filtering options for categories."),
        sort_by=CategorySortingInput(description="Sort categories."),
        level=graphene.Argument(
            graphene.Int,
            description="Filter categories by the nesting level in the category tree.",
        ),
        description="List of the shop's categories.",
    )

    def resolve_category(self, info, id):
        return get_node_or_slug(info, id, Category)

    def resolve_categories(self, info, level=None, **kwargs):
        return resolve_categories(info, level=level, **kwargs)


class CategoryMutations(graphene.ObjectType):
    category_create = CategoryCreate.Field()
    category_update = CategoryUpdate.Field()
    category_delete = CategoryDelete.Field()
    category_bulk_delete = CategoryBulkDelete.Field()
