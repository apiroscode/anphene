import graphene


class CourierService(graphene.ObjectType):
    service = graphene.String(description="Service name.")
    description = graphene.String(description="Description.")
    cost = graphene.Int(description="Cost.")
    etd = graphene.String(description="Estimate time delivery.")

    class Meta:
        description = "List all services from courier include cost."


class Courier(graphene.ObjectType):
    code = graphene.String(description="Courier code.")
    name = graphene.String(description="Courier name (verbose).")
    services = graphene.List(CourierService, description="List of services from this courier.")

    class Meta:
        description = "List all courier fetch based on manager."


class WaybillStatus(graphene.ObjectType):
    status = graphene.String(description="Status waybill.")
    receiver = graphene.String(description="Receiver order.")
    date = graphene.String(description="Status date.")

    class Meta:
        description = "Waybill status."


class WaybillHistory(graphene.ObjectType):
    date = graphene.String(description="History date.")
    description = graphene.String(description="History Description.")
    city = graphene.String(description="History city.")

    class Meta:
        description = "Waybill history."


class Waybill(graphene.ObjectType):
    status = graphene.Field(WaybillStatus, description="Waybill Status.")
    histories = graphene.List(WaybillHistory, description="Histories of waybill.")

    class Meta:
        description = "Waybill status and histories."
