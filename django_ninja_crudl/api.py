"""API module for the project."""

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpRequest, HttpResponse
from ninja_extra import NinjaExtraAPI, status
from src.databases.ninja import DatabaseCrudl

from .errors.schemas import ErrorSchema

api = NinjaExtraAPI()

api.register_controllers(DatabaseCrudl)
