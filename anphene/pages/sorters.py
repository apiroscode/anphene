import graphene

from core.graph.types import SortInputObjectType


class PageSortField(graphene.Enum):
    TITLE = "title"
    SLUG = "slug"

    @property
    def description(self):
        if self.name in PageSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort pages by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class PageSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = PageSortField
        type_name = "pages"
