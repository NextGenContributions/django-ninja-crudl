"""Test the API endpoints with forward One-To-One relation."""


import pytest
from django.test import Client
from ninja_extra import status

from tests.test_django.app import models


@pytest.mark.django_db
def test_creating_relation_with_post_should_work(client: Client) -> None:
    """Test creating a relation with POST request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )

    response = client.post(
        "/api/amazon_author_profiles",
        content_type="application/json",
        data={
            "author_id": author.id,
            "description": "Some description",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    profile = models.AmazonAuthorProfile.objects.get(id=response.json()["id"])
    assert profile.author_id == author.id
    assert profile.description == profile.description
    author.refresh_from_db()
    assert author.amazon_author_profile.id == profile.id


@pytest.mark.django_db
def test_updating_relation_with_put_should_work(client: Client) -> None:
    """Test updating a relation with PUT request."""
    author_1 = models.Author.objects.create(
        name="Some author 1",
        birth_date="1990-01-01",
    )
    author_2 = models.Author.objects.create(
        name="Some author 2",
        birth_date="1990-01-02",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author_1,
        description="Some description",
    )
    response = client.put(
        f"/api/amazon_author_profiles/{amz_author_profile.id}",
        content_type="application/json",
        data={
            "author_id": author_2.id,
            "description": "Some updated description",
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    amz_author_profile.refresh_from_db()
    assert amz_author_profile.author.id == author_2.id
    assert amz_author_profile.description == "Some updated description"


@pytest.mark.django_db
def test_updating_relation_with_patch_should_work(client: Client) -> None:
    """Test updating a relation with PATCH request."""
    author_1 = models.Author.objects.create(
        name="Some author 1",
        birth_date="1990-01-01",
    )
    author_2 = models.Author.objects.create(
        name="Some author 2",
        birth_date="1990-01-02",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author_1,
        description="Some description",
    )
    response = client.patch(
        f"/api/amazon_author_profiles/{amz_author_profile.id}",
        content_type="application/json",
        data={
            "author_id": author_2.id,
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    amz_author_profile.refresh_from_db()
    assert amz_author_profile.author.id == author_2.id


@pytest.mark.django_db
def test_deleting_relation_by_deleting_object_should_work(client: Client) -> None:
    """Test deleting a relation with DELETE request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author,
        description="Some description",
    )
    response = client.delete(f"/api/amazon_author_profiles/{amz_author_profile.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert models.Author.objects.filter(id=author.id).exists()
    assert not models.AmazonAuthorProfile.objects.filter(
        id=amz_author_profile.id
    ).exists()


@pytest.mark.django_db
def test_deleting_relation_by_patch_should_work(client: Client) -> None:
    """Test deleting a relation by using an update request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author,
        description="Some description",
    )
    response = client.patch(
        f"/api/amazon_author_profiles/{amz_author_profile.id}",
        content_type="application/json",
        data={
            "author_id": None
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    amz_author_profile.refresh_from_db()
    assert amz_author_profile.author_id == None


@pytest.mark.django_db
def test_getting_relation_with_get_many_should_work(client: Client) -> None:
    """Test listing relations with GET many (list) request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author,
        description="Some description",
    )
    response = client.get("/api/amazon_author_profiles")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["author"]["id"] == author.id
    assert response.json()[0]["author"]["name"] == "Some author"
    assert response.json()[0]["description"] == "Some description"


@pytest.mark.django_db
def test_getting_relation_with_get_one_should_work(client: Client) -> None:
    """Test getting relations with GET one (retrieve) request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author,
        description="Some description",
    )
    response = client.get(f"/api/amazon_author_profiles/{amz_author_profile.id}")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert response.json()["author"]["id"] == author.id
    assert response.json()["author"]["name"] == "Some author"
    assert response.json()["description"] == "Some description"
