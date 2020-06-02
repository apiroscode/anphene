from typing import Any, List

from django.http import HttpRequest
from promise import Promise
from promise.dataloader import DataLoader as BaseLoader


class DataLoader(BaseLoader):
    context_key = None
    context = None

    def __new__(cls, context: HttpRequest):
        key = cls.context_key
        if key is None:
            raise TypeError("Data loader %r does not define a context key" % (cls,))
        if not hasattr(context, "dataloaders"):
            context.dataloaders = {}
        if key not in context.dataloaders:
            context.dataloaders[key] = super().__new__(cls, context)
        loader = context.dataloaders[key]
        assert isinstance(loader, cls)
        return loader

    def __init__(self, context):
        if self.context != context:
            self.context = context
            self.user = context.user
            super().__init__()

    def batch_load_fn(self, keys):
        results = self.batch_load(keys)
        if not isinstance(results, Promise):
            return Promise.resolve(results)
        return results

    def batch_load(self, keys: List[Any]):
        raise NotImplementedError()
