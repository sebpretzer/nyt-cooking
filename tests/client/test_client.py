from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from pydantic import ValidationError

from nyt_cooking.client import Client
from nyt_cooking.client.settings import CredentialStore

if TYPE_CHECKING:
    from tests.conftest import FakeKeyring, Handler, Site


def _nyt_s(client: Client) -> str | None:
    rest, graphql = (
        http_client.cookies.get("NYT-S")
        for http_client in (client._rest_client, client._graphql_client)
    )
    assert rest == graphql
    return rest


def _empty_box(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        HTTPStatus.OK,
        json={
            "collectables": [],
            "meta": {"current_page": 1, "total_pages": 1, "total_count": 0},
        },
    )


class TestCookie:
    def test_defaults_come_from_the_keychain(self, fake_keyring: FakeKeyring) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "abc"
        assert _nyt_s(Client()) == "abc"

    def test_env_overrides_the_keychain(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_keyring: FakeKeyring,
    ) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "stored"
        monkeypatch.setenv("NYT_COOKING_COOKIE", "abc")
        assert _nyt_s(Client()) == "abc"

    def test_init_cookie_goes_straight_to_settings(self) -> None:
        assert _nyt_s(Client(cookie="abc")) == "abc"

    def test_explicit_cookie_is_never_saved(self, fake_keyring: FakeKeyring) -> None:
        Client(cookie="abc")
        assert fake_keyring.set_calls == 0

    def test_cookie_is_the_first_positional_argument(self) -> None:
        timeout = 10
        client = Client("abc", timeout=timeout)
        assert _nyt_s(client) == "abc"
        assert client._rest_client.timeout == httpx.Timeout(timeout)

    def test_is_required(self, identity_requests: list[httpx.Request]) -> None:
        with pytest.raises(ValidationError, match="cookie"):
            Client()
        assert identity_requests == []


class TestSubscription:
    def test_creating_a_client_checks_the_cookie_with_nyt(
        self,
        identity_requests: list[httpx.Request],
    ) -> None:
        client = Client("abc")
        (identity,) = identity_requests
        assert str(identity.url) == "https://a.nytimes.com/svc/nyt/data-layer"
        assert identity.headers["cookie"] == "NYT-S=abc"
        assert client.regi_id == "42"

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
    def test_only_nyt_cooking_subscribers_get_a_client(
        self,
        cookie: str,
        reason: str,
        site: Site,
    ) -> None:
        seen = site(_empty_box)
        with pytest.raises(ValueError, match=reason):
            Client(cookie)
        assert seen == []

    def test_the_check_is_made_once(
        self,
        site: Site,
        identity_requests: list[httpx.Request],
    ) -> None:
        site(_empty_box)
        with Client("abc") as client:
            client.get_recipe_box()
            client.get_folders()
        assert len(identity_requests) == 1


class TestRecipeBox:
    def test_uses_the_regi_id_nyt_reports(self, site: Site) -> None:
        seen = site(_empty_box)
        with Client("abc") as client:
            client.get_recipe_box(per_page=1)
        (box,) = seen
        assert box.url.path == "/api/v2/users/42/search/recipe_box_search"

    def test_folder_id_limits_the_search_to_the_folder(self, site: Site) -> None:
        seen = site(_empty_box)
        with Client("abc") as client:
            client.get_recipe_box(folder_id=7)
        assert seen[-1].url.params["collection_id"] == "7"

    def test_no_folder_id_searches_the_whole_box(self, site: Site) -> None:
        seen = site(_empty_box)
        with Client("abc") as client:
            client.get_recipe_box()
        assert "collection_id" not in seen[-1].url.params

    def test_folder_recipes_fetch_every_page_of_the_folder(
        self,
        site: Site,
        recipe_box_payload: dict[str, Any],
    ) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            page = int(request.url.params["page"])
            meta = {**recipe_box_payload["meta"], "current_page": page}
            return httpx.Response(
                HTTPStatus.OK,
                json={**recipe_box_payload, "meta": meta},
            )

        seen = site(respond)
        with Client("abc") as client:
            folder = client.get_folder_recipes(7)
        assert [recipe.id for recipe in folder.recipes] == [42, 43, 42, 43]
        searches = [request.url.params for request in seen]
        assert [params["page"] for params in searches] == ["1", "2"]
        assert {params["collection_id"] for params in searches} == {"7"}


def _folders_site(folders: dict[str, Any]) -> Handler:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            return httpx.Response(HTTPStatus.NO_CONTENT)
        if request.method in {"POST", "PUT"}:
            body = json.loads(request.content)
            folder = {**folders["collections"][0], "name": body["name"]}
            return httpx.Response(HTTPStatus.CREATED, json=folder)
        return httpx.Response(HTTPStatus.OK, json=folders)

    return respond


class TestFolders:
    def test_get_lists_every_folder_alphabetically(
        self,
        site: Site,
        folders_payload: dict[str, Any],
    ) -> None:
        seen = site(_folders_site(folders_payload))
        with Client("abc") as client:
            folders = client.get_folders()
        assert [folder.name for folder in folders.folders] == ["Soups", "Stews"]
        assert seen[-1].url.path == "/api/v5/users/me/collections"
        assert dict(seen[-1].url.params) == {"sort": "alphanumeric", "per_page": "9999"}

    def test_create_posts_the_name(
        self,
        site: Site,
        folders_payload: dict[str, Any],
    ) -> None:
        seen = site(_folders_site(folders_payload))
        with Client("abc") as client:
            folder = client.create_folder("Weeknight")
        assert folder.name == "Weeknight"
        assert (seen[-1].method, seen[-1].url.path) == (
            "POST",
            "/api/v5/users/me/collections",
        )
        assert json.loads(seen[-1].content) == {"name": "Weeknight"}

    def test_rename_puts_the_name_under_the_regi_id(
        self,
        site: Site,
        folders_payload: dict[str, Any],
    ) -> None:
        seen = site(_folders_site(folders_payload))
        with Client("abc") as client:
            folder = client.rename_folder(7, "Brothy")
        assert folder.name == "Brothy"
        assert (seen[-1].method, seen[-1].url.path) == (
            "PUT",
            "/api/v2/users/42/collections/7",
        )
        assert json.loads(seen[-1].content) == {"name": "Brothy"}

    def test_delete_returns_the_folders_left(
        self,
        site: Site,
        folders_payload: dict[str, Any],
    ) -> None:
        seen = site(_folders_site(folders_payload))
        with Client("abc") as client:
            folders = client.delete_folder(7)
        assert [folder.id for folder in folders.folders] == [7, 8]
        delete, listing = seen[-2:]
        assert (delete.method, delete.url.path) == (
            "DELETE",
            "/api/v2/users/42/collections/7",
        )
        assert listing.url.path == "/api/v5/users/me/collections"


def _saving_site(
    interactions: dict[str, Any],
    folders: dict[str, Any],
) -> Handler:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(HTTPStatus.CREATED)
        if request.method == "DELETE":
            return httpx.Response(HTTPStatus.NO_CONTENT)
        if request.url.path.endswith("/interactions"):
            return httpx.Response(HTTPStatus.OK, json=interactions)
        return httpx.Response(HTTPStatus.OK, json=folders)

    return respond


class TestSavedRecipes:
    @pytest.fixture
    def seen(
        self,
        site: Site,
        interactions_payload: dict[str, Any],
        folders_payload: dict[str, Any],
    ) -> list[httpx.Request]:
        return site(_saving_site(interactions_payload, folders_payload))

    def test_get_keeps_only_the_users_folders(self, seen: list[httpx.Request]) -> None:
        with Client("abc") as client:
            saved = client.get_saved_recipe(42)
        assert saved.saved
        assert [folder.id for folder in saved.folders] == [7]
        assert seen[0].url.path == "/api/v5/users/me/recipes/42/interactions"

    def test_save_posts_the_recipe(self, seen: list[httpx.Request]) -> None:
        with Client("abc") as client:
            client.save_recipe(42)
        save = seen[0]
        assert (save.method, save.url.path) == (
            "POST",
            "/api/v5/users/me/saved_recipes",
        )
        assert json.loads(save.content) == {"recipe_id": 42}

    def test_save_into_a_folder_sends_the_folder(
        self,
        seen: list[httpx.Request],
    ) -> None:
        with Client("abc") as client:
            client.save_recipe(42, folder_id=7)
        assert json.loads(seen[0].content) == {"recipe_id": 42, "collection_id": 7}

    def test_unsave_sends_no_body(self, seen: list[httpx.Request]) -> None:
        with Client("abc") as client:
            client.unsave_recipe(42)
        unsave = seen[0]
        assert (unsave.method, unsave.url.path) == (
            "DELETE",
            "/api/v5/users/me/saved_recipes/42",
        )
        assert unsave.content == b""

    def test_unsave_from_a_folder_sends_the_folder(
        self,
        seen: list[httpx.Request],
    ) -> None:
        with Client("abc") as client:
            client.unsave_recipe(42, folder_id=7)
        assert json.loads(seen[0].content) == {"collection_id": 7, "recipe_id": 42}

    def test_writes_return_the_state_afterwards(
        self,
        seen: list[httpx.Request],
    ) -> None:
        with Client("abc") as client:
            saved = client.save_recipe(42)
        assert saved.name == "Weeknight Test Soup"
        assert [request.url.path for request in seen[1:]] == [
            "/api/v5/users/me/recipes/42/interactions",
            "/api/v5/users/me/collections",
        ]

    def test_unsave_from_a_folder_it_is_not_in_raises(self, site: Site) -> None:
        site(lambda _request: httpx.Response(HTTPStatus.NOT_FOUND))
        with Client("abc") as client, pytest.raises(httpx.HTTPStatusError):
            client.unsave_recipe(42, folder_id=7)
