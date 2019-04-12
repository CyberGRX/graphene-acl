import graphene

from ...fields import AclField


def classifier(root, info, *args, **kwargs):
    permissions = info.context.jwt.permissions

    if "foo" in permissions:
        return "foo"
    elif "bar" in permissions:
        return "bar"

    return None


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
