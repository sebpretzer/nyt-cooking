from __future__ import annotations

import json
import re
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import httpx
import pytest

from nyt_cooking.client import Client
from nyt_cooking.client.models import (
    Recipe,
    SearchCriteria,
    SearchFilters,
    SearchResults,
    SearchSort,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.conftest import Handler, Site


pytestmark = pytest.mark.usefixtures("signed_in")


@pytest.fixture
def api(
    recipe_payload: dict[str, Any],
    search_payload: dict[str, Any],
    recipe_box_payload: dict[str, Any],
) -> Handler:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/api/v3/search"):
            return httpx.Response(HTTPStatus.OK, json=search_payload)
        if request.url.path.startswith("/api/v2/recipes/"):
            return httpx.Response(HTTPStatus.OK, json=recipe_payload)
        return httpx.Response(HTTPStatus.OK, json=recipe_box_payload)

    return respond


def test_search_recipes_requests_the_search_api(site: Site, api: Handler) -> None:
    seen = site(api)
    with Client(cookie="abc") as client:
        results = client.search_recipes("lemon pasta", page=2)
    assert isinstance(results, SearchResults)
    assert [result.id for result in results.results] == [42, 43]
    (request,) = seen
    assert request.method == "GET"
    assert request.url.path == "/api/v3/search"
    assert dict(request.url.params) == {"q": "lemon pasta", "page": "2"}
    assert request.headers["user-agent"].startswith("Mozilla/5.0")


def test_search_recipes_sends_every_filter(site: Site, api: Handler) -> None:
    seen = site(api)
    criteria = SearchCriteria(
        tags=["healthy", "one pot"],
        max_minutes=30,
        top_rated=True,
        sort=SearchSort.MOST_RECENT,
    )
    with Client() as client:
        client.search_recipes("chili", criteria=criteria)
    assert dict(seen[0].url.params) == {
        "q": "chili",
        "page": "1",
        "tags": "healthy,one pot",
        "time_lte": "30",
        "ratings": "topRated",
        "sort": "firstPublished",
    }


@pytest.mark.parametrize(
    "criteria",
    [None, SearchCriteria()],
    ids=["none", "empty"],
)
def test_search_recipes_omits_filters_that_are_not_set(
    site: Site,
    api: Handler,
    criteria: SearchCriteria | None,
) -> None:
    seen = site(api)
    with Client() as client:
        client.search_recipes("chili", criteria=criteria)
    assert set(seen[0].url.params) == {"q", "page"}


def test_search_filters_reads_the_search_page(
    site: Site,
    search_page_html: str,
) -> None:
    seen = site(lambda _request: httpx.Response(HTTPStatus.OK, text=search_page_html))
    with Client() as client:
        filters = client.search_filters(
            "soup",
            SearchCriteria(tags=["dinner"], max_minutes=45, top_rated=True),
        )
    assert isinstance(filters, SearchFilters)
    assert filters.tags == {"dinner": 30, "five ingredient": 2, "sheet-pan": 5}
    (request,) = seen
    assert request.url.path == "/search"
    assert dict(request.url.params) == {
        "q": "soup",
        "tags": "dinner",
        "time_lte": "45",
        "ratings": "topRated",
    }


def test_search_filters_without_filters_sends_only_the_query(
    site: Site,
    search_page_html: str,
) -> None:
    seen = site(lambda _request: httpx.Response(HTTPStatus.OK, text=search_page_html))
    with Client() as client:
        client.search_filters()
    assert dict(seen[0].url.params) == {"q": ""}


def test_search_filters_rejects_a_page_without_search_data(site: Site) -> None:
    site(lambda _request: httpx.Response(HTTPStatus.OK, text="<html></html>"))
    with Client() as client, pytest.raises(ValueError, match="no embedded"):
        client.search_filters("soup")


def test_cookie_is_sent_to_the_site(site: Site, api: Handler) -> None:
    seen = site(api)
    with Client(cookie="abc") as client:
        client.get_recipe("1")
    assert seen[0].headers["cookie"] == "NYT-S=abc"


def test_base_url_defaults_to_the_nyt_cooking_site(site: Site, api: Handler) -> None:
    seen = site(api)
    with Client() as client:
        client.get_recipe("1")
    assert str(client.settings.rest.base_url) == "https://cooking.nytimes.com/"
    assert seen[0].url.host == "cooking.nytimes.com"


def test_base_url_can_point_the_client_elsewhere(
    site: Site,
    api: Handler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NYT_COOKING_REST__BASE_URL", "http://localhost:8123")
    seen = site(api)
    with Client() as client:
        client.get_recipe("1")
    assert str(seen[0].url) == "http://localhost:8123/api/v2/recipes/1"


def test_get_recipe_returns_a_recipe(site: Site, api: Handler) -> None:
    seen = site(api)
    with Client() as client:
        recipe = client.get_recipe(1019049)
    assert isinstance(recipe, Recipe)
    assert recipe.name == "Weeknight Test Soup"
    (request,) = seen
    assert request.url.path == "/api/v2/recipes/1019049"
    assert request.headers["x-cooking-api"] == "cooking-frontend"


def test_get_recipe_box_requests_the_users_box(site: Site, api: Handler) -> None:
    seen = site(api)
    with Client(cookie="abc") as client:
        box = client.get_recipe_box(page=3, per_page=10)
    assert [recipe.id for recipe in box.recipes] == [42, 43]
    (request,) = seen
    assert request.url.path == "/api/v2/users/42/search/recipe_box_search"
    assert dict(request.url.params) == {"q": "", "page": "3", "per_page": "10"}
    assert request.headers["x-cooking-api"] == "cooking-frontend"


def test_get_recently_viewed_requests_me(site: Site) -> None:
    seen = site(
        lambda _request: httpx.Response(
            HTTPStatus.OK,
            json=[
                {"id": 42, "name": "Soup", "url": "https://x/42"},
                {"id": 43, "name": "Broth", "url": "https://x/43"},
                {"id": 44, "name": "Stew", "url": "https://x/44"},
            ],
        ),
    )
    with Client(cookie="abc") as client:
        viewed = client.get_recently_viewed(max_results=2)
    assert [recipe.id for recipe in viewed.recipes] == [42, 43]
    (request,) = seen
    assert request.url.path == "/api/v5/users/me/recently_viewed"
    assert dict(request.url.params) == {"per_page": "2"}


@pytest.mark.parametrize(
    "status",
    [
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.FORBIDDEN,
        HTTPStatus.NOT_FOUND,
        HTTPStatus.INTERNAL_SERVER_ERROR,
    ],
)
def test_error_statuses_raise_http_status_errors(
    site: Site,
    status: HTTPStatus,
) -> None:
    site(lambda _request: httpx.Response(status))
    with Client() as client, pytest.raises(httpx.HTTPStatusError) as excinfo:
        client.get_recipe("1")
    assert excinfo.value.response.status_code == status


def test_transport_failures_propagate(site: Site) -> None:
    def fail(_request: httpx.Request) -> httpx.Response:
        msg = "refused"
        raise httpx.ConnectError(msg)

    site(fail)
    with Client() as client, pytest.raises(httpx.ConnectError):
        client.search_recipes("salt")


def test_invalid_json_raises_a_decode_error(site: Site) -> None:
    site(lambda _request: httpx.Response(HTTPStatus.OK, text="<html>not json</html>"))
    with Client() as client, pytest.raises(json.JSONDecodeError):
        client.get_recipe("1")


def test_user_agent_can_be_overridden(
    site: Site,
    api: Handler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NYT_COOKING_USER_AGENT", "Custom/1.0")
    seen = site(api)
    with Client() as client:
        client.get_recipe("1")
    assert seen[0].headers["user-agent"] == "Custom/1.0"


def test_every_request_sends_the_shared_headers(site: Site, api: Handler) -> None:
    seen = site(api)
    with Client() as client:
        client.search_recipes("salt")
        client.get_recipe("1")
    for request in seen:
        assert "Firefox/" in request.headers["user-agent"]
        assert request.headers["x-cooking-api"] == "cooking-frontend"


def test_redirects_are_followed(site: Site, api: Handler) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/recipes/1":
            return httpx.Response(
                HTTPStatus.MOVED_PERMANENTLY,
                headers={"location": "/api/v2/recipes/1-moved"},
            )
        return api(request)

    seen = site(handler)
    with Client() as client:
        assert client.get_recipe(1).name == "Weeknight Test Soup"
    assert [request.url.path for request in seen] == [
        "/api/v2/recipes/1",
        "/api/v2/recipes/1-moved",
    ]


def _http_clients(client: Client) -> list[httpx.Client]:
    return [client._rest_client, client._graphql_client]


def test_one_client_per_api_serves_every_call(site: Site, api: Handler) -> None:
    site(api)
    with Client() as client:
        pooled = _http_clients(client)
        client.get_recipe("1")
        client.get_recipe("2")
        assert _http_clients(client) == pooled
        assert not any(http_client.is_closed for http_client in pooled)


def test_context_manager_closes_the_client(site: Site, api: Handler) -> None:
    site(api)
    with Client() as client:
        pass
    assert all(http_client.is_closed for http_client in _http_clients(client))


def test_context_manager_closes_the_client_after_an_error(site: Site) -> None:
    site(lambda _request: httpx.Response(HTTPStatus.NOT_FOUND))
    with pytest.raises(httpx.HTTPStatusError), Client() as client:
        client.get_recipe("1")
    assert all(http_client.is_closed for http_client in _http_clients(client))


def test_close_is_available_without_a_with_block(site: Site, api: Handler) -> None:
    site(api)
    client = Client()
    client.close()
    assert all(http_client.is_closed for http_client in _http_clients(client))


def test_timeout_is_applied_to_the_client(site: Site, api: Handler) -> None:
    site(api)
    timeout = 12
    with Client(timeout=timeout) as client:
        for http_client in _http_clients(client):
            assert http_client.timeout == httpx.Timeout(timeout)


def _paged_search(
    max_page: int,
    empty_pages: frozenset[int] | set[int] = frozenset(),
    per_page: int = 1,
) -> Handler:
    def respond(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        results = (
            []
            if page > max_page
            else [{"collection": {"id": page, "name": "Collection"}}]
            if page in empty_pages
            else [
                {"recipe": {"id": page * 10 + item, "name": f"Result {item}"}}
                for item in range(per_page)
            ]
        )
        return httpx.Response(
            HTTPStatus.OK,
            json={
                "query": request.url.params["q"],
                "results": results,
                "pagination": {"total": max_page, "page": page, "max_page": max_page},
            },
        )

    return respond


def _paged_box(max_page: int) -> Handler:
    def respond(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        return httpx.Response(
            HTTPStatus.OK,
            json={
                "collectables": [
                    {"id": page, "name": f"Saved {page}", "url": f"/r/{page}"},
                ],
                "meta": {
                    "current_page": page,
                    "total_pages": max_page,
                    "total_count": max_page,
                },
            },
        )

    return respond


def test_search_recipes_paginated_joins_every_page(site: Site) -> None:
    seen = site(_paged_search(max_page=3))
    with Client() as client:
        results = client.search_recipes_paginated("soup")
    assert [result.id for result in results.results] == [10, 20, 30]
    assert results.query == "soup"
    assert [request.url.params["page"] for request in seen] == ["1", "2", "3"]


def test_search_recipes_paginated_stops_and_trims_at_max_results(
    site: Site,
) -> None:
    seen = site(_paged_search(max_page=5, per_page=3))
    with Client() as client:
        results = client.search_recipes_paginated("soup", max_results=5)
    assert [result.id for result in results.results] == [10, 11, 12, 20, 21]
    assert [request.url.params["page"] for request in seen] == ["1", "2"]


def test_search_recipes_paginated_max_results_within_the_first_page(
    site: Site,
) -> None:
    seen = site(_paged_search(max_page=5, per_page=3))
    with Client() as client:
        results = client.search_recipes_paginated("soup", max_results=2)
    assert [result.id for result in results.results] == [10, 11]
    assert len(seen) == 1


def test_search_recipes_paginated_continues_past_a_page_without_recipes(
    site: Site,
) -> None:
    seen = site(_paged_search(max_page=3, empty_pages={2}))
    with Client() as client:
        results = client.search_recipes_paginated("soup")
    assert [result.id for result in results.results] == [10, 30]
    assert [request.url.params["page"] for request in seen] == ["1", "2", "3", "4"]


@pytest.mark.parametrize(
    "paginate",
    [
        lambda client: client.search_recipes_paginated("soup", max_results=-1),
        lambda client: client.get_recipe_box_paginated(max_results=-1),
    ],
    ids=["search", "recipe-box"],
)
def test_negative_max_results_is_rejected(
    site: Site,
    paginate: Callable[[Client], object],
) -> None:
    seen = site(_paged_search(max_page=3))
    with Client(cookie="abc") as client, pytest.raises(ValueError, match="negative"):
        paginate(client)
    assert seen == []


def test_search_recipes_paginated_keeps_filters_on_every_page(site: Site) -> None:
    seen = site(_paged_search(max_page=3))
    with Client() as client:
        client.search_recipes_paginated(
            "soup",
            criteria=SearchCriteria(
                tags=["vegan"],
                max_minutes=20,
                top_rated=True,
                sort=SearchSort.RATING,
            ),
        )
    assert [request.url.params["page"] for request in seen] == ["1", "2", "3"]
    for request in seen:
        params = request.url.params
        assert params["tags"] == "vegan"
        assert params["time_lte"] == "20"
        assert params["ratings"] == "topRated"
        assert params["sort"] == "rating"


def _capped_search(pages: dict[int, list[int]], overflow: list[int]) -> Handler:
    def respond(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        ids = pages.get(page, overflow)
        return httpx.Response(
            HTTPStatus.OK,
            json={
                "query": request.url.params["q"],
                "results": [{"recipe": {"id": i, "name": f"Result {i}"}} for i in ids],
                "pagination": {"total": 5, "page": page, "max_page": len(pages)},
            },
        )

    return respond


def test_search_recipes_paginated_drops_recipes_repeated_across_pages(
    site: Site,
) -> None:
    site(_capped_search({1: [1, 2], 2: [2, 3, 4, 5]}, overflow=[]))
    with Client() as client:
        results = client.search_recipes_paginated("soup")
    assert [result.id for result in results.results] == [1, 2, 3, 4, 5]


def test_search_recipes_paginated_fetches_recipes_past_the_last_page(
    site: Site,
) -> None:
    seen = site(_capped_search({1: [1], 2: [2]}, overflow=[3, 4]))
    with Client() as client:
        results = client.search_recipes_paginated("soup")
    assert [result.id for result in results.results] == [1, 2, 3, 4]
    assert [request.url.params["page"] for request in seen] == ["1", "2", "3", "4"]


def test_search_recipes_paginated_stops_past_the_last_page_at_max_results(
    site: Site,
) -> None:
    seen = site(_capped_search({1: [1], 2: [2]}, overflow=[3, 4]))
    with Client() as client:
        results = client.search_recipes_paginated("soup", max_results=3)
    assert [result.id for result in results.results] == [1, 2, 3]
    assert [request.url.params["page"] for request in seen] == ["1", "2", "3"]


def test_search_recipes_paginated_single_page_makes_one_request(site: Site) -> None:
    seen = site(_paged_search(max_page=1))
    with Client() as client:
        client.search_recipes_paginated("soup")
    assert len(seen) == 1


def test_get_recipe_box_paginated_joins_every_page(site: Site) -> None:
    seen = site(_paged_box(max_page=3))
    with Client(cookie="abc") as client:
        box = client.get_recipe_box_paginated(per_page=1)
    assert [recipe.id for recipe in box.recipes] == [1, 2, 3]
    assert [request.url.params["page"] for request in seen] == ["1", "2", "3"]
    assert {request.url.params["per_page"] for request in seen} == {"1"}


def test_get_recipe_box_paginated_stops_at_max_results(site: Site) -> None:
    seen = site(_paged_box(max_page=4))
    with Client(cookie="abc") as client:
        box = client.get_recipe_box_paginated(per_page=1, max_results=2)
    assert [recipe.id for recipe in box.recipes] == [1, 2]
    assert len(seen) == len(box.recipes)


GRAPHQL_URL = "https://samizdat-graphql.nytimes.com/graphql/v2"


def _graphql_body(request: httpx.Request) -> dict[str, Any]:
    return json.loads(request.content)


def test_graphql_requests_go_to_the_graphql_api(
    site: Site,
    comments_payload: dict[str, Any],
) -> None:
    seen = site(lambda _request: httpx.Response(HTTPStatus.OK, json=comments_payload))
    with Client(cookie="abc") as client:
        client.get_recipe_comments(775244489)
    (request,) = seen
    assert request.method == "POST"
    assert str(request.url) == GRAPHQL_URL
    assert request.headers["nyt-app-type"] == "cooking-frontend-client"
    assert request.headers["nyt-app-version"] == "1.0.0"
    assert request.headers["nyt-token"].startswith("MIIBIjAN")
    assert "Firefox/" in request.headers["user-agent"]
    assert request.headers["cookie"] == "NYT-S=abc"
    assert "x-cooking-api" not in request.headers


def test_rest_requests_carry_no_graphql_headers(site: Site, api: Handler) -> None:
    seen = site(api)
    with Client() as client:
        client.get_recipe("1")
    assert "nyt-token" not in seen[0].headers


def test_graphql_settings_can_point_the_client_elsewhere(
    site: Site,
    comments_payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NYT_COOKING_GRAPHQL__URL", "http://localhost:8124/graphql")
    monkeypatch.setenv("NYT_COOKING_GRAPHQL__TOKEN", "other-token")
    seen = site(lambda _request: httpx.Response(HTTPStatus.OK, json=comments_payload))
    with Client() as client:
        client.get_recipe_comments(1)
    assert str(seen[0].url) == "http://localhost:8124/graphql"
    assert seen[0].headers["nyt-token"] == "other-token"


def test_graphql_errors_raise_a_value_error(site: Site) -> None:
    site(
        lambda _request: httpx.Response(
            HTTPStatus.OK,
            json={"errors": [{"message": "first: must be no greater than 500."}]},
        ),
    )
    with Client() as client, pytest.raises(ValueError, match="no greater than 500"):
        client.get_recipe_comments(1)


@pytest.mark.parametrize(
    "status",
    [HTTPStatus.BAD_REQUEST, HTTPStatus.FORBIDDEN],
)
def test_graphql_errors_on_an_error_status_keep_nyts_message(
    site: Site,
    status: HTTPStatus,
) -> None:
    site(
        lambda _request: httpx.Response(
            status,
            json={
                "errors": [
                    {"message": "parsing error: expected R_PAREN, got {"},
                    {"message": "invalid query"},
                ],
            },
        ),
    )
    message = (
        f"NYT's GraphQL API rejected the query (HTTP {status.value}): "
        "parsing error: expected R_PAREN, got {; invalid query"
    )
    with Client() as client, pytest.raises(ValueError, match=re.escape(message)):
        client.get_recipe_comments(1)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(HTTPStatus.FORBIDDEN),
        httpx.Response(HTTPStatus.BAD_GATEWAY, text="<html>Bad gateway</html>"),
        httpx.Response(HTTPStatus.INTERNAL_SERVER_ERROR, json={"data": None}),
    ],
    ids=["empty", "html", "json-without-errors"],
)
def test_graphql_error_statuses_without_graphql_errors_raise_http_status_errors(
    site: Site,
    response: httpx.Response,
) -> None:
    site(lambda _request: response)
    with Client() as client, pytest.raises(httpx.HTTPStatusError) as excinfo:
        client.get_recipe_comments(1)
    assert excinfo.value.response.status_code == response.status_code


def test_graphql_invalid_json_raises_a_decode_error(site: Site) -> None:
    site(lambda _request: httpx.Response(HTTPStatus.OK, text="<html>not json</html>"))
    with Client() as client, pytest.raises(json.JSONDecodeError):
        client.get_recipe_comments(1)


def test_get_recipe_comments_asks_for_the_newest_comments(
    site: Site,
    comments_payload: dict[str, Any],
) -> None:
    seen = site(lambda _request: httpx.Response(HTTPStatus.OK, json=comments_payload))
    with Client() as client:
        comments = client.get_recipe_comments(775244489, after="cursor-0", per_page=2)
    assert [comment.id for comment in comments.comments] == ["101", "103"]
    body = _graphql_body(seen[0])
    assert "communityComments" in body["query"]
    assert body["variables"] == {
        "uri": "https://cooking.nytimes.com/recipes/775244489",
        "input": {
            "first": 2,
            "after": "cursor-0",
            "view": "ALL",
            "replies": 500,
            "asc": False,
        },
    }


def test_get_recipe_comments_helpful_only_asks_for_reader_picks(
    site: Site,
    comments_payload: dict[str, Any],
) -> None:
    seen = site(lambda _request: httpx.Response(HTTPStatus.OK, json=comments_payload))
    with Client() as client:
        client.get_recipe_comments(42, helpful_only=True)
    assert _graphql_body(seen[0])["variables"]["input"] == {
        "first": 15,
        "after": None,
        "view": "READER_PICKS",
        "replies": 500,
    }


def test_get_recipe_comments_uri_ignores_a_rest_base_url_override(
    site: Site,
    comments_payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NYT_COOKING_REST__BASE_URL", "http://localhost:8123")
    seen = site(lambda _request: httpx.Response(HTTPStatus.OK, json=comments_payload))
    with Client() as client:
        client.get_recipe_comments(42)
    uri = _graphql_body(seen[0])["variables"]["uri"]
    assert uri == "https://cooking.nytimes.com/recipes/42"


def test_get_recipe_comments_rejects_an_unknown_recipe(site: Site) -> None:
    site(
        lambda _request: httpx.Response(
            HTTPStatus.OK,
            json={
                "data": {
                    "communityComments": {
                        "summary": {"totalCount": None, "totalReadersPicks": None},
                        "pageInfo": {"endCursor": None, "hasNextPage": False},
                        "edges": [],
                    },
                },
            },
        ),
    )
    with Client() as client, pytest.raises(ValueError, match="recipe 999"):
        client.get_recipe_comments(999)


def _paged_comments(pages: int) -> Handler:
    def respond(request: httpx.Request) -> httpx.Response:
        page_input = _graphql_body(request)["variables"]["input"]
        page = int(page_input["after"] or 0)
        edges = [
            {
                "node": {
                    "comment": {
                        "id": f"{page}-{item}",
                        "text": "Good.",
                        "submittedAt": "2026-09-22T02:04:06Z",
                        "author": {"name": "Ada"},
                    },
                    "replies": [],
                },
            }
            for item in range(min(page_input["first"], 2))
        ]
        last = page + 1 >= pages
        return httpx.Response(
            HTTPStatus.OK,
            json={
                "data": {
                    "communityComments": {
                        "summary": {"totalCount": pages * 2, "totalReadersPicks": 0},
                        "pageInfo": {
                            "endCursor": str(page + 1),
                            "hasNextPage": not last,
                        },
                        "edges": edges,
                    },
                },
            },
        )

    return respond


def test_get_recipe_comments_paginated_follows_every_cursor(site: Site) -> None:
    seen = site(_paged_comments(pages=3))
    with Client() as client:
        comments = client.get_recipe_comments_paginated(42)
    assert [comment.id for comment in comments.comments] == [
        "0-0",
        "0-1",
        "1-0",
        "1-1",
        "2-0",
        "2-1",
    ]
    assert comments.next_cursor is None
    inputs = [_graphql_body(request)["variables"]["input"] for request in seen]
    assert [page_input["after"] for page_input in inputs] == [None, "1", "2"]
    assert {page_input["first"] for page_input in inputs} == {500}


def test_get_recipe_comments_paginated_stops_at_max_results(site: Site) -> None:
    seen = site(_paged_comments(pages=5))
    with Client() as client:
        comments = client.get_recipe_comments_paginated(42, max_results=3)
    assert [comment.id for comment in comments.comments] == ["0-0", "0-1", "1-0"]
    assert comments.next_cursor == "2"
    firsts = [_graphql_body(request)["variables"]["input"]["first"] for request in seen]
    assert firsts == [3, 1]


def test_get_recipe_comments_paginated_rejects_negative_max_results(
    site: Site,
) -> None:
    seen = site(_paged_comments(pages=1))
    with Client() as client, pytest.raises(ValueError, match="negative"):
        client.get_recipe_comments_paginated(42, max_results=-1)
    assert seen == []
