import graphene
from graphene import relay

from . import models
from core.graph.connection import CountableDjangoObjectType
from ..pages.dataloaders import PageByIdLoader
from ..products.dataloaders import CategoryByIdLoader, CollectionByIdLoader
from .dataloaders import (
    MenuByIdLoader,
    MenuItemByIdLoader,
    MenuItemChildrenLoader,
    MenuItemsByParentMenuLoader,
)


class Menu(CountableDjangoObjectType):
    items = graphene.List(lambda: MenuItem)

    class Meta:
        description = (
            "Represents a single menu - an object that is used to help navigate "
            "through the store."
        )
        interfaces = [relay.Node]
        only_fields = ["id", "name"]
        model = models.Menu

    @staticmethod
    def resolve_items(root: models.Menu, info, **_kwargs):
        return MenuItemsByParentMenuLoader(info.context).load(root.id)


class MenuItem(CountableDjangoObjectType):
    children = graphene.List(lambda: MenuItem)
    url = graphene.String(description="URL to the menu item.")

    class Meta:
        description = (
            "Represents a single item of the related menu. Can store categories, "
            "collection or pages."
        )
        interfaces = [relay.Node]
        only_fields = [
            "id",
            "name",
            "parent",
            "category",
            "collection",
            "level",
            "menu",
            "page",
            "sort_order",
        ]
        model = models.MenuItem

    @staticmethod
    def resolve_category(root: models.MenuItem, info, **_kwargs):
        if root.category_id:
            return CategoryByIdLoader(info.context).load(root.category_id)
        return None

    @staticmethod
    def resolve_children(root: models.MenuItem, info, **_kwargs):
        return MenuItemChildrenLoader(info.context).load(root.id)

    @staticmethod
    def resolve_collection(root: models.MenuItem, info, **_kwargs):
        if root.collection_id:
            return CollectionByIdLoader(info.context).load(root.collection_id)
        return None

    @staticmethod
    def resolve_menu(root: models.MenuItem, info, **_kwargs):
        if root.menu_id:
            return MenuByIdLoader(info.context).load(root.menu_id)
        return None

    @staticmethod
    def resolve_parent(root: models.MenuItem, info, **_kwargs):
        if root.parent_id:
            return MenuItemByIdLoader(info.context).load(root.parent_id)
        return None

    @staticmethod
    def resolve_page(root: models.MenuItem, info, **kwargs):
        if root.page_id:
            return PageByIdLoader(info.context).load(root.page_id)
        return None
