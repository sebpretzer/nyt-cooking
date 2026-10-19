from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from nyt_cooking.client.models import (
    SearchCriteria,
    SearchFilters,
    SearchResults,
    SearchSort,
)

EXPECTED_TOTAL = 30
EXPECTED_TOP_RATED = 12


class TestSearchResults:
    def test_unwraps_recipes_and_skips_other_entries(
        self,
        search_payload: dict[str, Any],
    ) -> None:
        results = SearchResults.model_validate(search_payload)
        assert [result.id for result in results.results] == [42, 43]

    def test_names_are_trimmed(self, search_payload: dict[str, Any]) -> None:
        search_payload["results"][0]["recipe"]["name"] = "Lemon Pasta\xa0"
        first = SearchResults.model_validate(search_payload).results[0]
        assert first.name == "Lemon Pasta"

    def test_maps_result_fields(self, search_payload: dict[str, Any]) -> None:
        first, second = SearchResults.model_validate(search_payload).results
        assert first.total_time == "40 minutes"
        assert first.url == "https://cooking.nytimes.com/recipes/42"
        assert second.byline is None
        assert second.total_time is None

    def test_str_lists_the_details(self, search_payload: dict[str, Any]) -> None:
        first, second = SearchResults.model_validate(search_payload).results
        assert str(first) == "Weeknight Test Soup (Ada Tester, 40 minutes) [42]"
        assert str(second) == "Plain Broth [43]"

    def test_pagination(self, search_payload: dict[str, Any]) -> None:
        pagination = SearchResults.model_validate(search_payload).pagination
        assert (pagination.page, pagination.max_page, pagination.total) == (1, 1, 2)

    def test_to_json_includes_the_url(self, search_payload: dict[str, Any]) -> None:
        dumped = SearchResults.model_validate(search_payload).to_json()
        assert dumped["results"][0]["url"] == "https://cooking.nytimes.com/recipes/42"

    def test_to_json_round_trips(self, search_payload: dict[str, Any]) -> None:
        results = SearchResults.model_validate(search_payload)
        assert SearchResults.model_validate(results.to_json()) == results

    def test_accepts_search_result_instances(
        self,
        search_payload: dict[str, Any],
    ) -> None:
        results = SearchResults.model_validate(search_payload)
        rebuilt = SearchResults(
            query=results.query,
            results=results.results,
            pagination=results.pagination,
        )
        assert rebuilt.results == results.results


class TestSearchEnums:
    def test_sort_values_are_the_ones_nyt_accepts(self) -> None:
        assert {sort.name: sort.value for sort in SearchSort} == {
            "RATING": "rating",
            "MOST_RECENT": "firstPublished",
        }


class TestSearchCriteria:
    def test_unset_criteria_add_no_parameters(self) -> None:
        assert SearchCriteria().to_params() == {}

    def test_maps_every_field_to_its_parameter(self) -> None:
        criteria = SearchCriteria(
            tags=["healthy", "one pot"],
            max_minutes=30,
            top_rated=True,
            sort=SearchSort.RATING,
        )
        assert criteria.to_params() == {
            "tags": "healthy,one pot",
            "time_lte": 30,
            "ratings": "topRated",
            "sort": "rating",
        }

    def test_keeps_a_zero_minute_limit(self) -> None:
        assert SearchCriteria(max_minutes=0).to_params() == {"time_lte": 0}

    def test_accepts_the_values_the_tool_receives(self) -> None:
        criteria = SearchCriteria.model_validate(
            {"tags": ["vegan"], "sort": "firstPublished"},
        )
        assert criteria.sort is SearchSort.MOST_RECENT

    @pytest.mark.parametrize(
        "invalid",
        [
            {"tag": ["vegan"]},
            {"sort": "newest"},
            {"result_type": "recipe"},
            {"max_minutes": -1},
        ],
        ids=["unknown-field", "unknown-sort", "result-type", "negative-minutes"],
    )
    def test_rejects_invalid_criteria(self, invalid: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            SearchCriteria.model_validate(invalid)


class TestSearchFilters:
    def test_reads_the_embedded_search_data(self, search_page_html: str) -> None:
        filters = SearchFilters.from_search_page(search_page_html)
        assert filters.query == "soup"
        assert filters.total == EXPECTED_TOTAL
        assert filters.tags == {"dinner": 30, "five ingredient": 2, "sheet-pan": 5}
        assert filters.cook_times == {20: 6, 30: 11, 45: 20, 60: 28}
        assert filters.top_rated == EXPECTED_TOP_RATED

    def test_leaves_out_drinks_which_cannot_be_filtered_by_tag(
        self,
        search_page_html: str,
    ) -> None:
        assert "drinks" not in SearchFilters.from_search_page(search_page_html).tags

    def test_optional_counts_default_to_empty(
        self,
        search_page_props: dict[str, Any],
    ) -> None:
        for key in ("cookTimeCounts", "topRatedCount"):
            del search_page_props[key]
        filters = SearchFilters.model_validate(search_page_props)
        assert (filters.cook_times, filters.top_rated) == ({}, 0)

    def test_to_json_round_trips(self, search_page_html: str) -> None:
        filters = SearchFilters.from_search_page(search_page_html)
        assert SearchFilters.model_validate(filters.to_json()) == filters

    @pytest.mark.parametrize(
        ("html", "message"),
        [
            ("<html></html>", "no embedded"),
            ('<script id="__NEXT_DATA__">not json</script>', "expected shape"),
            ('<script id="__NEXT_DATA__">{"props": {}}</script>', "expected shape"),
            ('<script id="__NEXT_DATA__">[]</script>', "expected shape"),
        ],
        ids=["missing", "invalid-json", "missing-keys", "wrong-type"],
    )
    def test_rejects_a_page_without_usable_data(
        self,
        html: str,
        message: str,
    ) -> None:
        with pytest.raises(ValueError, match=message):
            SearchFilters.from_search_page(html)

    def test_rejects_a_page_without_tag_counts(
        self,
        search_page_props: dict[str, Any],
    ) -> None:
        del search_page_props["filterCounts"]
        with pytest.raises(ValidationError):
            SearchFilters.model_validate(search_page_props)
