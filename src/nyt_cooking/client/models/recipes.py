from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, AliasPath, Field, RootModel, model_validator

from nyt_cooking.client.models.base import (
    CookingModel,
    Duration,
    Image,
    OptionalPlainText,
    Pagination,
    PlainText,
)


class Rating(CookingModel):
    """Average reader rating of a recipe."""

    value: float = Field(description="Average rating out of 5")
    total: int = Field(description="Number of ratings")

    def __str__(self) -> str:
        """Return the rating as `3.8/5 (367 ratings)`."""
        return f"{self.value:.1f}/5 ({self.total} ratings)"


class Ingredient(CookingModel):
    """A single ingredient line."""

    quantity: str = Field(
        default="",
        validation_alias="display_quantity",
        description="Amount, such as `4`; empty when part of the text",
    )
    text: PlainText = Field(
        validation_alias="display_text",
        description="The rest of the line, such as `ounces thick-cut bacon`",
    )

    def __str__(self) -> str:
        """Return the full line, such as `4 ounces thick-cut bacon`."""
        return f"{self.quantity} {self.text}".strip()


class IngredientGroup(CookingModel):
    """Ingredients under one heading of a recipe."""

    name: str = Field(
        default="",
        description="Heading, such as `For the topping`; empty for the main list",
    )
    ingredients: list[Ingredient] = Field(
        default_factory=list,
        description="Ingredients under this heading",
    )


class Ingredients(RootModel[list[IngredientGroup]]):
    """A recipe's ingredients, kept in NYT's groups."""

    root: list[IngredientGroup] = Field(default_factory=list)

    @property
    def items(self) -> list[Ingredient]:
        """Every ingredient across all groups, in order."""
        return [item for group in self.root for item in group.ingredients]

    def __len__(self) -> int:
        """Return the number of ingredients across all groups."""
        return len(self.items)

    def to_json(self) -> list[dict[str, Any]]:
        """Convert the groups to JSON-ready data.

        Returns:
            list[dict[str, Any]]: One dictionary per group.
        """
        return self.model_dump(mode="json")

    def to_string(self) -> str:
        """Render the ingredients as a plain-text list.

        Named groups are introduced by their name and a colon.

        Returns:
            str: One `- ` prefixed line per ingredient.
        """
        lines: list[str] = []
        for group in self.root:
            if group.name:
                lines.append(f"{group.name}:")
            lines.extend(f"- {ingredient}" for ingredient in group.ingredients)
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Render the ingredients as a markdown list.

        Named groups become `###` subheadings.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                ingredients = client.get_recipe(1019049).ingredients
            print(ingredients.to_markdown())
            ```

            will output:
            ```markdown
            - 4 ounces thick-cut bacon (4 to 6 slices)
            - ⅔ cup ricotta cheese
            ...
            ```

        Returns:
            str: The ingredients as markdown.
        """
        blocks: list[str] = []
        for group in self.root:
            items = "\n".join(f"- {ingredient}" for ingredient in group.ingredients)
            blocks.append(f"### {group.name}\n\n{items}" if group.name else items)
        return "\n\n".join(blocks)

    def __str__(self) -> str:
        """Return the same text as `to_string`."""
        return self.to_string()


class Step(CookingModel):
    """A single numbered step of a recipe."""

    number: int = Field(description="Step number")
    description: PlainText = Field(description="What to do in this step")

    def __str__(self) -> str:
        """Return the step as `1. Heat the oven to 450 degrees...`."""
        return f"{self.number}. {self.description}"


class StepGroup(CookingModel):
    """Steps under one heading of a recipe."""

    name: str = Field(
        default="",
        description="Heading, such as `For the dough`; empty for the main method",
    )
    steps: list[Step] = Field(
        default_factory=list,
        description="Steps under this heading",
    )


class Steps(RootModel[list[StepGroup]]):
    """A recipe's method, kept in NYT's groups."""

    root: list[StepGroup] = Field(default_factory=list)

    @property
    def items(self) -> list[Step]:
        """Every step across all groups, in order.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                steps = client.get_recipe(1019049).steps
            print(steps.items[0])
            ```

            will output:
            ```text
            1. Heat the oven to 450 degrees, and arrange racks in top and bottom...
            ```
        """
        return [item for group in self.root for item in group.steps]

    def __len__(self) -> int:
        """Return the number of steps across all groups."""
        return len(self.items)

    def to_json(self) -> list[dict[str, Any]]:
        """Convert the groups to JSON-ready data.

        Returns:
            list[dict[str, Any]]: One dictionary per group.
        """
        return self.model_dump(mode="json")

    def to_string(self) -> str:
        """Render the steps as plain text.

        Named groups are introduced by their name and a colon.

        Returns:
            str: One numbered line per step.
        """
        lines: list[str] = []
        for group in self.root:
            if group.name:
                lines.append(f"{group.name}:")
            lines.extend(str(step) for step in group.steps)
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Render the steps as a numbered markdown list.

        Named groups become `###` subheadings.

        Returns:
            str: The steps as markdown.
        """
        blocks: list[str] = []
        for group in self.root:
            items = "\n".join(str(step) for step in group.steps)
            blocks.append(f"### {group.name}\n\n{items}" if group.name else items)
        return "\n\n".join(blocks)

    def __str__(self) -> str:
        """Return the same text as `to_string`."""
        return self.to_string()


class RecipeSummary(CookingModel):
    """The headline details of a recipe, as listed in a recipe box."""

    id: int = Field(description="NYT Cooking recipe ID, such as `1019049`")
    name: PlainText = Field(description="Recipe title")
    byline: OptionalPlainText = Field(
        default=None,
        validation_alias=AliasChoices(
            AliasPath("content_attribution", "card_byline"),
            "byline",
        ),
        description="Recipe author(s)",
    )
    url: str = Field(description="Recipe page on cooking.nytimes.com")
    servings: OptionalPlainText = Field(
        default=None,
        validation_alias="yield",
        description="Yield, such as `2 to 4 servings`",
    )
    total_time: Duration | None = Field(
        default=None,
        validation_alias="cooking_time",
        description="Total time to make the recipe",
    )
    image: Image | None = Field(default=None, description="Recipe photo")
    has_video: bool = Field(default=False, description="Whether a video exists")

    def __str__(self) -> str:
        """Return the name, byline, total time and ID on one line."""
        details = [
            detail
            for detail in (
                self.byline,
                self.total_time.display if self.total_time else None,
            )
            if detail
        ]
        suffix = f" ({', '.join(details)})" if details else ""
        return f"{self.name}{suffix} [{self.id}]"


class Recipe(RecipeSummary):
    """A full recipe, including its ingredients and steps."""

    prep_time: Duration | None = Field(default=None, description="Preparation time")
    cook_time: Duration | None = Field(default=None, description="Cooking time")
    rating: Rating | None = Field(default=None, description="Average reader rating")
    description: OptionalPlainText = Field(
        default=None,
        validation_alias=AliasPath("topnote", "content"),
        description="The recipe's introduction",
    )
    ingredients: Ingredients = Field(
        default_factory=Ingredients,
        validation_alias="parts",
        description="Ingredients, grouped by heading",
    )
    steps: Steps = Field(
        default_factory=Steps,
        validation_alias="directions",
        description="Method, grouped by heading",
    )

    def _details(self) -> list[str]:
        details = [
            f"By {self.byline}" if self.byline else None,
            self.total_time.display if self.total_time else None,
            self.servings,
            str(self.rating) if self.rating else None,
        ]
        return [detail for detail in details if detail]

    def to_string(self) -> str:
        """Render the whole recipe as plain text.

        Returns:
            str: The title, details, introduction, ingredients, steps and URL,
                separated by blank lines.
        """
        sections = [self.name, " | ".join(self._details())]
        if self.description:
            sections.append(self.description)
        sections.append(f"Ingredients\n{self.ingredients.to_string()}")
        sections.append(f"Steps\n{self.steps.to_string()}")
        sections.append(self.url)
        return "\n\n".join(section for section in sections if section)

    def to_markdown(self) -> str:
        """Render the whole recipe as markdown.

        The title links to the recipe page, and ingredients and steps get `##`
        headings.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                recipe = client.get_recipe(1019049)
            print(recipe.to_markdown())
            ```

            will output:
            ```markdown
            # [Bacon and Egg Pizza](https://cooking.nytimes.com/recipes/1019049-...)

            By Melissa Clark · 30 minutes · 2 to 4 servings · 3.8/5 (367 ratings)

            If you've ever had a hankering for pizza for breakfast, this recipe...

            ## Ingredients

            - 4 ounces thick-cut bacon (4 to 6 slices)
            ...

            ## Steps

            1. Heat the oven to 450 degrees, and arrange racks in top and bottom...
            ...
            ```

        Returns:
            str: The recipe as markdown.
        """
        sections = [f"# [{self.name}]({self.url})"]
        if details := self._details():
            sections.append(" · ".join(details))
        if self.description:
            sections.append(self.description)
        sections.append(f"## Ingredients\n\n{self.ingredients.to_markdown()}")
        sections.append(f"## Steps\n\n{self.steps.to_markdown()}")
        return "\n\n".join(sections)

    def __str__(self) -> str:
        """Return the same text as `to_string`."""
        return self.to_string()


class RecipeBox(CookingModel):
    """Recipes saved to a user's recipe box."""

    recipes: list[RecipeSummary] = Field(
        default_factory=list,
        validation_alias="collectables",
        description="Saved recipes",
    )
    pagination: Pagination = Field(
        validation_alias="meta",
        description="Position within the recipe box, or the folder searched",
    )

    @model_validator(mode="before")
    @classmethod
    def _only_recipes(cls, data: object) -> object:
        if isinstance(data, dict) and isinstance(data.get("collectables"), list):
            data = {
                **data,
                "collectables": [
                    entry
                    for entry in data["collectables"]
                    if isinstance(entry, dict)
                    and entry.get("type", "recipe") == "recipe"
                ],
            }
        return data


class RecentlyViewed(CookingModel):
    """Recipes a user has recently opened, most recent first."""

    recipes: list[RecipeSummary] = Field(
        default_factory=list,
        description="Recently viewed recipes",
    )

    @model_validator(mode="before")
    @classmethod
    def _wrap_recipes(cls, data: object) -> object:
        if isinstance(data, list):
            return {
                "recipes": [
                    entry
                    for entry in data
                    if isinstance(entry, dict)
                    and entry.get("type", "recipe") == "recipe"
                ],
            }
        return data
