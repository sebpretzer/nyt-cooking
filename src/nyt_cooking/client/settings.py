from __future__ import annotations

import json
import logging
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import keyring
import typer
from keyring.errors import KeyringError, PasswordDeleteError
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

logger = logging.getLogger(__name__)

APP_DIR = Path(typer.get_app_dir("nyt-cooking"))


class CredentialStore:
    """Where a saved `NYT-S` cookie lives.

    The system keychain is used when available. Otherwise the cookie goes to
    `credentials.json` in the app config directory, readable only by its owner,
    with a warning. Keychain errors are logged rather than raised.

    ??? example "Example"
        ```python
        from nyt_cooking.client.settings import CredentialStore

        CredentialStore.save("0^CB...")
        print(CredentialStore.read("cookie"))
        ```

        will output:
        ```text
        0^CB...
        ```
    """

    service: ClassVar[str] = "nyt-cooking"
    fields: ClassVar[tuple[str, ...]] = ("cookie",)
    file: ClassVar[Path] = APP_DIR / "credentials.json"

    @classmethod
    def read(cls, name: str) -> str | None:
        """Read a saved credential, from the file first and then the keychain.

        The file only exists when the newest save could not use the keychain, so it
        takes precedence over any older keychain entry.

        Args:
            name (str): The credential's field name, such as `cookie`.

        Returns:
            str | None: The saved value, or `None` if nothing is saved.
        """
        saved = cls._read_file().get(name)
        if saved is not None:
            return saved
        try:
            return keyring.get_password(cls.service, name)
        except KeyringError as exc:
            logger.warning("Could not read %r from the keychain: %s", name, exc)
            return None

    @classmethod
    def save(cls, cookie: str) -> None:
        """Save the cookie, replacing any previously saved one.

        Args:
            cookie (str): Value of the `NYT-S` cookie.

        Warns:
            UserWarning: If the keychain is unavailable and the file is used.
        """
        values = {"cookie": cookie}
        try:
            for name, value in values.items():
                keyring.set_password(cls.service, name, value)
        except KeyringError as exc:
            msg = (
                f"The system keychain is unavailable ({exc}); saving credentials "
                f"to {cls.file} instead."
            )
            logger.warning(msg)
            warnings.warn(msg, UserWarning, stacklevel=3)
            cls._write_file(values)
        else:
            cls.file.unlink(missing_ok=True)

    @classmethod
    def clear(cls) -> bool:
        """Remove the saved cookie from both the keychain and the file.

        Returns:
            bool: Whether anything was removed.
        """
        removed = False
        for name in cls.fields:
            try:
                keyring.delete_password(cls.service, name)
            except PasswordDeleteError:
                logger.debug("No %r entry in the keychain to delete", name)
            except KeyringError as exc:
                logger.warning("Could not delete %r from the keychain: %s", name, exc)
            else:
                removed = True
        if cls.file.exists():
            cls.file.unlink()
            removed = True
        return removed

    @classmethod
    def _read_file(cls) -> dict[str, str]:
        try:
            data = json.loads(cls.file.read_text())
        except (OSError, ValueError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {
            name: value
            for name, value in data.items()
            if name in cls.fields and isinstance(value, str)
        }

    @classmethod
    def _write_file(cls, values: dict[str, str]) -> None:
        cls.file.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(cls.file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as handle:
            json.dump(values, handle)


class StoredCredentialsSource(PydanticBaseSettingsSource):
    """Settings source that reads the saved cookie from `CredentialStore`.

    It only reads; saving happens explicitly through `Settings.save_credentials`.
    """

    def get_field_value(
        self,
        field: FieldInfo,  # noqa: ARG002
        field_name: str,
    ) -> tuple[Any, str, bool]:
        """Read a field's saved value.

        Args:
            field (FieldInfo): The field's definition, unused.
            field_name (str): The field name.

        Returns:
            tuple[Any, str, bool]: The value, the field name, and `False` because
                values are never complex.
        """
        return CredentialStore.read(field_name), field_name, False

    def __call__(self) -> dict[str, Any]:
        """Load the saved credentials.

        Returns:
            dict[str, Any]: Each saved credential, keyed by field name.
        """
        data: dict[str, Any] = {}
        for name in CredentialStore.fields:
            field = self.settings_cls.model_fields[name]
            value, key, _ = self.get_field_value(field, name)
            if value is not None:
                data[key] = value
        return data


class PrefixedDotEnvSource(PydanticBaseSettingsSource):
    """Settings source that reads `.env` files, ignoring unrelated keys.

    A shared `.env` file can hold variables for other tools. Only keys with the
    settings prefix (`NYT_COOKING_`) reach `Settings`, so `extra="forbid"` still
    rejects unknown `NYT_COOKING_` keys without tripping on everything else.
    """

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        inner: PydanticBaseSettingsSource,
    ) -> None:
        """Wrap the default `.env` source.

        Args:
            settings_cls (type[BaseSettings]): The settings class being loaded.
            inner (PydanticBaseSettingsSource): The default `.env` source.
        """
        super().__init__(settings_cls)
        self._inner = inner

    def get_field_value(
        self,
        field: FieldInfo,
        field_name: str,
    ) -> tuple[Any, str, bool]:
        """Read a field's value from the wrapped `.env` source.

        Args:
            field (FieldInfo): The field's definition.
            field_name (str): The field name.

        Returns:
            tuple[Any, str, bool]: The value, its key, and whether it is complex.
        """
        return self._inner.get_field_value(field, field_name)

    def __call__(self) -> dict[str, Any]:
        """Load the `.env` values that belong to these settings.

        Returns:
            dict[str, Any]: Values for known fields or prefixed keys.
        """
        prefix = str(self.settings_cls.model_config.get("env_prefix", "")).lower()
        known = set(self.settings_cls.model_fields)
        return {
            key: value
            for key, value in self._inner().items()
            if key in known or key.lower().startswith(prefix)
        }


class RestSettings(BaseModel):
    """Configuration for NYT Cooking's REST API.

    Set through `NYT_COOKING_REST__*` variables, such as
    `NYT_COOKING_REST__BASE_URL`.
    """

    model_config = ConfigDict(extra="forbid")

    base_url: HttpUrl = Field(
        default=HttpUrl("https://cooking.nytimes.com"),
        description="The base URL for NYT Cooking.",
    )
    identity_url: HttpUrl = Field(
        default=HttpUrl("https://a.nytimes.com/svc/nyt/data-layer"),
        description="NYT endpoint that reports the signed-in user.",
    )

    @property
    def headers(self) -> dict[str, str]:
        """Headers sent with every REST request, mimicking the NYT Cooking web app."""
        return {"Accept": "*/*", "x-cooking-api": "cooking-frontend"}


class GraphQLSettings(BaseModel):
    """Configuration for NYT's GraphQL API, which serves recipe comments.

    Set through `NYT_COOKING_GRAPHQL__*` variables, such as
    `NYT_COOKING_GRAPHQL__TOKEN`.
    """

    model_config = ConfigDict(extra="forbid")

    url: HttpUrl = Field(
        default=HttpUrl("https://samizdat-graphql.nytimes.com/graphql/v2"),
        description="NYT's GraphQL endpoint.",
    )
    app_type: str = Field(
        default="cooking-frontend-client",
        description="The `nyt-app-type` header, naming the NYT Cooking web app.",
    )
    app_version: str = Field(
        default="1.0.0",
        description="The `nyt-app-version` header.",
    )
    token: str = Field(
        default=(
            "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzdp4mthaMhVrik7XIIjd/xmmzMsg"
            "KMzOJTt+0QlsU4bDpOY4Tc0Sc77GG+LjjzZG0wmozy6nqBgG0aKonVDbMfTd8PE3JEs48WC9"
            "J8cL5cuLdrcU2RUJs8tbpr/T6bxWXpe9gK1HkQwcU+RFTtHFUOw7GIDzTM0aNvlhev8Lp8RH"
            "CQMOSVxZ1JB/n//qTV0zbiB01eSMEPs99qnh7KMsIkAwU42nsh3kKYmK5p+91Ng7fXLqMWfS"
            "2fL6b5HE/fPPB0oClHgRqXAV87gcIbBAAvplWH6Ge7aqUCQBZhUE4rpMgEP//u7A/yYTs8kN"
            "XLXJmk1WNiebue8iLRRiR8vnjwIDAQAB"
        ),
        description=(
            "The `nyt-token` header: the public key the NYT Cooking web app sends to "
            "every visitor. It is not a secret and not tied to an account."
        ),
    )

    @property
    def headers(self) -> dict[str, str]:
        """Headers sent with every GraphQL request, as the NYT Cooking web app does."""
        return {
            "nyt-app-type": self.app_type,
            "nyt-app-version": self.app_version,
            "nyt-token": self.token,
        }


class Settings(BaseSettings):
    """Configuration for the NYT Cooking client.

    The session's cookie and User-Agent are shared by both APIs; `rest` and
    `graphql` hold what is specific to each.

    Each field is resolved from the first source that sets it:

    1. Arguments passed to `Settings`.
    2. `NYT_COOKING_*` environment variables, such as `NYT_COOKING_COOKIE`, with
        `__` reaching into `rest` and `graphql`, as in `NYT_COOKING_REST__BASE_URL`.
    3. `.env` files: the app config directory's `.env`, then `./.env`.
    4. The cookie saved by `save_credentials`.

    The cookie is required, so loading settings fails with a `ValidationError` when
    no source sets it. Reading settings never saves anything.

    ??? example "Example"
        ```python
        from nyt_cooking.client import Settings

        settings = Settings(cookie="0^CB...")
        print(settings.cookie, settings.rest.base_url)
        ```

        will output:
        ```text
        ********** https://cooking.nytimes.com/
        ```
    """

    model_config = SettingsConfigDict(
        env_prefix="NYT_COOKING_",
        env_nested_delimiter="__",
        env_file=(APP_DIR / ".env", ".env"),
        env_ignore_empty=True,
        extra="forbid",
    )

    cookie: SecretStr = Field(
        default=...,
        description="Value of the `NYT-S` session cookie from cooking.nytimes.com",
    )
    rest: RestSettings = Field(
        default_factory=RestSettings,
        description="NYT Cooking's REST API.",
    )
    graphql: GraphQLSettings = Field(
        default_factory=GraphQLSettings,
        description="NYT's GraphQL API.",
    )
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:156.0) "
            "Gecko/20100101 Firefox/156.0"
        ),
        description="The User-Agent header, used to mimic a web browser request.",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Order the sources: arguments, environment, `.env` files, saved cookie.

        Args:
            settings_cls (type[BaseSettings]): The settings class being loaded.
            init_settings (PydanticBaseSettingsSource): Arguments to `Settings`.
            env_settings (PydanticBaseSettingsSource): Environment variables.
            dotenv_settings (PydanticBaseSettingsSource): `.env` files.
            file_secret_settings (PydanticBaseSettingsSource): Secret files, unused.

        Returns:
            tuple[PydanticBaseSettingsSource, ...]: Sources, highest priority first.
        """
        return (
            init_settings,
            env_settings,
            PrefixedDotEnvSource(settings_cls, dotenv_settings),
            StoredCredentialsSource(settings_cls),
        )

    @classmethod
    def save_credentials(cls, cookie: str) -> None:
        """Save a cookie for later runs, without checking it with NYT.

        Create a `Client` with the cookie first to check that it belongs to an NYT
        Cooking subscriber.

        Args:
            cookie (str): Value of the `NYT-S` cookie.
        """
        CredentialStore.save(cookie)

    @classmethod
    def clear_credentials(cls) -> bool:
        """Remove the saved cookie.

        Cookies set through arguments, the environment or `.env` files are
        unaffected.

        Returns:
            bool: Whether anything was removed.
        """
        return CredentialStore.clear()
