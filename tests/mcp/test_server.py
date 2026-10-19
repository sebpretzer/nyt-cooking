from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import Client as MCPClient
from fastmcp.exceptions import ToolError

from nyt_cooking.client import Client
from nyt_cooking.client.models import (
    Comments,
    Folder,
    Folders,
    IsAuthenticated,
    RecentlyViewed,
    Recipe,
    RecipeBox,
    SavedRecipe,
    SearchCriteria,
    SearchFilters,
    SearchResults,
    SearchSort,
)
from nyt_cooking.client.settings import CredentialStore, Settings
from nyt_cooking.mcp import server

if TYPE_CHECKING:
    from tests.conftest import FakeKeyring, Site


SHEET_PAN_COUNT = 5


def _call(tool: Any, **kwargs: Any) -> Any:
    with Client() as client:
        return getattr(tool, "fn", tool)(client=client, **kwargs)


def _call_auth(tool: Any, **kwargs: Any) -> Any:
    return getattr(tool, "fn", tool)(**kwargs)


@pytest.fixture
def tracked_clients(monkeypatch: pytest.MonkeyPatch) -> list[Client]:
    opened: list[Client] = []

    def tracking(**kwargs: Any) -> Client:
        created = Client(**kwargs)
        opened.append(created)
        return created

    monkeypatch.setattr(server, "Client", tracking)
    return opened


def _call_over_mcp(*calls: tuple[str, dict[str, Any]]) -> list[Any]:
    async def run() -> list[Any]:
        async with MCPClient(server.mcp) as client:
            return [
                (await client.call_tool(tool, arguments)).data
                for tool, arguments in calls
            ]

    return asyncio.run(run())


def _respond_with(payload: Any) -> Any:
    return lambda _request: httpx.Response(HTTPStatus.OK, json=payload)


SEARCH_GUIDANCE = {
    "get_search_filters": [
        "Call this before filtering",
        "same `query` as `search_recipes`",
        "only tags with at",
        "least one result",
        "empty `query` returns every tag",
        "exactly as `search_recipes` expects them",
        "counts shrink as filters are added",
        "time limit",
        "top rated",
    ],
    "search_recipes": [
        "call `get_search_filters`",
        "misspelled or invented tag returns 0 results rather than an error",
        "0 results",
        "can mean a bad tag",
        "combine with AND",
        "960 results",
        "inclusive",
        "no minimum",
        "`rating` for highest rated",
        "`firstPublished` for most recent",
        "best match",
    ],
}


def _descriptions(node: Any) -> list[str]:
    if isinstance(node, dict):
        found = (
            [node["description"]] if isinstance(node.get("description"), str) else []
        )
        for value in node.values():
            found += _descriptions(value)
        return found
    if isinstance(node, list):
        return [text for item in node for text in _descriptions(item)]
    return []


class TestToolGuidance:
    @staticmethod
    def _tool_schema(tool: str) -> dict[str, Any]:
        async def describe() -> dict[str, Any]:
            async with MCPClient(server.mcp) as client:
                tools = {t.name: t for t in await client.list_tools()}
            listed = tools[tool]
            return {
                "description": listed.description,
                "input_schema": listed.input_schema,
            }

        return asyncio.run(describe())

    @pytest.mark.parametrize("tool", SEARCH_GUIDANCE)
    def test_descriptions_carry_the_search_caveats(self, tool: str) -> None:
        guidance = " ".join(" ".join(_descriptions(self._tool_schema(tool))).split())
        missing = [
            phrase
            for phrase in SEARCH_GUIDANCE[tool]
            if phrase.lower() not in guidance.lower()
        ]
        assert missing == []

    def test_sort_lists_its_allowed_values(self) -> None:
        text = json.dumps(self._tool_schema("search_recipes")["input_schema"])
        for value in ("rating", "firstPublished"):
            assert f'"{value}"' in text


class TestToolAnnotations:
    def test_only_the_tools_that_change_nothing_are_read_only(self) -> None:
        async def read_only() -> set[str]:
            async with MCPClient(server.mcp) as client:
                tools = await client.list_tools()
            return {
                tool.name
                for tool in tools
                if tool.annotations and tool.annotations.read_only_hint
            }

        assert asyncio.run(read_only()) == {
            "get_search_filters",
            "search_recipes",
            "get_recipe",
            "get_recipe_comments",
            "get_recipe_box",
            "get_recently_viewed",
            "get_folders",
            "get_folder_recipes",
            "get_recipe_save_status",
            "get_auth_status",
        }

    def test_tools_that_change_data_declare_if_they_are_destructive(self) -> None:
        async def destructive() -> dict[str, bool | None]:
            async with MCPClient(server.mcp) as client:
                tools = await client.list_tools()
            return {
                tool.name: tool.annotations.destructive_hint
                for tool in tools
                if tool.annotations and not tool.annotations.read_only_hint
            }

        assert asyncio.run(destructive()) == {
            "add_folder": False,
            "rename_folder": True,
            "remove_folder": True,
            "add_recipe": False,
            "remove_recipe": True,
            "auth_login": True,
            "auth_logout": True,
        }

    def test_every_tool_has_a_title(self) -> None:
        async def titles() -> dict[str, str | None]:
            async with MCPClient(server.mcp) as client:
                tools = await client.list_tools()
            return {tool.name: tool.title for tool in tools}

        assert asyncio.run(titles()) == {
            "get_search_filters": "Get Search Filters",
            "search_recipes": "Search Recipes",
            "get_recipe": "Get Recipe",
            "get_recipe_comments": "Get Recipe Comments",
            "get_recipe_box": "Get Recipe Box",
            "get_recently_viewed": "Get Recently Viewed",
            "get_folders": "Get Folders",
            "get_folder_recipes": "Get Folder Recipes",
            "add_folder": "Add Folder",
            "rename_folder": "Rename Folder",
            "remove_folder": "Remove Folder",
            "get_recipe_save_status": "Get Recipe Save Status",
            "add_recipe": "Add Recipe",
            "remove_recipe": "Remove Recipe",
            "auth_login": "Log In",
            "auth_logout": "Log Out",
            "get_auth_status": "Get Login Status",
        }


@pytest.mark.usefixtures("signed_in")
class TestTools:
    def test_registers_every_tool_with_an_output_schema(self) -> None:
        async def list_tools() -> dict[str, bool]:
            async with MCPClient(server.mcp) as client:
                tools = await client.list_tools()
            return {tool.name: bool(tool.output_schema) for tool in tools}

        assert asyncio.run(list_tools()) == {
            "get_search_filters": True,
            "search_recipes": True,
            "get_recipe": True,
            "get_recipe_comments": True,
            "get_recipe_box": True,
            "get_recently_viewed": True,
            "get_folders": True,
            "get_folder_recipes": True,
            "add_folder": True,
            "rename_folder": True,
            "remove_folder": True,
            "get_recipe_save_status": True,
            "add_recipe": True,
            "remove_recipe": True,
            "auth_login": True,
            "auth_logout": True,
            "get_auth_status": True,
        }

    def test_search_recipes_returns_search_results(
        self,
        site: Site,
        search_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(search_payload))
        result = _call(server.search_recipes, query="soup")
        assert isinstance(result, SearchResults)
        assert [recipe.id for recipe in result.results] == [42, 43]
        assert seen[0].url.params["q"] == "soup"

    def test_search_recipes_forwards_max_results(
        self,
        site: Site,
        search_payload: dict[str, Any],
    ) -> None:
        site(_respond_with(search_payload))
        result = _call(server.search_recipes, query="soup", max_results=1)
        assert [recipe.id for recipe in result.results] == [42]

    def test_search_recipes_forwards_filters(
        self,
        site: Site,
        search_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(search_payload))
        _call(
            server.search_recipes,
            query="soup",
            criteria=SearchCriteria(
                tags=["vegan", "one pot"],
                max_minutes=30,
                top_rated=True,
                sort=SearchSort.RATING,
            ),
        )
        params = seen[0].url.params
        assert params["tags"] == "vegan,one pot"
        assert params["time_lte"] == "30"
        assert params["ratings"] == "topRated"
        assert params["sort"] == "rating"

    def test_get_search_filters_returns_filters(
        self,
        site: Site,
        search_page_html: str,
    ) -> None:
        seen = site(
            lambda _request: httpx.Response(HTTPStatus.OK, text=search_page_html),
        )
        result = _call(
            server.get_search_filters,
            query="soup",
            criteria=SearchCriteria(tags=["dinner"], max_minutes=30, top_rated=True),
        )
        assert isinstance(result, SearchFilters)
        assert result.tags["sheet-pan"] == SHEET_PAN_COUNT
        params = seen[0].url.params
        assert seen[0].url.path == "/search"
        assert (params["q"], params["tags"], params["time_lte"]) == (
            "soup",
            "dinner",
            "30",
        )
        assert params["ratings"] == "topRated"

    def test_get_search_filters_defaults_to_every_tag(
        self,
        site: Site,
        search_page_html: str,
    ) -> None:
        seen = site(
            lambda _request: httpx.Response(HTTPStatus.OK, text=search_page_html),
        )
        _call(server.get_search_filters)
        assert dict(seen[0].url.params) == {"q": ""}

    def test_get_recipe_returns_a_recipe(
        self,
        site: Site,
        recipe_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(recipe_payload))
        result = _call(server.get_recipe, recipe_id=42)
        assert isinstance(result, Recipe)
        assert result.name == "Weeknight Test Soup"
        assert seen[0].url.path == "/api/v2/recipes/42"

    def test_get_recipe_comments_returns_the_comments(
        self,
        site: Site,
        comments_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(comments_payload))
        result = _call(
            server.get_recipe_comments,
            recipe_id=42,
            max_results=1,
            helpful_only=True,
        )
        assert isinstance(result, Comments)
        assert [comment.id for comment in result.comments] == ["101"]
        assert result.comments[0].replies[0].author.is_staff
        page_input = json.loads(seen[0].content)["variables"]["input"]
        assert (page_input["first"], page_input["view"]) == (1, "READER_PICKS")

    def test_get_recipe_box_returns_the_box(
        self,
        site: Site,
        recipe_box_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(recipe_box_payload))
        result = _call(server.get_recipe_box, max_results=1)
        assert isinstance(result, RecipeBox)
        assert [recipe.id for recipe in result.recipes] == [42]
        assert seen[-1].url.path == "/api/v2/users/42/search/recipe_box_search"

    def test_get_recently_viewed_returns_recipes(self, site: Site) -> None:
        seen = site(
            _respond_with(
                [
                    {"id": 42, "name": "Soup", "url": "https://x/42", "type": "recipe"},
                    {"id": 7, "name": "Soups", "url": "/c/7", "type": "collection"},
                ],
            ),
        )
        result = _call(server.get_recently_viewed, max_results=5)
        assert isinstance(result, RecentlyViewed)
        assert [recipe.id for recipe in result.recipes] == [42]
        assert seen[-1].url.path == "/api/v5/users/me/recently_viewed"
        assert seen[-1].url.params["per_page"] == "5"

    def test_get_folders_returns_the_folders(
        self,
        site: Site,
        folders_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(folders_payload))
        result = _call(server.get_folders)
        assert isinstance(result, Folders)
        assert [folder.id for folder in result.folders] == [7, 8]
        assert seen[-1].url.path == "/api/v5/users/me/collections"

    def test_get_recipe_box_forwards_the_folder_id(
        self,
        site: Site,
        recipe_box_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(recipe_box_payload))
        _call(server.get_recipe_box, folder_id=7)
        assert seen[-1].url.params["collection_id"] == "7"

    def test_get_folder_recipes_returns_the_folder(
        self,
        site: Site,
        recipe_box_payload: dict[str, Any],
    ) -> None:
        recipe_box_payload["meta"]["total_pages"] = 1
        seen = site(_respond_with(recipe_box_payload))
        result = _call(server.get_folder_recipes, folder_id=7)
        assert isinstance(result, RecipeBox)
        assert [recipe.id for recipe in result.recipes] == [42, 43]
        assert seen[-1].url.path == "/api/v2/users/42/search/recipe_box_search"
        assert seen[-1].url.params["collection_id"] == "7"

    def test_add_folder_returns_the_folder(
        self,
        site: Site,
        folders_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(folders_payload["collections"][0]))
        result = _call(server.add_folder, name=" Soups ")
        assert isinstance(result, Folder)
        assert json.loads(seen[-1].content) == {"name": "Soups"}

    def test_rename_folder_returns_the_folder(
        self,
        site: Site,
        folders_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(folders_payload["collections"][0]))
        result = _call(server.rename_folder, folder_id=7, name="Soups")
        assert isinstance(result, Folder)
        assert seen[-1].url.path == "/api/v2/users/42/collections/7"

    def test_remove_folder_returns_the_folders_left(
        self,
        site: Site,
        folders_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(folders_payload))
        result = _call(server.remove_folder, folder_id=7)
        assert isinstance(result, Folders)
        assert [request.method for request in seen[-2:]] == ["DELETE", "GET"]

    @pytest.mark.parametrize(
        ("tool", "method"),
        [
            ("get_recipe_save_status", "GET"),
            ("add_recipe", "POST"),
            ("remove_recipe", "DELETE"),
        ],
    )
    def test_saved_recipe_tools_return_the_saved_state(
        self,
        tool: str,
        method: str,
        site: Site,
        interactions_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(interactions_payload))
        result = _call(getattr(server, tool), recipe_id=42)
        assert isinstance(result, SavedRecipe)
        assert seen[0].method == method

    def test_add_recipe_forwards_the_folder_id(
        self,
        site: Site,
        interactions_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(interactions_payload))
        _call(server.add_recipe, recipe_id=42, folder_id=7)
        assert json.loads(seen[0].content) == {"recipe_id": 42, "collection_id": 7}

    @pytest.mark.parametrize("tool", ["add_folder", "rename_folder"])
    @pytest.mark.parametrize("name", ["", "   "], ids=["empty", "blank"])
    def test_folder_tools_require_a_name(
        self,
        tool: str,
        name: str,
        site: Site,
    ) -> None:
        seen = site(lambda _request: httpx.Response(HTTPStatus.OK))
        kwargs: dict[str, Any] = {"name": name}
        if tool == "rename_folder":
            kwargs["folder_id"] = 7
        with pytest.raises(ToolError, match="required"):
            _call(getattr(server, tool), **kwargs)
        assert seen == []

    def test_other_http_errors_propagate(self, site: Site) -> None:
        site(lambda _request: httpx.Response(HTTPStatus.INTERNAL_SERVER_ERROR))
        with pytest.raises(httpx.HTTPStatusError):
            _call(server.get_recipe_box)

    def test_invalid_payload_raises_a_validation_error(self, site: Site) -> None:
        site(_respond_with({"unexpected": True}))
        with pytest.raises(ValueError, match="validation error"):
            _call(server.get_recipe, recipe_id=42)

    def test_tool_errors_reach_the_mcp_client(self) -> None:
        async def call() -> None:
            async with MCPClient(server.mcp) as client:
                await client.call_tool("auth_login", {"cookie": " "})

        with pytest.raises(ToolError, match="required"):
            asyncio.run(call())

    def test_each_tool_call_gets_its_own_client_closed_afterwards(
        self,
        site: Site,
        search_payload: dict[str, Any],
        tracked_clients: list[Client],
    ) -> None:
        site(_respond_with(search_payload))
        calls = (
            ("search_recipes", {"query": "soup"}),
            ("search_recipes", {"query": "stew"}),
        )
        _call_over_mcp(*calls)
        assert len(tracked_clients) == len(calls)
        for client in tracked_clients:
            assert client._rest_client.is_closed
            assert client._graphql_client.is_closed

    def test_every_tool_call_checks_the_subscription(
        self,
        site: Site,
        recipe_box_payload: dict[str, Any],
        identity_requests: list[httpx.Request],
    ) -> None:
        site(_respond_with(recipe_box_payload))
        calls = (("get_recipe_box", {"max_results": 1}),) * 3
        _call_over_mcp(*calls)
        assert len(identity_requests) == len(calls)


AUTH_TOOLS = {"auth_login", "auth_logout", "get_auth_status"}

LOGGED_IN_TOOLS: dict[str, dict[str, Any]] = {
    "get_search_filters": {},
    "search_recipes": {"query": "soup"},
    "get_recipe": {"recipe_id": 42},
    "get_recipe_comments": {"recipe_id": 42},
    "get_recipe_box": {},
    "get_recently_viewed": {},
    "get_folders": {},
    "get_folder_recipes": {"folder_id": 7},
    "add_folder": {"name": "Soups"},
    "rename_folder": {"folder_id": 7, "name": "Soups"},
    "remove_folder": {"folder_id": 7},
    "get_recipe_save_status": {"recipe_id": 42},
    "add_recipe": {"recipe_id": 42},
    "remove_recipe": {"recipe_id": 42},
}


class TestLoginRequired:
    def test_every_tool_but_the_auth_tools_is_covered(self) -> None:
        async def names() -> set[str]:
            async with MCPClient(server.mcp) as client:
                return {tool.name for tool in await client.list_tools()}

        assert asyncio.run(names()) - AUTH_TOOLS == set(LOGGED_IN_TOOLS)

    def test_the_server_explains_how_to_log_in(self) -> None:
        text = server.mcp.instructions or ""
        assert "NYT Cooking subscription" in text
        assert "`auth_login`" in text

    @pytest.mark.parametrize("tool", LOGGED_IN_TOOLS)
    def test_tools_refuse_until_the_user_logs_in(
        self,
        tool: str,
        site: Site,
        identity_requests: list[httpx.Request],
    ) -> None:
        seen = site(_respond_with({}))
        with pytest.raises(ToolError, match="Not logged in"):
            _call_over_mcp((tool, LOGGED_IN_TOOLS[tool]))
        assert seen == []
        assert identity_requests == []

    @pytest.mark.parametrize(
        ("cookie", "reason"),
        [
            ("expired", "does not recognise"),
            ("lapsed", "no active NYT Cooking subscription"),
        ],
    )
    def test_a_saved_cookie_nyt_no_longer_accepts_is_refused(
        self,
        cookie: str,
        reason: str,
        site: Site,
    ) -> None:
        Settings.save_credentials(cookie)
        seen = site(_respond_with({}))
        with pytest.raises(ToolError, match=reason):
            _call_over_mcp(("get_recipe", {"recipe_id": 42}))
        assert seen == []

    def test_logging_in_over_mcp_unlocks_the_tools(
        self,
        site: Site,
        recipe_payload: dict[str, Any],
    ) -> None:
        seen = site(_respond_with(recipe_payload))
        _call_over_mcp(
            ("auth_login", {"cookie": "abc"}),
            ("get_recipe", {"recipe_id": 42}),
        )
        assert seen[-1].url.path == "/api/v2/recipes/42"
        assert seen[-1].headers["cookie"] == "NYT-S=abc"

    def test_logging_in_replaces_a_cookie_nyt_no_longer_accepts(
        self,
        site: Site,
        recipe_box_payload: dict[str, Any],
    ) -> None:
        Settings.save_credentials("expired")
        seen = site(_respond_with(recipe_box_payload))
        _call_over_mcp(
            ("auth_login", {"cookie": "abc"}),
            ("get_recipe_box", {"max_results": 1}),
        )
        assert seen[-1].headers["cookie"] == "NYT-S=abc"
        assert seen[-1].url.path == "/api/v2/users/42/search/recipe_box_search"

    def test_a_rejected_login_keeps_the_saved_cookie(
        self,
        site: Site,
        recipe_payload: dict[str, Any],
    ) -> None:
        Settings.save_credentials("abc")
        seen = site(_respond_with(recipe_payload))

        async def run() -> None:
            async with MCPClient(server.mcp) as client:
                await client.call_tool("get_recipe", {"recipe_id": 42})
                failed = await client.call_tool(
                    "auth_login",
                    {"cookie": "free"},
                    raise_on_error=False,
                )
                assert failed.is_error
                await client.call_tool("get_recipe", {"recipe_id": 42})

        asyncio.run(run())
        assert [request.headers["cookie"] for request in seen] == ["NYT-S=abc"] * 2

    def test_logging_out_over_mcp_locks_the_tools(self) -> None:
        Settings.save_credentials("abc")
        with pytest.raises(ToolError, match="Not logged in"):
            _call_over_mcp(
                ("auth_logout", {}),
                ("get_recipe", {"recipe_id": 42}),
            )


class TestAuth:
    def test_login_saves_accepted_credentials(
        self,
        fake_keyring: FakeKeyring,
    ) -> None:
        result = _call_auth(server.auth_login, cookie=" abc ")
        assert result == IsAuthenticated(authenticated=True)
        assert fake_keyring.entries == {
            (CredentialStore.service, "cookie"): "abc",
        }

    @pytest.mark.parametrize(
        ("cookie", "reason"),
        [
            ("garbage", "does not recognise"),
            ("free", "no active NYT Cooking subscription"),
            ("games", "no active NYT Cooking subscription"),
            ("lapsed", "no active NYT Cooking subscription"),
        ],
        ids=["unrecognised", "free-account", "other-product", "lapsed"],
    )
    def test_only_nyt_cooking_subscribers_can_log_in(
        self,
        cookie: str,
        reason: str,
        fake_keyring: FakeKeyring,
    ) -> None:
        with pytest.raises(ToolError, match=rf"{reason}.*not saved"):
            _call_auth(server.auth_login, cookie=cookie)
        assert fake_keyring.entries == {}

    @pytest.mark.parametrize("cookie", ["", "   "], ids=["empty", "blank"])
    def test_login_requires_a_cookie(
        self,
        cookie: str,
        identity_requests: list[httpx.Request],
    ) -> None:
        with pytest.raises(ToolError, match="required"):
            _call_auth(server.auth_login, cookie=cookie)
        assert identity_requests == []

    @pytest.mark.usefixtures("signed_in")
    def test_status_checks_with_nyt(
        self,
        identity_requests: list[httpx.Request],
    ) -> None:
        assert _call_auth(server.get_auth_status) == IsAuthenticated(
            authenticated=True,
        )
        assert identity_requests[-1].url.host == "a.nytimes.com"

    def test_status_is_false_when_logged_out(
        self,
        identity_requests: list[httpx.Request],
    ) -> None:
        assert _call_auth(server.get_auth_status) == IsAuthenticated(
            authenticated=False,
        )
        assert identity_requests == []

    def test_status_is_false_once_the_subscription_lapses(self) -> None:
        Settings.save_credentials("lapsed")
        assert _call_auth(server.get_auth_status) == IsAuthenticated(
            authenticated=False,
        )

    @pytest.mark.usefixtures("signed_in")
    def test_status_rechecks_with_nyt_on_every_call(
        self,
        identity_requests: list[httpx.Request],
    ) -> None:
        calls = (("get_auth_status", {}),) * 3
        _call_over_mcp(*calls)
        assert len(identity_requests) == len(calls)

    @pytest.mark.usefixtures("signed_in")
    def test_logout_clears_the_login(self, fake_keyring: FakeKeyring) -> None:
        assert _call_auth(server.auth_logout) == IsAuthenticated(authenticated=False)
        assert fake_keyring.entries == {}

    def test_logout_keeps_a_cookie_set_in_the_environment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("NYT_COOKING_COOKIE", "abc")
        assert _call_auth(server.auth_logout) == IsAuthenticated(authenticated=True)
