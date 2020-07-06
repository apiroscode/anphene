from anphene.users.models import Address


class AddressValidation:
    @classmethod
    def validate_address(cls, info, data, instance=None):
        if not instance:
            instance = Address()
        data["sub_district"] = cls.get_node_or_error(info, data["sub_district"])
        address = cls.construct_instance(instance, data)
        cls.clean_instance(info, address)
        return instance
