"""Test API calls using the generated OpenAPI schema."""

import pytest
import schemathesis

# Generate and save the OpenAPI schema in a file
# by running Django DRF management command:
from pytest_django.live_server_helper import LiveServer
from schemathesis.specs.openapi.schemas import BaseOpenAPISchema

schemathesis.experimental.OPEN_API_3_1.enable()


@pytest.fixture
def web_app(live_server: LiveServer) -> BaseOpenAPISchema:
    # some dynamically built application
    # that depends on other fixtures

    api_spec_url = f"{live_server.url}/api/openapi.json"

    return schemathesis.from_uri(api_spec_url)


schema = schemathesis.from_pytest_fixture("web_app")


@pytest.mark.django_db
@schema.parametrize()  # pyright: ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
def test_api_calls_against_schema(
    case: schemathesis.Case,
    live_server: LiveServer,  # this starts the needed live server so # noqa: ARG001
) -> None:
    """Test API calls using the generated OpenAPI schema and the schemathesis library.

    Schemathesis is a tool that levels-up your API testing by automating the process of
    finding crashes, uncovering bugs, and validating spec compliance.

    With Schemathesis, you can:

    🎯 Catch Hard-to-Find Bugs

    Uncover hidden crashes and edge cases that manual testing might miss
    Identify spec violations and ensure your API adheres to its defined contra

    Parameters
    ----------
    case: schemathesis.Case
        The generated test case.
    live_server: LiveServer
        The Django live server fixture from the pytest-django plugin.

    """
    case.call_and_validate()  # we do not need the return value
