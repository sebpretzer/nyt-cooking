from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from nyt_cooking.client.models import Comments

ADA_HELPFUL_COUNT = 22


@pytest.fixture
def found(comments_payload: dict[str, Any]) -> dict[str, Any]:
    return comments_payload["data"]["communityComments"]


class TestComments:
    def test_unwraps_each_edge_into_a_comment(self, found: dict[str, Any]) -> None:
        comments = Comments.model_validate(found)
        assert [comment.id for comment in comments.comments] == ["101", "103"]
        assert (comments.total, comments.helpful_total) == (4, 1)

    def test_nests_replies_under_their_comment(self, found: dict[str, Any]) -> None:
        first, second = Comments.model_validate(found).comments
        (reply,) = first.replies
        assert reply.id == "102"
        assert reply.author.is_staff
        assert reply.author.title == "Staff Editor"
        assert second.replies == []

    def test_text_keeps_line_breaks_and_drops_other_html(
        self,
        found: dict[str, Any],
    ) -> None:
        first = Comments.model_validate(found).comments[0]
        assert first.text == "Less broth.\n\n1. More mint."

    def test_reads_the_author_date_and_helpful_count(
        self,
        found: dict[str, Any],
    ) -> None:
        first, second = Comments.model_validate(found).comments
        assert first.author.name == "Ada"
        assert first.author.location == "Chicago"
        assert first.author.title is None
        assert first.submitted_at == datetime(2026, 9, 22, 2, 4, 6, tzinfo=UTC)
        assert first.helpful_count == ADA_HELPFUL_COUNT
        assert second.author.location is None

    def test_next_cursor_is_the_end_cursor_while_more_pages_remain(
        self,
        found: dict[str, Any],
    ) -> None:
        assert Comments.model_validate(found).next_cursor == "cursor-1"

    def test_next_cursor_is_none_on_the_last_page(self, found: dict[str, Any]) -> None:
        found["pageInfo"]["hasNextPage"] = False
        assert Comments.model_validate(found).next_cursor is None

    def test_str_shows_the_author_helpful_count_and_text(
        self,
        found: dict[str, Any],
    ) -> None:
        first = Comments.model_validate(found).comments[0]
        assert str(first) == "Ada (22 helpful): Less broth.\n\n1. More mint."
        assert str(first.replies[0]) == (
            "Test Editor (staff, 3 helpful): It freezes beautifully."
        )

    def test_round_trips_through_its_own_json(self, found: dict[str, Any]) -> None:
        comments = Comments.model_validate(found)
        assert Comments.model_validate(comments.to_json()) == comments
