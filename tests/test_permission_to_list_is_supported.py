"""Test API permissions."""

import datetime

import pytest
from django.contrib.auth.models import User
from django.test import Client
from ninja_extra import status

from tests.test_django.app import models
from tests.test_django.urls import ADMIN_USER, RESTRICTED_USER, STANDARD_USER


@pytest.mark.django_db
def test_list_resources_while_unauthenticated_should_fail(client: Client) -> None:
    """Test listing resources with GET request."""
    response = client.get("/api/gated-authors")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_list_resources_with_unpermitted_user_should_fail(client: Client) -> None:
    """Test listing resources with GET request."""
    u = User.objects.create_user(RESTRICTED_USER)
    client.force_login(u)

    response = client.get("/api/gated-authors")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_list_permitted_resources_with_permitted_user_should_succeed(
    client: Client,
) -> None:
    """Test listing resources with GET request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)
    client.force_login(std_usr)

    models.Author.objects.create(
        name="Test Author 1",
        birth_date=datetime.date(1990, 1, 1),
        created_by=admin,
    )
    models.Author.objects.create(
        name="Test Author 2",
        birth_date=datetime.date(1985, 5, 5),
        created_by=std_usr,
    )

    response = client.get("/api/gated-authors")
    assert response.status_code == status.HTTP_200_OK, response.json()
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] in ["Test Author 2"]


# TODO(phuongfi91): What about listing permitted resources that have unpermitted related resources?
