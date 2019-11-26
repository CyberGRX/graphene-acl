from logging import getLogger
from promise import Promise
from enum import Enum

logger = getLogger(__name__)


def _hash_keys(keys=None):
    if keys:
        if type(keys) in [list, tuple]:
            sorted_keys = sorted(keys)
            return tuple(sorted_keys)
        return str(keys)
    return keys


def _default_handler(root, info, *args, **kwargs):
    return None


class ResolverRouter(object):
    def __init__(self, classifier=None):
        self._handlers = {}
        self._classifier = classifier
        self._default_handler = None

    def register(self, handler, key=None):
        hashable_key = _hash_keys(key)
        if hashable_key:
            if isinstance(key, Enum):
                self._handlers[key.value] = handler
                self._handlers[key.name] = handler
                self._handlers[str(key)] = handler
            else:
                self._handlers[hashable_key] = handler
        else:
            self._default_handler = handler

    def _get_handler(self, root, info, *args, routing_key=None, **kwargs):
        handler = None

        if routing_key:
            routing_key_hashable = _hash_keys(routing_key)
            handler = self._handlers.get(routing_key_hashable, None)
            if not handler:
                logger.error(
                    "Missing resolver for {}.{} classifier {}".format(
                        self.__class__, info.field_name, routing_key_hashable
                    )
                )
        return handler or self._default_handler

    def _resolver(
        self, routing_key, parent_resolver, root, info, *args, **kwargs
    ):
        handler = None

        if routing_key:
            handler = self._get_handler(
                root, info, *args, routing_key=routing_key, **kwargs
            )

        if not handler:
            handler = self._default_handler or parent_resolver

        if handler:
            if Promise.is_thenable(handler):
                return Promise.resolve(handler(root, info, *args, **kwargs))

            return handler(root, info, *args, **kwargs)
        return None

    def resolver(self, parent_resolver, root, info, *args, **kwargs):
        routing_key = None
        if self._classifier:
            routing_key = self._classifier(root, info, *args, **kwargs)
            if Promise.is_thenable(routing_key):
                return Promise.resolve(routing_key).then(
                    lambda key: self._resolver(
                        key, parent_resolver, root, info, *args, **kwargs
                    )
                )
        return self._resolver(
            routing_key, parent_resolver, root, info, *args, **kwargs
        )
