from datetime import datetime

from pydantic import Field, model_validator

from nyt_cooking.client.models.base import (
    CookingModel,
    MultilineText,
    OptionalPlainText,
    PlainText,
)


class CommentAuthor(CookingModel):
    """Who wrote a recipe comment, as they chose to sign it."""

    name: PlainText = Field(description="Display name")
    location: OptionalPlainText = Field(default=None, description="Stated location")
    title: OptionalPlainText = Field(
        default=None,
        description="Job title, given for NYT staff",
    )
    is_staff: bool = Field(
        default=False,
        validation_alias="isReporter",
        description="Whether the author is NYT Cooking staff",
    )


class Comment(CookingModel):
    """A public comment on a recipe, with any replies to it."""

    id: str = Field(description="NYT comment ID, such as `150214450`")
    text: MultilineText = Field(description="The comment, with its line breaks")
    author: CommentAuthor = Field(description="Who wrote the comment")
    submitted_at: datetime = Field(
        validation_alias="submittedAt",
        description="When the comment was posted",
    )
    helpful_count: int = Field(
        default=0,
        validation_alias="recommendedCount",
        description="How many readers marked the comment helpful",
    )
    replies: list["Comment"] = Field(
        default_factory=list,
        description="Replies to the comment, oldest first",
    )

    def __str__(self) -> str:
        """Return the author, whether they are staff, the helpful count and text."""
        staff = "staff, " if self.author.is_staff else ""
        return f"{self.author.name} ({staff}{self.helpful_count} helpful): {self.text}"


class Comments(CookingModel):
    """A page of a recipe's public comments.

    Validates the `communityComments` field of NYT's GraphQL response, where each
    comment arrives as an edge holding the comment and its replies.

    ??? example "Example"
        ```python
        from nyt_cooking.client.models import Comments

        comments = Comments.model_validate(
            {
                "summary": {"totalCount": 1, "totalReadersPicks": 0},
                "pageInfo": {"endCursor": "abc", "hasNextPage": False},
                "edges": [
                    {
                        "node": {
                            "comment": {
                                "id": "1",
                                "text": "Less broth.<br/>More mint.",
                                "submittedAt": "2026-04-07T20:21:13Z",
                                "recommendedCount": 3,
                                "author": {"name": "muriel"},
                            },
                            "replies": [],
                        },
                    },
                ],
            },
        )
        print(comments.comments[0], comments.next_cursor)
        ```

        will output:
        ```text
        muriel (3 helpful): Less broth.
        More mint. None
        ```
    """

    comments: list[Comment] = Field(
        default_factory=list,
        description="Top-level comments, each with its replies",
    )
    total: int = Field(
        default=0,
        description="Number of comments on the recipe, replies included",
    )
    helpful_total: int = Field(
        default=0,
        description="Number of comments readers picked as most helpful",
    )
    next_cursor: str | None = Field(
        default=None,
        description="Cursor for the next page, or `None` on the last page",
    )

    @model_validator(mode="before")
    @classmethod
    def _unwrap_edges(cls, data: object) -> object:
        if not isinstance(data, dict) or "edges" not in data:
            return data
        summary = data.get("summary") or {}
        page_info = data.get("pageInfo") or {}
        nodes = [edge["node"] for edge in data["edges"] if (edge or {}).get("node")]
        return {
            "comments": [
                {**node["comment"], "replies": node.get("replies") or []}
                for node in nodes
            ],
            "total": summary.get("totalCount") or 0,
            "helpful_total": summary.get("totalReadersPicks") or 0,
            "next_cursor": (
                page_info.get("endCursor") if page_info.get("hasNextPage") else None
            ),
        }
