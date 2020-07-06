import graphene

from ..attributes.schema import AttributeMutations, AttributeQueries
from ..categories.schema import CategoryMutations, CategoryQueries
from ..collections.schema import CollectionMutations, CollectionQueries
from ..discounts.schema import DiscountMutations, DiscountQueries
from ..menus.schema import MenuMutations, MenuQueries
from ..pages.schema import PageMutations, PageQueries
from ..products.schema import ProductMutations, ProductQueries
from ..regions.schema import RegionQueries
from ..site.schema import ShopMutations, ShopQueries
from ..suppliers.schema import SupplierMutations, SupplierQueries
from ..users.schema import UserMutations, UserQueries


class Query(
    AttributeQueries,
    CategoryQueries,
    CollectionQueries,
    DiscountQueries,
    MenuQueries,
    PageQueries,
    ProductQueries,
    RegionQueries,
    ShopQueries,
    SupplierQueries,
    UserQueries,
):
    pass


class Mutation(
    AttributeMutations,
    CategoryMutations,
    CollectionMutations,
    DiscountMutations,
    MenuMutations,
    PageMutations,
    ProductMutations,
    ShopMutations,
    SupplierMutations,
    UserMutations,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
