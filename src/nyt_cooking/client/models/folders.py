from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, computed_field, field_validator

from nyt_cooking.client.models.base import (
    SITE_URL,
    CookingModel,
    OptionalPlainText,
    PlainText,
)

if TYPE_CHECKING:
    from pydantic import ValidationInfo


class Folder(CookingModel):
    """A folder in a user's recipe box."""

    id: int = Field(description="NYT Cooking folder ID, such as `14142135`")
    name: PlainText = Field(description="Folder name")
    description: OptionalPlainText = Field(
        default=None,
        description="Folder description",
    )
    recipe_count: int = Field(
        default=0,
        validation_alias="collectables_count",
        description="Number of recipes in the folder",
    )

    @computed_field
    @property
    def url(self) -> str:
        """Folder page in the recipe box on cooking.nytimes.com."""
        return f"{SITE_URL}/recipe-box/{self.id}"

    def __str__(self) -> str:
        """Return the name, recipe count and ID on one line."""
        noun = "recipe" if self.recipe_count == 1 else "recipes"
        return f"{self.name} ({self.recipe_count} {noun}) [{self.id}]"


class Folders(CookingModel):
    """The folders in a user's recipe box, in alphabetical order."""

    folders: list[Folder] = Field(
        default_factory=list,
        validation_alias="collections",
        description="Recipe box folders",
    )


class SavedRecipe(CookingModel):
    """Whether a recipe is saved to the user's recipe box, and in which folders.

    Validates NYT's recipe interactions response, whose `collection_ids` are
    matched against the user's folders, passed as the `folders` validation
    context. IDs that are not among them, such as the hidden collection behind
    the whole recipe box, are dropped.

    ??? example "Example"
        ```python
        from nyt_cooking.client.models import Folder, SavedRecipe

        stew = Folder(id=61803398, name="Stew")
        saved = SavedRecipe.model_validate(
            {
                "id": 4735,
                "name": "Beef Stew",
                "saved": True,
                "collection_ids": [1, 61803398],
            },
            context={"folders": [stew]},
        )
        print(saved)
        ```

        will output:
        ```text
        Beef Stew [4735]: saved, in Stew
        ```
    """

    id: int = Field(description="NYT Cooking recipe ID, such as `1019049`")
    name: PlainText = Field(description="Recipe title")
    saved: bool = Field(description="Whether the recipe is saved to the recipe box")
    folders: list[Folder] = Field(
        default_factory=list,
        validation_alias="collection_ids",
        description="Recipe box folders the recipe is in",
    )

    @field_validator("folders", mode="before")
    @classmethod
    def _match_collection_ids(cls, value: object, info: ValidationInfo) -> object:
        if not isinstance(value, list) or not all(isinstance(i, int) for i in value):
            return value
        known: list[Folder] = (info.context or {}).get("folders", [])
        return [folder for folder in known if folder.id in value]

    def __str__(self) -> str:
        """Return the name, ID, and whether and where the recipe is saved."""
        if not self.saved:
            return f"{self.name} [{self.id}]: not saved"
        names = ", ".join(folder.name for folder in self.folders)
        return f"{self.name} [{self.id}]: saved" + (f", in {names}" if names else "")
