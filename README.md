# graphene-acl

The motivation for this library is to simplify access control protection for Graphene Fields. A common approach to ACL protection is through the use of a reusable permissions validation decorator. The problem is this is cumbersome for Graphene Fields that use the standard resolver. You are forced to write an unnecessary resolver function just to annotate it with your permissions validator. The second cumbersome problem this library addresses is ACL role based resolvers. Depending on the users role you might want to perform different business logic in order to retrieve the data they requested for a Graphene Field.

## Usage

### acl_classifier

The purpose of the classifier is to return a route key that will be used to determine which resolver function is used for resolving the field. The classifier function has access to all the arguments from the field resolver.

### acl_validator

The purpose of the validator is to authorize access to the field. This validation will occurr before classification routing happens. If authorization validation is different per classification route then you should not use this validator to enforce authorization access. Instead you should authorize at the specific classifier resolver definition.

### Example

```python
from graphene_acl import AclField
import graphene

def classifier(root, info, *args, **kwargs):
    if 'admin' in info.context.jwt.permissions:
        return 'admin'
    return None

def has_permissions(permissions):
    def validator(root, info, *args, **kwars):
        if (any([permission in info.context.jwt.permissions for permission in permissions])):
            return True
        raise AuthorizationError(f'Not authorized to query field {info.field_name}')

    return validator

class Foo(graphene.ObjectType):
    private_name = AclField(graphene.String, acl_classifier=classifier)
    restricted_name = AclField(graphene.String, acl_validator=has_permissions(['foo:name:read', 'admin']))

@Foo.private_name.resolve('admin')
def resolve_private_name__admin(root, info, *args, **kwargs):
    pass

@Foo.private_name.resolve()
def resolve_private_name__default(root, info):
    # Alternatively, authorization handling could be done by an acl_validator
    raise Error('Not Authorized')
```

## Development

### First time setup

-   Install Precommit hooks
-   `brew install pre-commit && pre-commit install && pre-commit install --install-hooks`
-   Install poetry: https://github.com/sdispater/poetry#installation
-   `curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python`
-   Install dependencies
-   `poetry install`
