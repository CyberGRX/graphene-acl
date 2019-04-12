from logging import getLogger
from graphene import Field
from functools import partial, wraps
from promise import Promise
from .routing import ResolverRouter

logger = getLogger(__name__)


class AclField(Field):
    def __init__(
        self, *args, acl_validator=None, acl_classifier=None, **kwargs
    ):
        self._acl_validator = acl_validator
        self._acl_router = ResolverRouter(acl_classifier)
        super().__init__(*args, **kwargs)

    def get_resolver(self, parent_resolver):
        resolver = partial(
            self._acl_router.resolver, self.resolver or parent_resolver
        )

        @wraps(resolver)
        def _resolver(root, info, *args, **kwargs):
            if self._acl_validator(root, info, *args, **kwargs):
                result = resolver(root, info, *args, **kwargs)
                if Promise.is_thenable(result):
                    return Promise.resolve(result)
                return result

        if self._acl_validator:
            return _resolver
        else:
            return resolver

    def resolve(self, route_key=None):
        def decorator(func):
            self._acl_router.register(func, route_key)
            return func

        return decorator
