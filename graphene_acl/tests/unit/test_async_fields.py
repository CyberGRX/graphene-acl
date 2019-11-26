import graphene
import pytest
import asyncio
from ...fields import AclField


async def async_classifier(root, info, *args, **kwargs):
    permissions = info.context.jwt.permissions
    await asyncio.sleep(0.1)

    if "foo" in permissions:
        return "foo"
    elif "bar" in permissions:
        return "bar"

    return None


def classifier(root, info, *args, **kwargs):
    permissions = info.context.jwt.permissions

    if "foo" in permissions:
        return "foo"
    elif "bar" in permissions:
        return "bar"

    return None


async_classifier_field = AclField(
    graphene.String, acl_classifier=async_classifier
)
sync_classifier_field = AclField(graphene.String, acl_classifier=classifier)


@async_classifier_field.resolve("foo")
@sync_classifier_field.resolve("foo")
async def foo_resolver(root, info, *args, **kwargs):
    await asyncio.sleep(0.1)
    return "foo"


@async_classifier_field.resolve("bar")
@sync_classifier_field.resolve("bar")
def bar_resolver(root, info, *args, **kwargs):
    return "bar"


@async_classifier_field.resolve()
@sync_classifier_field.resolve()
def default_resolver(root, info, *args, **kwargs):
    return "default"


@pytest.mark.asyncio
async def test_AclField_async_classifier_success(mocker):
    info = mocker.MagicMock()

    resolver = async_classifier_field.get_resolver(None)

    info.context.jwt.permissions = ["foo"]

    result = await resolver(None, info)

    assert result == "foo"

    info.context.jwt.permissions = ["bar"]

    result = await resolver(None, info)

    assert result == "bar"

    info.context.jwt.permissions = []

    result = await resolver(None, info)

    assert result == "default"


@pytest.mark.asyncio
async def test_AclField_sync_classifier_success(mocker):
    info = mocker.MagicMock()
    resolver = sync_classifier_field.get_resolver(None)

    info.context.jwt.permissions = ["foo"]

    result = await resolver(None, info)

    assert result == "foo"

    info.context.jwt.permissions = ["bar"]

    result = resolver(None, info)

    assert result == "bar"

    info.context.jwt.permissions = []

    result = resolver(None, info)

    assert result == "default"
