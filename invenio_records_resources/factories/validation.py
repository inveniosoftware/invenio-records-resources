import importlib

from invenio_records_resources.factories.errors import RecordTypeFactoryError


class Registered(type):

    @classmethod
    def register_in_module(cls, new_cls_instance):
        import invenio_records_resources.factories as factory_module
        setattr(factory_module, new_cls_instance.__name__, new_cls_instance)

    @classmethod
    def validate_cls(mcs, class_name):
        module = importlib.import_module("invenio_records_resources.factories")
        existing_cls = getattr(module, class_name, None)
        if existing_cls:
            raise RecordTypeFactoryError(
                f"Record type {class_name} already exists.")
