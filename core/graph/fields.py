import json
from functools import partial

import graphene
import graphene_django_optimizer as gql_optimizer
from django.core.exceptions import FieldError
from graphene_django.fields import DjangoConnectionField
from graphql.error import GraphQLError
from promise import Promise


def patch_pagination_args(field: DjangoConnectionField):
    """Add descriptions to pagination arguments in a connection field.

    By default Graphene's connection fields comes without description for pagination
    arguments. This functions patches those fields to add the descriptions.
    """
    field.args["first"].description = "Return the first n elements from the list."
    field.args["last"].description = "Return the last n elements from the list."
    field.args[
        "before"
    ].description = "Return the elements in the list that come before the specified cursor."
    field.args[
        "after"
    ].description = "Return the elements in the list that come after the specified cursor."


class BaseConnectionField(graphene.ConnectionField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        patch_pagination_args(self)


class BaseDjangoConnectionField(DjangoConnectionField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        patch_pagination_args(self)


class PrefetchingConnectionField(BaseDjangoConnectionField):
    @classmethod
    def connection_resolver(
        cls,
        resolver,
        connection,
        default_manager,
        queryset_resolver,
        max_limit,
        enforce_first_or_last,
        root,
        info,
        **args,
    ):

        # Disable `enforce_first_or_last` if not querying for `edges`.
        values = [field.name.value for field in info.field_asts[0].selection_set.selections]
        if "edges" not in values:
            enforce_first_or_last = False

        return super().connection_resolver(
            resolver,
            connection,
            default_manager,
            queryset_resolver,
            max_limit,
            enforce_first_or_last,
            root,
            info,
            **args,
        )


class FilterInputConnectionField(PrefetchingConnectionField):
    def __init__(self, *args, **kwargs):
        # FILTER
        self.filter_field_name = kwargs.pop("filter_field_name", "filter")
        self.filter_input = kwargs.get(self.filter_field_name)
        self.filterset_class = None
        if self.filter_input:
            self.filterset_class = self.filter_input.filterset_class

        # SORTER
        sort_by = kwargs.get("sort_by")
        self.sort_enum = None
        if sort_by:
            self.sort_enum = sort_by._meta.sort_enum
        super().__init__(*args, **kwargs)

    @classmethod
    def connection_resolver(
        cls,
        resolver,
        connection,
        default_manager,
        queryset_resolver,
        max_limit,
        enforce_first_or_last,
        filterset_class,
        filters_name,
        sort_enum,
        root,
        info,
        **args,
    ):
        sort_by = args.get("sort_by")
        # Disable `enforce_first_or_last` if not querying for `edges`.
        values = [field.name.value for field in info.field_asts[0].selection_set.selections]
        if "edges" not in values:
            enforce_first_or_last = False

        first = args.get("first")
        last = args.get("last")

        if enforce_first_or_last and not (first or last):
            raise GraphQLError(
                f"You must provide a `first` or `last` value to properly paginate "
                f"the `{info.field_name}` connection."
            )

        if max_limit:
            if first:
                assert first <= max_limit, (
                    "Requesting {} records on the `{}` connection exceeds the "
                    "`first` limit of {} records."
                ).format(first, info.field_name, max_limit)
                args["first"] = min(first, max_limit)

            if last:
                assert last <= max_limit, (
                    "Requesting {} records on the `{}` connection exceeds the "
                    "`last` limit of {} records."
                ).format(last, info.field_name, max_limit)
                args["last"] = min(last, max_limit)

        iterable = resolver(root, info, **args)

        if iterable is None:
            iterable = default_manager

        # gql_optimizer query
        iterable = gql_optimizer.query(iterable, info)
        if sort_by:
            try:
                custom_sort_by = getattr(sort_enum, f"qs_with_{sort_by['field']}", None)
                if custom_sort_by:
                    iterable = custom_sort_by(iterable)
                iterable = iterable.order_by(f"{sort_by['direction']}{sort_by['field']}")
            except FieldError:
                raise GraphQLError("Received sorter is invalid.")
        # thus the iterable gets refiltered by resolve_queryset
        # but iterable might be promise
        iterable = queryset_resolver(connection, iterable, info, args)

        on_resolve = partial(cls.resolve_connection, connection, args)

        filter_input = args.get(filters_name)

        if filter_input and filterset_class:
            instance = filterset_class(
                data=dict(filter_input), queryset=iterable, request=info.context
            )
            # Make sure filter input has valid values
            if not instance.is_valid():
                raise GraphQLError(json.dumps(instance.errors.get_json_data()))
            iterable = instance.qs

        if Promise.is_thenable(iterable):
            return Promise.resolve(iterable).then(on_resolve)
        return on_resolve(iterable)

    def get_resolver(self, parent_resolver):
        return partial(
            super().get_resolver(parent_resolver),
            self.filterset_class,
            self.filter_field_name,
            self.sort_enum,
        )
