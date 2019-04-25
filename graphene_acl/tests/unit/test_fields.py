import graphene
import pytest
from ...fields import AclField, acl_field_type


class FooEnum(graphene.Enum):
    FOO = "foo"
    BAR = "bar"
    FOOBAR = "foobar"


def classifier(root, info, *args, **kwargs):
    permissions = info.context.jwt.permissions

    if "foo" in permissions:
        return "foo"
    elif "bar" in permissions:
        return "bar"

    return None


def enum_classifier(root, info, foo, *args, **kwargs):
    if foo in [FooEnum.FOO]:
        return foo
    elif foo in [FooEnum.BAR, FooEnum.FOOBAR]:
        return foo


def has_permissions(permissions):
    def validator(root, info, *args, **kwars):
        user_perms = info.context.jwt.permissions
        if any([permission in user_perms for permission in permissions]):
            return True
        raise Exception(f"Not authorized to query field {info.field_name}")

    return validator


def test_AclField_validator_success(mocker):
    field = AclField(
        graphene.String,
        acl_validator=has_permissions(["foo", "bar"]),
        resolver=lambda root, info: "name",
    )

    resolver = field.get_resolver(None)
    mock_info = mocker.MagicMock()
    mock_info.context.jwt.permissions = ["foo"]

    result = resolver(None, mock_info)

    assert result == "name"

    mock_info.context.jwt.permissions = ["bar"]

    result = resolver(None, mock_info)

    assert result == "name"

    mock_info.context.jwt.permissions = []

    try:
        result = resolver(None, mock_info)
        assert False, "Failed to raise expected exception"
    except Exception:
        assert True


def test_AclField_classifier_success(mocker):
    field = AclField(graphene.String, acl_classifier=classifier)

    @field.resolve("foo")
    def foo_resolver(root, info, *args, **kwargs):
        return "foo"

    @field.resolve("bar")
    def bar_resolver(root, info, *args, **kwargs):
        return "bar"

    @field.resolve()
    def default_resolver(root, info, *args, **kwargs):
        return "default"

    resolver = field.get_resolver(None)

    mock_info = mocker.MagicMock()
    mock_info.context.jwt.permissions = ["foo"]

    result = resolver(None, mock_info)

    assert result == "foo"

    mock_info.context.jwt.permissions = ["bar"]

    result = resolver(None, mock_info)

    assert result == "bar"

    mock_info.context.jwt.permissions = []

    result = resolver(None, mock_info)

    assert result == "default"


def test_AclField_enum_classifier_success(mocker):
    field = AclField(
        graphene.String,
        foo=graphene.Argument(FooEnum),
        acl_classifier=enum_classifier,
    )

    @field.resolve(FooEnum.FOO)
    def foo_resolver(root, info, *args, **kwargs):
        return "foo"

    @field.resolve(FooEnum.BAR)
    def bar_resolver(root, info, *args, **kwargs):
        return "bar"

    @field.resolve(FooEnum.FOOBAR.value)
    def default_resolver(root, info, *args, **kwargs):
        return "foobar"

    resolver = field.get_resolver(None)

    mock_info = mocker.MagicMock()

    result = resolver(None, mock_info, "foo")

    assert result == "foo"

    result = resolver(None, mock_info, FooEnum.FOO)

    assert result == "foo"

    result = resolver(None, mock_info, FooEnum.FOO.value)

    assert result == "foo"

    result = resolver(None, mock_info, "bar")

    assert result == "bar"

    result = resolver(None, mock_info, FooEnum.BAR)

    assert result == "bar"

    result = resolver(None, mock_info, "foobar")

    assert result == "foobar"

    result = resolver(None, mock_info, FooEnum.FOOBAR.value)

    assert result == "foobar"

    result = resolver(None, mock_info, "RABOOF")

    assert result is None


class CustomField(graphene.Field):
    def _resolver(self, parent_resolver, root, info, *args, **kwargs):
        response = parent_resolver(root, info, *args, **kwargs)
        if not response:
            return response
        return response + "bar"

    def get_resolver(self, parent_resolver):
        from functools import partial

        resolver = super(CustomField, self).get_resolver(parent_resolver)
        return partial(self._resolver, resolver)


def test_acl_field_type(mocker):
    AclCustomField = acl_field_type("AclCustomField", CustomField)

    field = AclCustomField(
        graphene.String,
        acl_validator=has_permissions(["foo"]),
        resolver=lambda root, info: "foo",
    )

    resolver = field.get_resolver(None)
    mock_info = mocker.MagicMock()
    mock_info.context.jwt.permissions = ["foo"]

    result = resolver(None, mock_info)

    assert result == "foobar"

    mock_info.context.jwt.permissions = ["bar"]

    with pytest.raises(Exception):
        resolver(None, mock_info)
