import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from core.graph.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from . import models
from .enums import NavigationType
from .types import Menu, MenuItem
from ..categories import models as categories_models
from ..categories.types import Category
from ..collections import models as collections_models
from ..collections.types import Collection
from ..core.permissions import MenuPermissions, SitePermissions
from ..pages import models as pages_models
from ..pages.types import Page


class MenuItemMoveInput(graphene.InputObjectType):
    item_id = graphene.ID(description="The menu item ID to move.", required=True)
    parent_id = graphene.ID(
        description="ID of the parent menu. If empty, menu will be top level menu."
    )
    sort_order = graphene.Int(description="Sorting position of the menu item (from 0 to x).")


class MenuItemInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu item.")
    url = graphene.String(description="URL of the pointed item.")
    category = graphene.ID(description="Category to which item points.", name="category")
    collection = graphene.ID(description="Collection to which item points.", name="collection")
    page = graphene.ID(description="Page to which item points.", name="page")


class MenuItemCreateInput(MenuItemInput):
    name = graphene.String(description="Name of the menu item.", required=True)
    menu = graphene.ID(description="Menu to which item belongs.", name="menu", required=True)
    parent = graphene.ID(
        description="ID of the parent menu. If empty, menu will be top level menu.", name="parent",
    )


class MenuInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu.")


class MenuCreateInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu.", required=True)
    items = graphene.List(MenuItemInput, description="List of menu items.")


class MenuCreate(ModelMutation):
    class Arguments:
        input = MenuCreateInput(required=True, description="Fields required to create a menu.")

    class Meta:
        description = "Creates a new Menu."
        model = models.Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        items = []
        for item in cleaned_input.get("items", []):
            category = item.get("category")
            collection = item.get("collection")
            page = item.get("page")
            url = item.get("url")
            if len([i for i in [category, collection, page, url] if i]) > 1:
                raise ValidationError({"items": ValidationError("More than one item provided.")})

            if category:
                category = cls.get_node_or_error(info, category, field="items", only_type=Category)
                item["category"] = category
            elif collection:
                collection = cls.get_node_or_error(
                    info, collection, field="items", only_type=Collection
                )
                item["collection"] = collection
            elif page:
                page = cls.get_node_or_error(info, page, field="items", only_type=Page)
                item["page"] = page
            elif not url:
                raise ValidationError({"items": ValidationError("No menu item provided.")})
            items.append(item)

        cleaned_input["items"] = items
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        items = cleaned_data.get("items", [])
        for item in items:
            instance.items.create(**item)


class MenuUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu to update.")
        input = MenuInput(required=True, description="Fields required to update a menu.")

    class Meta:
        description = "Updates a menu."
        model = models.Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)


class MenuDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu to delete.")

    class Meta:
        description = "Deletes a menu."
        model = models.Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)


def _validate_menu_item_instance(cleaned_input: dict, field: str, expected_model):
    """Check if the value to assign as a menu item matches the expected model."""
    item = cleaned_input.get(field)
    if item:
        if not isinstance(item, expected_model):
            msg = (
                f"Enter a valid {expected_model._meta.verbose_name} ID "
                f"(got {item._meta.verbose_name} ID)."
            )
            raise ValidationError({field: ValidationError(msg)})


class MenuItemCreate(ModelMutation):
    class Arguments:
        input = MenuItemCreateInput(
            required=True,
            description=(
                "Fields required to update a menu item. Only one of `url`, `category`, "
                "`page`, `collection` is allowed per item."
            ),
        )

    class Meta:
        description = "Creates a new menu item."
        model = models.MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        _validate_menu_item_instance(cleaned_input, "page", pages_models.Page)
        _validate_menu_item_instance(cleaned_input, "collection", collections_models.Collection)
        _validate_menu_item_instance(cleaned_input, "category", categories_models.Category)

        items = [
            cleaned_input.get("page"),
            cleaned_input.get("collection"),
            cleaned_input.get("url"),
            cleaned_input.get("category"),
        ]
        items = [item for item in items if item is not None]
        if len(items) > 1:
            raise ValidationError("More than one item provided.")
        return cleaned_input


class MenuItemUpdate(MenuItemCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu item to update.")
        input = MenuItemInput(
            required=True,
            description=(
                "Fields required to update a menu item. Only one of `url`, `category`, "
                "`page`, `collection` is allowed per item."
            ),
        )

    class Meta:
        description = "Updates a menu item."
        model = models.MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        # Only one item can be assigned per menu item
        instance.page = None
        instance.collection = None
        instance.category = None
        instance.url = None
        return super().construct_instance(instance, cleaned_data)


class MenuItemDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu item to delete.")

    class Meta:
        description = "Deletes a menu item."
        model = models.MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)


class MenuItemMove(BaseMutation):
    menu = graphene.Field(Menu, description="Assigned menu to move within.")

    class Arguments:
        id = graphene.ID(description="The menu item ID to move.", required=True)
        parent_id = graphene.ID(
            description="ID of the parent menu. If empty, menu will be top level menu."
        )
        sort_order = graphene.Int(
            description="Sorting position index based on parent.", required=True
        )

    class Meta:
        description = "Moves items of menus."
        permissions = (MenuPermissions.MANAGE_MENUS,)

    @classmethod
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):
        id = data.get("id")
        parent = data.get("parent_id", None)
        sort_order = data.get("sort_order", 0)
        item = cls.get_node_or_error(info, id, field="id", only_type=MenuItem)
        menu = item.menu

        if parent:
            parent = cls.get_node_or_error(info, parent, field="id", only_type=MenuItem)
            item.parent = parent
            item.save()
            parent.refresh_from_db()
        else:
            item.parent = parent
            item.save()

        # resort order
        qs = (
            models.MenuItem.objects.filter(level=0, menu_id=menu.id)
            if parent is None
            else parent.get_children()
        )
        qs = list(qs)
        old_index = next((index for (index, d) in enumerate(qs) if d.id == item.id), None)
        qs.insert(sort_order, qs.pop(old_index))
        for idx, item in enumerate(qs):
            item.sort_order = idx
        models.MenuItem.objects.bulk_update(qs, ["sort_order"])
        menu.refresh_from_db()

        return MenuItemMove(menu=menu)


class AssignNavigation(BaseMutation):
    menu = graphene.Field(Menu, description="Assigned navigation menu.")

    class Arguments:
        menu = graphene.ID(description="ID of the menu.")
        navigation_type = NavigationType(
            description="Type of the navigation bar to assign the menu to.", required=True,
        )

    class Meta:
        description = "Assigns storefront's navigation menus."
        permissions = (MenuPermissions.MANAGE_MENUS, SitePermissions.MANAGE_SETTINGS)

    @classmethod
    def perform_mutation(cls, _root, info, navigation_type, menu=None):
        site_settings = info.context.site.settings
        menu = cls.get_node_or_error(info, menu, field="menu")

        prev_menu = None
        if navigation_type == NavigationType.MAIN:
            prev_menu = site_settings.top_menu
            site_settings.top_menu = menu
            site_settings.save(update_fields=["top_menu"])
        elif navigation_type == NavigationType.SECONDARY:
            prev_menu = site_settings.bottom_menu
            site_settings.bottom_menu = menu
            site_settings.save(update_fields=["bottom_menu"])

        if menu is not None and prev_menu:
            prev_menu.refresh_from_db()

        return AssignNavigation(menu=menu if menu is not None else prev_menu)
