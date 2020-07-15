import graphene

from .mutations import FetchShippingCost, FetchWaybill


class ShippingMutations(graphene.ObjectType):
    fetch_shipping_cost = FetchShippingCost.Field()
    fetch_waybill = FetchWaybill.Field()
