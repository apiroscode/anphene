import graphene


class MoneyRange(graphene.ObjectType):
    start = graphene.Int(description="Lower bound of a price range.")
    stop = graphene.Int(description="Upper bound of a price range.")

    class Meta:
        description = "Represents a range of monetary values."
