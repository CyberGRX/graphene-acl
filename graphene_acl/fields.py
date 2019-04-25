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
        super(AclField, self).__init__(*args, **kwargs)

    def get_resolver(self, parent_resolver):
        super_resolver = super(AclField, self).get_resolver(parent_resolver)
        resolver = partial(
            self._acl_router.resolver, super_resolver or self.resolver
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


def acl_field_type(name, WrappedField):
    def get_resolver(self, parent_resolver):
        acl_resolver = AclField.get_resolver(self, parent_resolver)
        return WrappedField.get_resolver(self, acl_resolver)

    return type(name, (WrappedField, AclField), {"get_resolver": get_resolver})
