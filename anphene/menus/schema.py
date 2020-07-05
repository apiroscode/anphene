import graphene

from core.graph.fields import FilterInputConnectionField
from .filters import MenuFilterInput, MenuItemFilterInput
from .mutations import (
    AssignNavigation,
    MenuCreate,
    MenuDelete,
    MenuItemCreate,
    MenuItemDelete,
    MenuItemMove,
    MenuItemUpdate,
    MenuUpdate,
)
from .mutations_bulk import MenuBulkDelete, MenuItemBulkDelete
from .resolvers import resolve_menu_items, resolve_menus
from .sorters import MenuItemSortingInput, MenuSortingInput
from .types import Menu, MenuItem


class MenuQueries(graphene.ObjectType):
    menu = graphene.Field(
        Menu,
        id=graphene.Argument(graphene.ID, description="ID of the menu.", required=True),
        description="Look up a navigation menu by ID or name.",
    )
    menus = FilterInputConnectionField(
        Menu,
        sort_by=MenuSortingInput(description="Sort menus."),
        filter=MenuFilterInput(description="Filtering options for menus."),
        description="List of the storefront's menus.",
    )
    menu_item = graphene.Field(
        MenuItem,
        id=graphene.Argument(graphene.ID, description="ID of the menu item.", required=True),
        description="Look up a menu item by ID.",
    )
    menu_items = FilterInputConnectionField(
        MenuItem,
        sort_by=MenuItemSortingInput(description="Sort menus items."),
        filter=MenuItemFilterInput(description="Filtering options for menu items."),
        description="List of the storefronts's menu items.",
    )

    def resolve_menu(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Menu)

    def resolve_menus(self, info, **kwargs):
        return resolve_menus(info, **kwargs)

    def resolve_menu_item(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, MenuItem)

    def resolve_menu_items(self, info, **kwargs):
        return resolve_menu_items(info, **kwargs)


class MenuMutations(graphene.ObjectType):
    assign_navigation = AssignNavigation.Field()

    menu_create = MenuCreate.Field()
    menu_update = MenuUpdate.Field()
    menu_delete = MenuDelete.Field()
    menu_bulk_delete = MenuBulkDelete.Field()

    menu_item_create = MenuItemCreate.Field()
    menu_item_update = MenuItemUpdate.Field()
    menu_item_delete = MenuItemDelete.Field()
    menu_item_move = MenuItemMove.Field()

    menu_item_bulk_delete = MenuItemBulkDelete.Field()
