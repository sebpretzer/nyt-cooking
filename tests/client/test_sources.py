from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import typer
from pydantic import ValidationError

from nyt_cooking.client.settings import (
    CredentialStore,
    Settings,
    StoredCredentialsSource,
)

if TYPE_CHECKING:
    from tests.conftest import FakeKeyring

DEFAULT_ENV_FILES = Settings.model_config.get("env_file")


def _load(**kwargs: Any) -> Settings:
    return Settings(**kwargs)


class TestStoredCredentialsSource:
    def test_empty_keychain_yields_nothing(self) -> None:
        assert StoredCredentialsSource(Settings)() == {}

    def test_returns_only_fields_that_have_entries(
        self,
        fake_keyring: FakeKeyring,
    ) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "abc"
        assert StoredCredentialsSource(Settings)() == {"cookie": "abc"}

    def test_returns_every_stored_field(self, fake_keyring: FakeKeyring) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "abc"
        assert StoredCredentialsSource(Settings)() == {"cookie": "abc"}

    def test_ignores_non_credential_fields(self, fake_keyring: FakeKeyring) -> None:
        fake_keyring.entries[(CredentialStore.service, "base_url")] = "http://x"
        fake_keyring.entries[(CredentialStore.service, "user_agent")] = "Other/1.0"
        assert StoredCredentialsSource(Settings)() == {}

    def test_falls_back_to_the_file(self) -> None:
        CredentialStore.file.write_text(json.dumps({"cookie": "abc"}))
        assert StoredCredentialsSource(Settings)() == {"cookie": "abc"}

    def test_file_beats_the_keychain(self, fake_keyring: FakeKeyring) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "from-keyring"
        CredentialStore.file.write_text(json.dumps({"cookie": "from-file"}))
        assert StoredCredentialsSource(Settings)() == {"cookie": "from-file"}

    def test_file_ignores_unknown_keys(self) -> None:
        CredentialStore.file.write_text(json.dumps({"base_url": "http://x"}))
        assert StoredCredentialsSource(Settings)() == {}

    def test_ignores_other_services(self, fake_keyring: FakeKeyring) -> None:
        fake_keyring.entries[("some-other-app", "cookie")] = "not-ours"
        assert StoredCredentialsSource(Settings)() == {}

    def test_never_writes(self, fake_keyring: FakeKeyring) -> None:
        StoredCredentialsSource(Settings)()
        assert fake_keyring.set_calls == 0

    @pytest.mark.usefixtures("no_keyring")
    def test_backend_failure_yields_nothing_and_warns(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with caplog.at_level(logging.WARNING):
            assert StoredCredentialsSource(Settings)() == {}
        assert "Could not read" in caplog.text


@pytest.mark.usefixtures("signed_in")
class TestDotenv:
    @staticmethod
    def _write(path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_unprefixed_keys_are_ignored(self, tmp_path: Path) -> None:
        env_file = self._write(tmp_path / ".env", "COOKIE=nope\nUSER_AGENT=nope\n")
        settings = _load(_env_file=env_file)
        assert settings.cookie.get_secret_value() == "abc"
        assert settings.user_agent != "nope"

    def test_unrelated_keys_do_not_raise(self, tmp_path: Path) -> None:
        env_file = self._write(tmp_path / ".env", "PATH_EXTRA=/x\nHOME_DIR=/y\n")
        assert _load(_env_file=env_file).cookie.get_secret_value() == "abc"

    def test_unknown_prefixed_key_raises(self, tmp_path: Path) -> None:
        env_file = self._write(tmp_path / ".env", "NYT_COOKING_COKIE=typo\n")
        with pytest.raises(ValidationError):
            _load(_env_file=env_file)

    def test_unknown_init_argument_raises(self) -> None:
        with pytest.raises(ValidationError):
            _load(cokie="typo")

    def test_variable_names_are_case_insensitive(self, tmp_path: Path) -> None:
        env_file = self._write(tmp_path / ".env", "nyt_cooking_user_agent=Custom/1.0\n")
        assert _load(_env_file=env_file).user_agent == "Custom/1.0"

    def test_quoted_and_commented_values(self, tmp_path: Path) -> None:
        env_file = self._write(
            tmp_path / ".env",
            '# a comment\nNYT_COOKING_COOKIE="quoted-value"\n'
            "NYT_COOKING_USER_AGENT=Custom/7\n",
        )
        settings = _load(_env_file=env_file)
        assert settings.cookie.get_secret_value() == "quoted-value"
        assert settings.user_agent == "Custom/7"

    def test_missing_file_is_not_an_error(self, tmp_path: Path) -> None:
        settings = _load(_env_file=tmp_path / "absent.env")
        assert settings.cookie.get_secret_value() == "abc"

    def test_later_file_wins_over_earlier(self, tmp_path: Path) -> None:
        home = self._write(tmp_path / "home.env", "NYT_COOKING_USER_AGENT=from-home\n")
        cwd = self._write(tmp_path / "cwd.env", "NYT_COOKING_USER_AGENT=from-cwd\n")
        assert _load(_env_file=(home, cwd)).user_agent == "from-cwd"

    def test_files_merge_when_they_set_different_fields(self, tmp_path: Path) -> None:
        home = self._write(tmp_path / "home.env", "NYT_COOKING_COOKIE=abc\n")
        cwd = self._write(tmp_path / "cwd.env", "NYT_COOKING_USER_AGENT=Custom/42\n")
        settings = _load(_env_file=(home, cwd))
        assert settings.cookie.get_secret_value() == "abc"
        assert settings.user_agent == "Custom/42"

    def test_default_search_path_is_home_config_then_cwd(self) -> None:
        home_env = Path(typer.get_app_dir("nyt-cooking")) / ".env"
        assert (home_env, ".env") == DEFAULT_ENV_FILES

    def test_default_config_picks_up_dotenv_in_cwd(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(
            Settings,
            "model_config",
            {
                **Settings.model_config,
                "env_file": (tmp_path / "no-home" / ".env", Path(".env")),
            },
        )
        self._write(tmp_path / ".env", "NYT_COOKING_USER_AGENT=from-cwd\n")
        assert Settings().user_agent == "from-cwd"


class TestEnvironment:
    def test_blank_env_var_falls_through_to_keyring(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_keyring: FakeKeyring,
    ) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "stored"
        monkeypatch.setenv("NYT_COOKING_COOKIE", "")
        assert Settings().cookie.get_secret_value() == "stored"

    def test_blank_env_var_never_overwrites_the_keychain(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_keyring: FakeKeyring,
    ) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "stored"
        monkeypatch.setenv("NYT_COOKING_COOKIE", "")
        Settings()
        assert fake_keyring.entries[(CredentialStore.service, "cookie")] == "stored"
        assert fake_keyring.set_calls == 0

    def test_blank_dotenv_value_falls_through_too(
        self,
        fake_keyring: FakeKeyring,
        tmp_path: Path,
    ) -> None:
        fake_keyring.entries[(CredentialStore.service, "cookie")] = "stored"
        env_file = tmp_path / ".env"
        env_file.write_text("NYT_COOKING_COOKIE=\n")
        assert _load(_env_file=env_file).cookie.get_secret_value() == "stored"
