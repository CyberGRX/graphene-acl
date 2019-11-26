# graphene-acl

The motivation for this library is to simplify access control protection for Graphene Fields. A common approach to ACL protection is through the use of a reusable permissions validation decorator. The problem is this is cumbersome for Graphene Fields that use the standard resolver. You are forced to write an unnecessary resolver function just to annotate it with your permissions validator. The second cumbersome problem this library addresses is ACL role based resolvers. Depending on the users role you might want to perform different business logic in order to retrieve the data they requested for a Graphene Field.

## Installation

```bash
$ pip install graphene-acl
```

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
    permissions = info.context.jwt.permissions

    if 'admin' in permissions:
        return 'admin'
    if 'perm1' in permissions and not 'perm2' in permissions:
        return 'perm1'
    if 'perm2' in permissions and not 'perm1' in permissions:
        return 'perm2'
    if 'perm2' in permissions and 'perm1' in permissions:
        return ['perm1', 'perm2']
    if 'perm3' in permissions:
        return 'perm3'
    if 'perm4' in permissions:
        return 'perm4'
    return None

def has_permissions(permissions):
    def validator(root, info, *args, **kwars):
        if (any([permission in info.context.jwt.permissions for permission in permissions])):
            return True
        raise AuthorizationError(f'Not authorized to query field {info.field_name}')

    return validator

class Foo(graphene.ObjectType):
    # Demonstrates simple routing based on an Admin classifier route key
    admin_field = AclField(graphene.String, acl_classifier=classifier)
    restricted_name = AclField(graphene.String, acl_validator=has_permissions(['foo:name:read', 'admin']))

    tenant_field = AclField(graphene.String, acl_classifier=classifier)

@Foo.admin_field.resolve('admin')
def resolve_admin_field(root, info, *args, **kwargs):
    pass

@Foo.admin_field.resolve()
def resolve_default_admin_field(root, info):
    raise Error('Not Authorized')

@Foo.tenant_field.resolve('perm1')
def resolve_perm1_field(root, info, *args, **kwargs):
    pass

@Foo.tenant_field.resolve('perm2')
def resolve_perm2_field(root, info, *args, **kwargs):
    pass

@Foo.tenant_field.resolve(['perm1', 'perm2'])
def resolve_perm1_and_perm2_field(root, info, *args, **kwargs):
    # Uses sorted() + tuple hashing to register function
    pass

@Foo.tenant_field.resolve('perm3')
@Foo.tenant_field.resolve('perm4')
def resolve_perm3_or_perm4_field(root, info, *args, **kwargs):
    # Registers function for both 'perm3' and 'perm4' route keys
    pass
```

ACL Connection Fields

```python
from graphene_django.filter import DjangoFilterConnectionField
from graphene_acl import acl_field_type

BarConnectionField = acl_field_type('BarConnectionField', DjangoFilterConnectionField)

class Foo(graphene.ObjectType):
    bar = BarConnectionField(MyNode, acl_permissions=has_permission('FOO'))

```

## Development

### First time setup

-   Install Precommit hooks
-   `brew install pre-commit && pre-commit install && pre-commit install --install-hooks`
-   Install poetry: https://github.com/sdispater/poetry#installation
-   `curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python`
-   Install dependencies
-   `poetry install`
