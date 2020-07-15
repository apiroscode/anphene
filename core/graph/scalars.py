import graphene
from graphql.error import GraphQLError


class UUID(graphene.UUID):
    @staticmethod
    def serialize(uuid):
        return super(UUID, UUID).serialize(uuid)

    @staticmethod
    def parse_literal(node):
        try:
            return super(UUID, UUID).parse_literal(node)
        except ValueError as e:
            raise GraphQLError(str(e))

    @staticmethod
    def parse_value(value):
        try:
            return super(UUID, UUID).parse_value(value)
        except ValueError as e:
            raise GraphQLError(str(e))
