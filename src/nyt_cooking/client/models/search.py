from __future__ import annotations

import json
import re
from enum import StrEnum

from pydantic import ConfigDict, Field, computed_field, field_validator, model_validator

from nyt_cooking.client.models.base import (
    SITE_URL,
    CookingModel,
    Image,
    OptionalPlainText,
    Pagination,
    PlainText,
)


class SearchResult(CookingModel):
    """A recipe returned by a search."""

    id: int = Field(description="NYT Cooking recipe ID, such as `1023921`")
    name: PlainText = Field(description="Recipe title")
    byline: OptionalPlainText = Field(default=None, description="Recipe author(s)")
    total_time: OptionalPlainText = Field(
        default=None,
        validation_alias="cooking_time",
        description="Total time, such as `1 1/2 hours`",
    )
    image: Image | None = Field(default=None, description="Recipe photo")
    has_video: bool = Field(default=False, description="Whether a video exists")

    @computed_field
    @property
    def url(self) -> str:
        """Recipe page on cooking.nytimes.com."""
        return f"{SITE_URL}/recipes/{self.id}"

    def __str__(self) -> str:
        """Return the name, byline, total time and ID on one line."""
        details = [detail for detail in (self.byline, self.total_time) if detail]
        suffix = f" ({', '.join(details)})" if details else ""
        return f"{self.name}{suffix} [{self.id}]"


class SearchResults(CookingModel):
    """Recipes matching a search query."""

    query: str = Field(description="The search query")
    results: list[SearchResult] = Field(
        default_factory=list,
        description="Matching recipes",
    )
    pagination: Pagination = Field(description="Position within all matches")

    @model_validator(mode="before")
    @classmethod
    def _unwrap_recipes(cls, data: object) -> object:
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            data = {
                **data,
                "results": [
                    entry["recipe"]
                    if isinstance(entry, dict) and "recipe" in entry
                    else entry
                    for entry in data["results"]
                    if not isinstance(entry, dict) or "recipe" in entry or "id" in entry
                ],
            }
        return data


class SearchSort(StrEnum):
    """How NYT Cooking orders search results.

    Leave the sort unset for best match, which is the default.
    """

    RATING = "rating"
    MOST_RECENT = "firstPublished"


class SearchCriteria(CookingModel):
    """Limits that narrow a recipe search.

    Leave a field unset to apply no limit of that kind. Unknown fields are
    rejected, so a misspelled limit is an error instead of being ignored.
    """

    model_config = ConfigDict(extra="forbid")

    tags: list[str] = Field(
        default_factory=list,
        description=(
            "Tags every result must have, such as `healthy`, `dinner` or `one pot`, "
            "from `get_search_filters`. Only those names match: a misspelled or "
            "invented tag matches nothing, with no error, so 0 results can mean a "
            "bad tag. Tags combine with AND, so each one narrows the results"
        ),
    )
    max_minutes: int | None = Field(
        default=None,
        ge=0,
        description="Longest total time in minutes, inclusive. There is no minimum",
    )
    top_rated: bool = Field(
        default=False,
        description="Whether to keep only top-rated recipes",
    )
    sort: SearchSort | None = Field(
        default=None,
        description=(
            "`rating` for highest rated or `firstPublished` for most recent. "
            "Leave unset for best match"
        ),
    )

    def to_params(self) -> dict[str, str | int]:
        """Return the query parameters NYT's search expects, leaving out unset ones.

        Returns:
            dict[str, str | int]: Parameters to add to the search query.
        """
        params: dict[str, str | int] = {}
        if self.tags:
            params["tags"] = ",".join(self.tags)
        if self.max_minutes is not None:
            params["time_lte"] = self.max_minutes
        if self.top_rated:
            params["ratings"] = "topRated"
        if self.sort is not None:
            params["sort"] = self.sort.value
        return params


_NEXT_DATA = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(?P<json>.*?)</script>',
    re.DOTALL,
)

_COUNTED_BUT_NOT_FILTERABLE_TAGS = frozenset({"drinks"})


class SearchFilters(CookingModel):
    """The filters available for a search, with how many results each leaves.

    The counts are for the query and filters that were searched, so they shrink
    as filters are added. Tags with no results are left out, as is `drinks`, which
    NYT counts but matches nothing when used as a tag.
    """

    query: str = Field(description="The search query")
    total: int = Field(
        validation_alias="size",
        description="Number of results for the query and filters searched",
    )
    tags: dict[str, int] = Field(
        validation_alias="filterCounts",
        description=(
            "Results left by each tag, keyed by the exact name to pass as a search "
            "tag, such as `one pot` or `sheet-pan`"
        ),
    )
    cook_times: dict[int, int] = Field(
        default_factory=dict,
        validation_alias="cookTimeCounts",
        description="Results left by each total-time limit, keyed by minutes",
    )
    top_rated: int = Field(
        default=0,
        validation_alias="topRatedCount",
        description="Results left by limiting the search to top-rated recipes",
    )

    @field_validator("tags")
    @classmethod
    def _drop_unfilterable_tags(cls, tags: dict[str, int]) -> dict[str, int]:
        return {
            tag: count
            for tag, count in tags.items()
            if tag not in _COUNTED_BUT_NOT_FILTERABLE_TAGS
        }

    @classmethod
    def from_search_page(cls, html: str) -> SearchFilters:
        """Read the filters from the HTML of a NYT Cooking search page.

        Args:
            html (str): Body of a `GET /search` response.

        Returns:
            SearchFilters: The filters the page was rendered with.

        Raises:
            ValueError: If the page does not carry its search data, such as after
                NYT changes the page.
        """
        match = _NEXT_DATA.search(html)
        if match is None:
            msg = "The NYT Cooking search page has no embedded search data."
            raise ValueError(msg)
        try:
            props = json.loads(match["json"])["props"]["pageProps"]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            msg = "The NYT Cooking search page data is not in the expected shape."
            raise ValueError(msg) from error
        return cls.model_validate(props)
