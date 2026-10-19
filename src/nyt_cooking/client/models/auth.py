from __future__ import annotations

from pydantic import AliasPath, ConfigDict, Field

from nyt_cooking.client.models.base import CookingModel


class IsAuthenticated(CookingModel):
    """Whether NYT recognises the current login as an NYT Cooking subscriber."""

    authenticated: bool = Field(
        description=(
            "True when NYT recognises the cookie as an account with an active NYT "
            "Cooking subscription"
        ),
    )


class Subscription(CookingModel):
    """One of an NYT account's subscriptions, as NYT's identity endpoint reports it."""

    active: bool = Field(
        default=False,
        validation_alias="hasActiveEntitlements",
        description="Whether the subscription currently grants its entitlements",
    )
    entitlements: list[str] = Field(
        default_factory=list,
        description="Codes of the products it grants, such as `CKG` for NYT Cooking",
    )


class Identity(CookingModel):
    """The user NYT's identity endpoint reports for a cookie."""

    model_config = ConfigDict(coerce_numbers_to_str=True)

    regi_id: str | None = Field(
        default=None,
        validation_alias=AliasPath("user", "regiId"),
        description="NYT account ID, or `None` when the cookie is not recognised",
    )
    subscriptions: list[Subscription] = Field(
        default_factory=list,
        validation_alias=AliasPath("user", "subInfo", "subscriptions"),
        description="The account's subscriptions",
    )

    @property
    def cooking_subscriber(self) -> bool:
        """Whether the account has an active subscription that includes NYT Cooking."""
        return self.regi_id is not None and any(
            subscription.active and "CKG" in subscription.entitlements
            for subscription in self.subscriptions
        )
