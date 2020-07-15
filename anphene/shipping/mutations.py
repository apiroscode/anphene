import graphene
from core.graph.mutations import BaseMutation
from .types import Courier, Waybill
from ..users.types import Address
from ..plugins.manager import get_plugins_manager


class FetchShippingInput(graphene.InputObjectType):
    address = graphene.ID(required=True, description="ID of address.")
    weight = graphene.Int(required=True, description="Total weight products.")


class FetchShippingCost(BaseMutation):
    couriers = graphene.List(Courier, description="List of couriers.")

    class Arguments:
        input = FetchShippingInput(required=True, description="Fields required to fetch shipping.")

    class Meta:
        description = "Fetch shipping cost based on plugin."

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        data = data.get("input")
        address = cls.get_node_or_error(info, data["address"], field="address", only_type=Address)
        weight = data.get("weight")
        couriers = get_plugins_manager().fetch_shipping_cost(address, weight)

        return cls(couriers=couriers)


class FetchWaybillInput(graphene.InputObjectType):
    waybill = graphene.String(required=True, description="Waybill.")
    courier_code = graphene.String(required=True, description="Courier from this waybill.")


class FetchWaybill(BaseMutation):
    waybill = graphene.Field(Waybill, description="Waybill information.")

    class Arguments:
        input = FetchWaybillInput(
            required=True, description="Fields required to fetch waybill info."
        )

    class Meta:
        description = "Fetch waybill histories."

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        data = data.get("input")
        waybill = data.get("waybill")
        courier_code = data.get("courier_code")
        waybill = get_plugins_manager().fetch_waybill(waybill, courier_code)

        return cls(waybill=waybill)
