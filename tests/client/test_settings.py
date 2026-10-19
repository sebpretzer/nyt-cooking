from __future__ import annotations

import json
import logging
import stat
from collections.abc import Callable
from typing import TYPE_CHECKING

import keyring
import pytest
from keyring.errors import KeyringError
from pydantic import ValidationError

from nyt_cooking.client.settings import CredentialStore, Settings

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import FakeKeyring

MakeSettings = Callable[..., Settings]
OWNER_ONLY = 0o600
OTHER_PUBLIC_KEY = "other-public-key"


def _cookie(settings: Settings) -> str:
    return settings.cookie.get_secret_value()


class TestPrecedence:
    def test_cookie_is_required(self, make_settings: MakeSettings) -> None:
        with pytest.raises(ValidationError, match="cookie"):
            make_settings()

    def test_keyring_is_the_default_source(
        self,
        make_settings: MakeSettings,
        fake_keyring: FakeKeyring,
    ) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "from-keyring"
        settings = make_settings()
        assert _cookie(settings) == "from-keyring"

    def test_env_beats_keyring(
        self,
        make_settings: MakeSettings,
        fake_keyring: FakeKeyring,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "from-keyring"
        monkeypatch.setenv("NYT_COOKING_COOKIE", "from-env")
        assert _cookie(make_settings()) == "from-env"

    def test_dotenv_beats_keyring(
        self,
        make_settings: MakeSettings,
        fake_keyring: FakeKeyring,
        tmp_path: Path,
    ) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "from-keyring"
        env_file = tmp_path / ".env"
        env_file.write_text("NYT_COOKING_COOKIE=from-dotenv\n")
        assert _cookie(make_settings(_env_file=env_file)) == "from-dotenv"

    def test_env_beats_dotenv(
        self,
        make_settings: MakeSettings,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("NYT_COOKING_COOKIE=from-dotenv\n")
        monkeypatch.setenv("NYT_COOKING_COOKIE", "from-env")
        assert _cookie(make_settings(_env_file=env_file)) == "from-env"

    def test_init_beats_everything(
        self,
        make_settings: MakeSettings,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("NYT_COOKING_COOKIE=from-dotenv\n")
        monkeypatch.setenv("NYT_COOKING_COOKIE", "from-env")
        settings = make_settings(cookie="from-init", _env_file=env_file)
        assert _cookie(settings) == "from-init"

    @pytest.mark.usefixtures("signed_in")
    def test_dotenv_ignores_unrelated_keys(
        self,
        make_settings: MakeSettings,
        tmp_path: Path,
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("SOMETHING_ELSE=1\nNYT_COOKING_USER_AGENT=Custom/7\n")
        assert make_settings(_env_file=env_file).user_agent == "Custom/7"


@pytest.mark.usefixtures("signed_in")
class TestApis:
    def test_each_api_has_its_own_defaults(self, make_settings: MakeSettings) -> None:
        settings = make_settings()
        assert str(settings.rest.base_url) == "https://cooking.nytimes.com/"
        assert str(settings.graphql.url) == (
            "https://samizdat-graphql.nytimes.com/graphql/v2"
        )

    def test_each_api_has_its_own_headers(self, make_settings: MakeSettings) -> None:
        settings = make_settings()
        assert settings.rest.headers == {
            "Accept": "*/*",
            "x-cooking-api": "cooking-frontend",
        }
        assert set(settings.graphql.headers) == {
            "nyt-app-type",
            "nyt-app-version",
            "nyt-token",
        }

    def test_env_reaches_into_each_api(
        self,
        make_settings: MakeSettings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("NYT_COOKING_REST__BASE_URL", "http://localhost:8123")
        monkeypatch.setenv("NYT_COOKING_GRAPHQL__TOKEN", OTHER_PUBLIC_KEY)
        settings = make_settings()
        assert str(settings.rest.base_url) == "http://localhost:8123/"
        assert settings.graphql.token == OTHER_PUBLIC_KEY
        assert settings.graphql.app_type == "cooking-frontend-client"

    def test_dotenv_reaches_into_each_api(
        self,
        make_settings: MakeSettings,
        tmp_path: Path,
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OTHER__SETTING=1\n"
            "NYT_COOKING_REST__BASE_URL=http://localhost:8123\n"
            "NYT_COOKING_GRAPHQL__APP_VERSION=2.0.0\n",
        )
        settings = make_settings(_env_file=env_file)
        assert str(settings.rest.base_url) == "http://localhost:8123/"
        assert settings.graphql.app_version == "2.0.0"

    def test_init_sets_one_api_without_touching_the_other(
        self,
        make_settings: MakeSettings,
    ) -> None:
        settings = make_settings(graphql={"token": OTHER_PUBLIC_KEY})
        assert settings.graphql.token == OTHER_PUBLIC_KEY
        assert str(settings.rest.base_url) == "https://cooking.nytimes.com/"

    def test_unknown_api_settings_are_rejected(
        self,
        make_settings: MakeSettings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("NYT_COOKING_GRAPHQL__TOKN", "typo")
        with pytest.raises(ValidationError):
            make_settings()


class TestSaving:
    def test_saves_to_the_keychain(self, fake_keyring: FakeKeyring) -> None:
        Settings.save_credentials("abc")
        assert fake_keyring.entries == {
            (CredentialStore.service, "cookie"): "abc",
        }
        assert not CredentialStore.file.exists()

    def test_saved_credentials_are_loaded(self, make_settings: MakeSettings) -> None:
        Settings.save_credentials("abc")
        settings = make_settings()
        assert _cookie(settings) == "abc"

    def test_saving_replaces_previous_credentials(
        self,
        make_settings: MakeSettings,
    ) -> None:
        Settings.save_credentials("old")
        Settings.save_credentials("new")
        settings = make_settings()
        assert _cookie(settings) == "new"

    def test_reading_settings_never_writes(
        self,
        make_settings: MakeSettings,
        fake_keyring: FakeKeyring,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("NYT_COOKING_COOKIE", "from-env")
        make_settings(cookie="from-init")
        assert fake_keyring.set_calls == 0
        assert not CredentialStore.file.exists()

    def test_keychain_save_removes_a_stale_file(self) -> None:
        CredentialStore.file.write_text(json.dumps({"cookie": "stale"}))
        Settings.save_credentials("abc")
        assert not CredentialStore.file.exists()


@pytest.mark.usefixtures("no_keyring")
class TestFileFallback:
    def test_saves_to_a_private_file_and_warns(self) -> None:
        with pytest.warns(UserWarning, match="keychain is unavailable"):
            Settings.save_credentials("abc")
        assert json.loads(CredentialStore.file.read_text()) == {
            "cookie": "abc",
        }
        assert stat.S_IMODE(CredentialStore.file.stat().st_mode) == OWNER_ONLY

    def test_overwriting_a_permissive_file_makes_it_private(self) -> None:
        CredentialStore.file.write_text(json.dumps({"cookie": "old"}))
        CredentialStore.file.chmod(0o644)
        with pytest.warns(UserWarning, match="keychain is unavailable"):
            Settings.save_credentials("abc")
        assert stat.S_IMODE(CredentialStore.file.stat().st_mode) == OWNER_ONLY

    def test_file_credentials_are_loaded(self, make_settings: MakeSettings) -> None:
        with pytest.warns(UserWarning, match="keychain is unavailable"):
            Settings.save_credentials("abc")
        settings = make_settings()
        assert _cookie(settings) == "abc"

    def test_read_failure_is_a_warning_not_an_error(
        self,
        make_settings: MakeSettings,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with (
            caplog.at_level(logging.WARNING),
            pytest.raises(ValidationError, match="cookie"),
        ):
            make_settings()
        assert "keychain" in caplog.text

    def test_unreadable_file_is_ignored(self, make_settings: MakeSettings) -> None:
        CredentialStore.file.write_text("not json")
        with pytest.raises(ValidationError, match="cookie"):
            make_settings()

    def test_env_still_works(
        self,
        make_settings: MakeSettings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("NYT_COOKING_COOKIE", "from-env")
        assert _cookie(make_settings()) == "from-env"

    def test_clear_removes_the_file(self) -> None:
        with pytest.warns(UserWarning, match="keychain is unavailable"):
            Settings.save_credentials("abc")
        assert Settings.clear_credentials() is True
        assert not CredentialStore.file.exists()


def test_failed_keychain_replacement_does_not_restore_the_old_cookie(
    make_settings: MakeSettings,
    fake_keyring: FakeKeyring,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_keyring.entries[(CredentialStore.service, "cookie")] = "old"

    def refuse(*_args: object) -> None:
        raise KeyringError

    monkeypatch.setattr(keyring, "set_password", refuse)
    with pytest.warns(UserWarning, match="keychain is unavailable"):
        Settings.save_credentials("new")
    assert _cookie(make_settings()) == "new"


class TestClearing:
    def test_removes_keychain_entries(self, fake_keyring: FakeKeyring) -> None:
        Settings.save_credentials("abc")
        assert Settings.clear_credentials() is True
        assert fake_keyring.entries == {}

    def test_removes_both_stores(self, fake_keyring: FakeKeyring) -> None:
        Settings.save_credentials("abc")
        CredentialStore.file.write_text(json.dumps({"cookie": "other"}))
        assert Settings.clear_credentials() is True
        assert fake_keyring.entries == {}
        assert not CredentialStore.file.exists()

    def test_leaves_non_credential_entries_alone(
        self,
        fake_keyring: FakeKeyring,
    ) -> None:
        fake_keyring.entries[(CredentialStore.service, "base_url")] = "http://x"
        assert Settings.clear_credentials() is False
        assert fake_keyring.entries == {
            (CredentialStore.service, "base_url"): "http://x",
        }

    def test_when_empty_returns_false_without_warning(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with caplog.at_level(logging.WARNING):
            assert Settings.clear_credentials() is False
        assert caplog.text == ""

    def test_env_credentials_are_unaffected(
        self,
        make_settings: MakeSettings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("NYT_COOKING_COOKIE", "from-env")
        Settings.clear_credentials()
        assert _cookie(make_settings()) == "from-env"


def test_cookie_is_not_leaked_in_repr(make_settings: MakeSettings) -> None:
    settings = make_settings(cookie="super-secret")
    assert "super-secret" not in repr(settings)
    assert "super-secret" not in str(settings)
