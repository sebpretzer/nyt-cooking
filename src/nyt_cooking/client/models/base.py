from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Annotated, Any

from pydantic import (
    AliasChoices,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
)

SITE_URL = "https://cooking.nytimes.com"


_BREAK_TAG = re.compile(r"</?(?:br|div|li|p)\b[^>]*>", re.IGNORECASE)


class _TextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self.chunks.append(data)


def _strip_html(value: str) -> str:
    collector = _TextCollector()
    collector.feed(_BREAK_TAG.sub(" ", value))
    collector.close()
    return " ".join("".join(collector.chunks).split())


def _plain_or_none(value: object) -> object:
    if isinstance(value, str):
        return _strip_html(value) or None
    return value


def _strip_html_keeping_lines(value: str) -> str:
    line_break_tag = re.compile(r"<br\s*/?>", re.IGNORECASE)
    lines = [
        _strip_html(line)
        for line in line_break_tag.sub("\n", value).replace("\r\n", "\n").split("\n")
    ]
    return "\n".join(lines).strip()


PlainText = Annotated[str, BeforeValidator(_strip_html)]
OptionalPlainText = Annotated[str | None, BeforeValidator(_plain_or_none)]
MultilineText = Annotated[str, BeforeValidator(_strip_html_keeping_lines)]


class CookingModel(BaseModel):
    """Base model for every NYT Cooking response model.

    NYT responses carry many fields these models do not use, so unknown fields are
    ignored rather than rejected. Fields validate by either their name or their NYT
    alias.
    """

    model_config = ConfigDict(
        extra="ignore",
        validate_by_name=True,
        validate_by_alias=True,
    )

    def to_json(self) -> dict[str, Any]:
        """Convert the model to JSON-ready data keyed by field name.

        ??? example "Example"
            ```python
            from nyt_cooking.client.models import Duration

            Duration(display="30 minutes", minutes=30).to_json()
            ```

            will output:
            ```python
            {"display": "30 minutes", "minutes": 30.0}
            ```

        Returns:
            dict[str, Any]: The model as a dictionary of JSON-compatible values.
        """
        return self.model_dump(mode="json")


class Duration(CookingModel):
    """A length of time, as NYT both displays and measures it."""

    display: str | None = Field(
        default=None,
        description="Human-readable time, such as `1 1/2 hours`",
    )
    minutes: float | None = Field(default=None, description="Time in minutes")

    @field_validator("display", mode="before")
    @classmethod
    def _blank_is_none(cls, value: object) -> object:
        return value or None

    def __str__(self) -> str:
        """Return the display text, or an empty string when there is none."""
        return self.display or ""


class ImageCrop(CookingModel):
    """One size of a recipe image."""

    name: str = Field(description="NYT's name for the crop, such as `superJumbo`")
    url: str = Field(description="URL of the image file")
    width: int = Field(description="Width in pixels")
    height: int = Field(description="Height in pixels")


class Image(CookingModel):
    """A recipe image, available in several crops."""

    caption: str | None = Field(default=None, description="Image caption")
    credit: str | None = Field(default=None, description="Photographer credit")
    crops: list[ImageCrop] = Field(
        default_factory=list,
        description="Available sizes of the image",
    )

    @property
    def url(self) -> str | None:
        """URL of the largest crop, or `None` when there are no crops."""
        if not self.crops:
            return None
        return max(self.crops, key=lambda crop: crop.width * crop.height).url


class Pagination(CookingModel):
    """Where a page of results sits within the full result set."""

    total: int = Field(
        validation_alias=AliasChoices("total", "total_count"),
        description="Total number of results across all pages",
    )
    page: int = Field(
        validation_alias=AliasChoices("page", "current_page"),
        description="This page's number, starting at 1",
    )
    max_page: int = Field(
        validation_alias=AliasChoices("max_page", "total_pages"),
        description="Number of the last page",
    )
