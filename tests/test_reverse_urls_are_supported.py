"""Test URL pattern reversing for the Author API endpoints."""

from django.urls import reverse


def test_author_create_list_urls() -> None:
    """Test URLs for author creation and listing."""
    # Test create endpoint
    create_url = reverse("api-1.0.0:Author_create")
    assert create_url == "/api/authors"

    # Test list endpoint
    list_url = reverse("api-1.0.0:Author_list")
    assert list_url == "/api/authors"


def test_author_detail_urls() -> None:
    """Test URLs for author detail operations that require an ID."""
    author_id = 1

    # Test get_one endpoint
    get_one_url = reverse("api-1.0.0:Author_get_one", kwargs={"id": author_id})
    assert get_one_url == f"/api/authors/{author_id}"

    # Test update endpoint
    update_url = reverse("api-1.0.0:Author_update", kwargs={"id": author_id})
    assert update_url == f"/api/authors/{author_id}"

    # Test partial_update endpoint
    partial_update_url = reverse(
        "api-1.0.0:Author_partial_update", kwargs={"id": author_id}
    )
    assert partial_update_url == f"/api/authors/{author_id}"

    # Test delete endpoint
    delete_url = reverse("api-1.0.0:Author_delete", kwargs={"id": author_id})
    assert delete_url == f"/api/authors/{author_id}"


def test_author_urls_with_string_ids() -> None:
    """Test URLs with string IDs to ensure proper URL encoding."""
    author_id = "test-author"

    get_one_url = reverse("api-1.0.0:Author_get_one", kwargs={"id": author_id})
    assert get_one_url == f"/api/authors/{author_id}"
