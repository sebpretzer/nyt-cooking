from __future__ import annotations

import copy
import json
import os
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import httpx
import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.backends import fail
from keyring.errors import PasswordDeleteError

from nyt_cooking.client import client as client_module
from nyt_cooking.client.settings import CredentialStore, Settings

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    Handler = Callable[[httpx.Request], httpx.Response]
    Site = Callable[[Handler], list[httpx.Request]]


class FakeKeyring(KeyringBackend):
    priority = 1  # pyright: ignore[reportAssignmentType]

    def __init__(self) -> None:
        super().__init__()
        self.entries: dict[tuple[str, str], str] = {}
        self.set_calls = 0

    def get_password(self, service: str, username: str) -> str | None:
        return self.entries.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.set_calls += 1
        self.entries[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        if (service, username) not in self.entries:
            raise PasswordDeleteError(username)
        del self.entries[(service, username)]


@pytest.fixture(autouse=True)
def fake_keyring() -> Iterator[FakeKeyring]:
    previous = keyring.get_keyring()
    backend = FakeKeyring()
    keyring.set_keyring(backend)
    yield backend
    keyring.set_keyring(previous)


@pytest.fixture
def no_keyring() -> None:
    keyring.set_keyring(fail.Keyring())


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in list(os.environ):
        if name.startswith("NYT_COOKING_"):
            monkeypatch.delenv(name)
    monkeypatch.setattr(
        Settings,
        "model_config",
        {**Settings.model_config, "env_file": None},
    )
    monkeypatch.setattr(CredentialStore, "file", tmp_path / "credentials.json")
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def make_settings() -> Callable[..., Settings]:
    def _make(**kwargs: Any) -> Settings:
        return Settings(**kwargs)

    return _make


def _subscription(*entitlements: str, active: bool = True) -> dict[str, Any]:
    return {
        "status": "ACTIVE" if active else "EXPIRED",
        "hasActiveEntitlements": active,
        "entitlements": list(entitlements),
        "subscriptionName": "Test Access",
    }


_USERS: dict[str, dict[str, Any]] = {
    "abc": {
        "type": "sub",
        "regiId": 42,
        "subInfo": {"subscriptions": [_subscription("MM", "CKG", "XWD")]},
    },
    "free": {"type": "regi", "regiId": 43, "subInfo": {"modified": 0}},
    "games": {
        "type": "sub",
        "regiId": 44,
        "subInfo": {"subscriptions": [_subscription("XWD")]},
    },
    "lapsed": {
        "type": "sub",
        "regiId": 45,
        "subInfo": {"subscriptions": [_subscription("CKG", active=False)]},
    },
}


def nyt_identity(request: httpx.Request) -> httpx.Response:
    """Answer NYT's identity endpoint for the test cookies in `_USERS`.

    `abc` is an NYT Cooking subscriber, `free` a free account, `games` a Games-only
    subscriber and `lapsed` a lapsed NYT Cooking subscriber. Any other cookie is
    unrecognised.
    """
    cookies = request.headers.get("cookie", "").split("; ")
    nyt_s = next(
        (
            cookie.removeprefix("NYT-S=")
            for cookie in cookies
            if cookie.startswith("NYT-S=")
        ),
        "",
    )
    user = _USERS.get(nyt_s, {"type": "anon", "subInfo": {"modified": 0}})
    return httpx.Response(HTTPStatus.OK, json={"user": user})


@pytest.fixture
def nyt_users() -> dict[str, dict[str, Any]]:
    return _USERS


@pytest.fixture
def identity_requests() -> list[httpx.Request]:
    return []


@pytest.fixture
def site(
    monkeypatch: pytest.MonkeyPatch,
    identity_requests: list[httpx.Request],
) -> Site:
    def install(handler: Handler) -> list[httpx.Request]:
        seen: list[httpx.Request] = []

        def recording(request: httpx.Request) -> httpx.Response:
            if request.url.host == "a.nytimes.com":
                identity_requests.append(request)
                return nyt_identity(request)
            seen.append(request)
            return handler(request)

        monkeypatch.setattr(
            client_module.httpx,
            "Client",
            partial(httpx.Client, transport=httpx.MockTransport(recording)),
        )
        return seen

    return install


@pytest.fixture(autouse=True)
def offline(site: Site) -> None:
    site(lambda _request: httpx.Response(HTTPStatus.NOT_FOUND))


@pytest.fixture
def signed_in() -> None:
    Settings.save_credentials("abc")


_RECIPE: dict[str, Any] = {
    "id": 42,
    "name": "Weeknight Test Soup",
    "byline": "ADA TESTER",
    "content_attribution": {"card_byline": "Ada Tester"},
    "url": "https://cooking.nytimes.com/recipes/42-weeknight-test-soup",
    "yield": "4 servings",
    "cooking_time": {"display": "40 minutes", "minutes": 40},
    "prep_time": {"display": "", "minutes": None},
    "cook_time": {"display": "30 minutes", "minutes": 30},
    "rating": {"total": 12, "value": 4.25, "distribution": {"5": 12}},
    "topnote": {"content": "<p>A <strong>simple</strong> soup.</p>"},
    "image": {
        "caption": "",
        "credit": "Test Kitchen",
        "crops": [
            {"name": "small", "width": 100, "height": 50, "url": "https://img/s.jpg"},
            {"name": "large", "width": 800, "height": 400, "url": "https://img/l.jpg"},
        ],
    },
    "parts": [
        {
            "name": "",
            "ingredients": [
                {"display_quantity": "2", "display_text": "cups stock"},
                {"display_quantity": "", "display_text": "Salt"},
            ],
        },
        {
            "name": "For the topping",
            "ingredients": [
                {
                    "display_quantity": "1",
                    "display_text": 'lemon (<a href="/recipes/1">zested</a>)',
                },
            ],
        },
    ],
    "directions": [
        {
            "name": "",
            "steps": [
                {"number": 1, "description": "Warm the stock."},
                {"number": 2, "description": "Season <em>to taste</em>."},
            ],
        },
    ],
    "notes": [],
    "suggestions": [],
}

_SEARCH: dict[str, Any] = {
    "query": "soup",
    "results": [
        {
            "recipe": {
                "id": 42,
                "name": "Weeknight Test Soup",
                "byline": "Ada Tester",
                "cooking_time": "40 minutes",
                "image": None,
                "has_video": False,
                "type": "recipe",
            },
        },
        {"collection": {"id": 7, "name": "Soups"}},
        {
            "recipe": {
                "id": 43,
                "name": "Plain Broth",
                "byline": "",
                "cooking_time": None,
                "type": "recipe",
            },
        },
    ],
    "pagination": {"total": 2, "start": 1, "end": 2, "page": 1, "max_page": 1},
}


@pytest.fixture
def recipe_payload() -> dict[str, Any]:
    return copy.deepcopy(_RECIPE)


@pytest.fixture
def search_payload() -> dict[str, Any]:
    return copy.deepcopy(_SEARCH)


_SEARCH_PAGE_PROPS: dict[str, Any] = {
    "query": "soup",
    "size": 30,
    "filterCounts": {"dinner": 30, "drinks": 4, "five ingredient": 2, "sheet-pan": 5},
    "cookTimeCounts": {"20": 6, "30": 11, "45": 20, "60": 28},
    "topRatedCount": 12,
    "results": [],
}


def _search_page(props: dict[str, Any]) -> str:
    data = json.dumps({"props": {"pageProps": props}, "buildId": "1.0-test"})
    return (
        "<html><body><p>Soup</p>"
        f'<script id="__NEXT_DATA__" type="application/json">{data}</script>'
        "</body></html>"
    )


@pytest.fixture
def search_page_props() -> dict[str, Any]:
    return copy.deepcopy(_SEARCH_PAGE_PROPS)


@pytest.fixture
def search_page_html(search_page_props: dict[str, Any]) -> str:
    return _search_page(search_page_props)


_RECIPE_BOX: dict[str, Any] = {
    "type": "Search",
    "collectables_count": 3,
    "collectables": [
        {
            "id": 42,
            "name": "Weeknight Test Soup",
            "byline": "ADA TESTER",
            "content_attribution": {"card_byline": "Ada Tester"},
            "url": "https://cooking.nytimes.com/recipes/42-weeknight-test-soup",
            "yield": "4  servings",
            "cooking_time": {"display": "40 minutes", "minutes": "40.0"},
            "type": "recipe",
        },
        {"id": 7, "name": "Soups", "url": "/collections/7", "type": "collection"},
        {
            "id": 43,
            "name": "Plain Broth",
            "url": "https://cooking.nytimes.com/recipes/43-plain-broth",
            "type": "recipe",
        },
    ],
    "meta": {
        "current_page": 1,
        "next_page": 2,
        "prev_page": None,
        "total_pages": 2,
        "total_count": 3,
    },
}


@pytest.fixture
def recipe_box_payload() -> dict[str, Any]:
    return copy.deepcopy(_RECIPE_BOX)


_FOLDERS: dict[str, Any] = {
    "collections": [
        {
            "id": 7,
            "slug": "7-soups",
            "name": "Soups",
            "description": "",
            "type": "collection",
            "url": "https://cooking.nytimes.com/42/7-soups",
            "collectables_count": 2,
            "image": None,
        },
        {
            "id": 8,
            "slug": "8-stews",
            "name": "Stews",
            "description": "<p>Slow and <em>low</em></p>",
            "type": "collection",
            "url": "https://cooking.nytimes.com/42/8-stews",
            "collectables_count": 0,
            "image": None,
        },
    ],
    "meta": {"current_page": 1, "total_pages": 1, "total_count": 2},
}


@pytest.fixture
def folders_payload() -> dict[str, Any]:
    return copy.deepcopy(_FOLDERS)


_INTERACTIONS: dict[str, Any] = {
    "id": 42,
    "type": "recipe",
    "saved": True,
    "cooked": False,
    "rating": None,
    "name": "Weeknight Test Soup",
    "collection_ids": [999, 7],
    "private_notes": [],
    "interactions_recipe_ids_map": {},
}


@pytest.fixture
def interactions_payload() -> dict[str, Any]:
    return copy.deepcopy(_INTERACTIONS)


_COMMENTS: dict[str, Any] = {
    "data": {
        "communityComments": {
            "summary": {"totalCount": 4, "totalReadersPicks": 1},
            "pageInfo": {"endCursor": "cursor-1", "hasNextPage": True},
            "edges": [
                {
                    "cursor": "cursor-0",
                    "node": {
                        "comment": {
                            "id": "101",
                            "text": "Less broth.<br/><br/>1. More <b>mint</b>.",
                            "submittedAt": "2026-09-22T02:04:06Z",
                            "recommendedCount": 22,
                            "author": {
                                "name": "Ada",
                                "location": "Chicago",
                                "title": "",
                                "isReporter": False,
                            },
                        },
                        "replies": [
                            {
                                "id": "102",
                                "text": "It freezes beautifully.",
                                "submittedAt": "2026-09-23T10:00:00Z",
                                "recommendedCount": 3,
                                "author": {
                                    "name": "Test Editor",
                                    "location": None,
                                    "title": "Staff Editor",
                                    "isReporter": True,
                                },
                            },
                        ],
                    },
                },
                {
                    "cursor": "cursor-1",
                    "node": {
                        "comment": {
                            "id": "103",
                            "text": "Delicious.",
                            "submittedAt": "2026-09-21T03:23:07Z",
                            "recommendedCount": 0,
                            "author": {"name": "Grace", "isReporter": False},
                        },
                        "replies": [],
                    },
                },
            ],
        },
    },
}


@pytest.fixture
def comments_payload() -> dict[str, Any]:
    return copy.deepcopy(_COMMENTS)
