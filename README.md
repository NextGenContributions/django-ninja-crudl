# Why this package?

To provide the most simplest and quickest way to expose Django models securely as RESTful API CRUDL (Create, Retrieve, Update, Delete, List) endpoints and provide the most complete OpenAPI documentation for those endpoints.

# What is it?

The package provides a set of classes and methods to expose Django models via RESTful API CRUDL endpoints.

Behind the scenes, the package uses the [Django Ninja Extra](https://eadwincode.github.io/django-ninja-extra/) package which in turn uses [Django Ninja](https://django-ninja.dev/).
For the input and output validation schemas, [django2pydantic](https://github.com/NextGenContributions/django2pydantic) package is used.

# Tutorial on how to use

## Define the Django models along the fields exposed via the CRUDL endpoints

You can define you Django model fields that are exposed via the CRUDL endpoints in the model itself using the `CrudlApiMeta` nested class inside your model:

```python

from django2pydantic import Infer, ModelFields
from django.db import models
from django_ninja_crudl.crudl import CrudlApiBaseMeta # <-- Add this import if you want type checking

class MyModelA(models.Model):
    """Some example model."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()

    class CrudlApiMeta(CrudlApiBaseMeta): # <-- Add this nested class to your model
        create_fields: ClassVar[ModelFields] = {
            "name": Infer,
            "description": Infer,
        }
        update_fields: ClassVar[ModelFields] = {
            "name": Infer,
            "description": Infer,
        }
        get_one_fields: ClassVar[ModelFields] = {
            "id": Infer,
            "name": Infer,
            "description": Infer,
        }
        list_fields: ClassVar[ModelFields] = {
            "id": Infer,
            "name": Infer,
        }

```

NOTE: In order to avoid accidentally exposing sensitive fields, you need to explicitly define the model fields that shall be exposed via the CRUDL endpoints. Some other libraries support exposing all fields (with optional exlude) which can lead to unintentional exposure of sensitive data.

NOTE: The `Infer` class from the `django2pydantic` library is used to infer the field type and details from the Django model fields.

NOTE: The library allows using different schemas for the `create`, `update`/`partial update`, `get one`, and `list` operations. For example, this can have the following practical advantages: - Allows that some fields can be used during create but cannot be updated after the creation - The list operation can expose only the fields that are needed for the list view - The get one operation can expose more fields than the list operation

## Define the CRUDL endpoints for a model

Then you need to define the CRUDL controller for the model.

```python

from django_ninja_crudl.crudl import Crudl
from .models import MyModelA


class MyModelACrudl(Crudl):
    """A CRUDL controller for the model."""

    class Meta:
        model_class = MyModelA # <-- Add reference to your model class here that you defined previously
```

## Register the endpoint

Then you need to register the CRUDL controller in the API itself.

```python
from ninja_extra import NinjaExtraAPI

from .api import MyModelACrudl

api = NinjaExtraAPI()

api.register_controllers(MyModelACrudl)
```

Further instructions: https://eadwincode.github.io/django-ninja-extra/tutorial/

## Define the queryset filters for the CRUDL endpoints

In order to control what is exposed and operable via the CRUDL endpoints, you can define the queryset filters.

This serves as an additional layer of security and control.

You can define:

- the base queryset filter that applies to all CRUDL operations
- the operation type specific filters that apply to the create, update, delete, list, and get_one operations separately.

The filters are defined as [Django models.Q objects](https://docs.djangoproject.com/en/5.1/topics/db/queries/#complex-lookups-with-q-objects). If you return an empty model.Q object, no additional filtering is applied.

For security reasons, the developer needs to explicitly define the filters for each operation type.
You need to explicitely override the following methods in the CRUDL controller. If you do not override them, the "not implemented error" will be raised.

```python

from django_ninja_crudl.types import RequestDetails

class MyModelACrudl(Crudl):
    """A CRUDL controller for the Database model."""

    class Meta:
        model_class = MyModelA

    @override
    def get_qs_base_filter(self, request: RequestDetails) -> Q:
        """Return the base queryset filter that applies to all CRUDL operations."""
        return Q()

    @override
    def get_filter_for_create(self, request: RequestDetails) -> Q:
        """Return the queryset filter that applies to the create operation."""
        return Q()

    @override
    def get_filter_for_update(self, request: RequestDetails) -> Q:
        """Return the queryset filter that applies to the update operation."""
        return Q()

    def get_filter_for_delete(self, request: RequestDetails) -> Q:
        """Return the queryset filter that applies to the delete operation."""
        return Q()

    def get_filter_for_list(self, request: RequestDetails) -> Q:
        """Return the queryset filter that applies to the list operation."""
        return Q()

    def get_filter_for_get_one(self, request: RequestDetails) -> Q:
        """Return the queryset filter that applies to the get_one operation."""
        return Q()
```

The [`RequestDetails`](./django_ninja_crudl/types.py) object contains as much information as possible about the request that is available at the time of the call.

## Implement permission checks

The permission checks are for checking if the user has permission to perform the CRUDL operations for:

- the resource (=model) type
- the object (=instance)
- the related object (=related instance)

```python

from django_ninja_crudl.permissions import BasePermission

class ResourcePermission(BasePermission):
    def has_permission(self, request: RequestDetails) -> bool:
        """Check if the user has permission for the action.

        If this method returns False, the operation is not executed.
        And the endpoint returns a 403 Forbidden response.
        """
        return True

    def has_object_permission(self, request: RequestDetails) -> bool:
        """Check if the user has permission for the object.

        If this method returns False, the operation is not executed.
        And the endpoint returns a 404 Not Found response.
        """
        return True

    def has_related_object_permission(self, request: RequestDetails) -> bool:
        """Check if the user has permission for the related object.

        If this method returns False, the operation is not executed.
        And the endpoint returns a 404 Not Found response.
        """
        return True

```

NOTE: again the `RequestDetails` object contains as much information as possible about the request that is available at the time of the call.

Finally, you can define the permission classes to be used in the CRUDL controller:

```python

class MyModelACrudl(Crudl):

    class Meta:
        model_class = MyModelA
        permission_classes = [ResourcePermission] # <-- Add the permission classes you wish to use here

```

## Implement the pre and post hooks (optional)

With the pre and post hooks, you can execute custom code before and after each CRUDL operation type.

- The pre hooks are executed after the has_permission&has_object_permission check but before the operation itself
- The post hooks are executed at the end of the operation.

```python

class MyModelACrudl(Crudl):

    class Meta:
        model_class = MyModelA

    def pre_create(self, request: RequestDetails):
        """Do something before creating the object."""
        ...

    def post_create(self, request: RequestDetails):
        """Do something after creating the object."""
        ...

    def pre_update(self, request: RequestDetails):
        """Do something before updating the object."""
        ...

    def post_update(self, request: RequestDetails):
        """Do something after updating the object."""
        ...

    def pre_delete(self, request: RequestDetails):
        """Do something before deleting the object."""
        ...

    def post_delete(self, request: RequestDetails):
        """Do something after deleting the object."""
        ...

    def pre_list(self, request: RequestDetails):
        """Do something before listing the objects."""
        ...

    def post_list(self, request: RequestDetails):
        """Do something after listing the objects."""
        ...

    def pre_get_one(self, request: RequestDetails):
        """Do something before getting the object."""
        ...

    def post_get_one(self, request: RequestDetails):
        """Do something after getting the object."""
        ...

```

Again, here too, the `RequestDetails` object contains as much information as possible about the request that is available at the time of the call.

## Implement additional REST endpoints

You can implement additional REST endpoints in the CRUDL controller.

```python

from ninja_extra import NinjaExtraAPI
from ninja_extra.crudl import Crudl
from ninja_extra.types import RequestDetails

from .models import MyModelA

class MyModelACrudl(Crudl):
    """A CRUDL controller for the Database model."""

    class Meta:
        model_class = MyModelA

    @http.get("/my_custom_endpoint")
    def my_custom_endpoint(self, request: RequestDetails):
        """A custom endpoint."""
        return {"message": "Hello, world!"}

```

## Summary of functionality

| Operation               | Base queryset filter applied | Queryset filter             | has_permission(...) | has_object_permission(...) | has_related_object_permission(...) | Model full_clean() method called | Pre and post hook methods     |
| ----------------------- | ---------------------------- | --------------------------- | ------------------- | -------------------------- | ---------------------------------- | -------------------------------- | ----------------------------- |
| Create                  | No                           | None                        | Yes                 | No                         | Yes                                | Yes                              | pre_create(), post_create()   |
| Retrieve                | Yes                          | get_filter_for_get_one(...) | Yes                 | Yes                        | Yes                                | Yes                              | pre_get_one(), post_get_one() |
| Update / Partial update | Yes                          | get_filter_for_update(...)  | Yes                 | Yes                        | Yes                                | Yes                              | pre_update(), post_update()   |
| Delete                  | Yes                          | get_filter_for_delete(...)  | Yes                 | Yes                        | No                                 | No                               | pre_delete(), post_delete()   |
| List                    | Yes                          | get_filter_for_list(...)    | Yes                 | No                         | No                                 | No                               | pre_list(), post_list()       |

## Create operation

The create operation is done through the Django model manager create method.

If you want to customize the create operation, you can override the create method in the model manager.

```python

from django.db import models

class MyModelAManager(models.Manager):

    def create(self, **kwargs):
        # Do something before creating the object
        return super().create(**kwargs)

class MyModelA(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()

    objects = MyModelAManager()

```

## Validations

The framework provides the following validations:

### Request validation

The request payload structure is validated automatically using Pydantic just like it is done in Django Ninja. If the request payload does not match the expected structure, a 422 Unprocessable Entity response is returned.

### Create and update validation

The models are validated before creating or updating the object using the Django model's [full_clean() method](https://docs.djangoproject.com/en/5.1/ref/models/instances/#validating-objects).

If you want to customize the validation, you can override or customize the full_clean method in the Django model.

# Ways to support this project

- ⭐ Star this project on GitHub
- Share this project with your friends, colleagues, and on social media
- [Contribute code, documentation, and tests](CONTRIBUTING.md)
- Report bugs, issues, or feature requests
- Sponsor this project
