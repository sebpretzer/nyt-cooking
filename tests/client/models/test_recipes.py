from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from nyt_cooking.client.models import (
    Duration,
    Ingredients,
    Rating,
    Recipe,
    RecipeBox,
    Steps,
)


@pytest.fixture
def recipe(recipe_payload: dict[str, Any]) -> Recipe:
    return Recipe.model_validate(recipe_payload)


class TestRecipe:
    def test_maps_api_fields(self, recipe: Recipe) -> None:
        assert (recipe.id, recipe.name) == (42, "Weeknight Test Soup")
        assert recipe.servings == "4 servings"
        assert recipe.total_time == Duration(display="40 minutes", minutes=40)
        assert recipe.cook_time == Duration(display="30 minutes", minutes=30)
        assert recipe.rating == Rating(value=4.25, total=12)

    def test_prefers_the_card_byline_over_the_uppercase_one(
        self,
        recipe: Recipe,
    ) -> None:
        assert recipe.byline == "Ada Tester"

    def test_falls_back_to_the_plain_byline(
        self,
        recipe_payload: dict[str, Any],
    ) -> None:
        payload = {**recipe_payload, "content_attribution": {}}
        assert Recipe.model_validate(payload).byline == "ADA TESTER"

    def test_blank_display_time_is_none(self, recipe: Recipe) -> None:
        assert recipe.prep_time == Duration()
        assert str(recipe.prep_time) == ""

    def test_description_is_plain_text(self, recipe: Recipe) -> None:
        assert recipe.description == "A simple soup."

    def test_missing_topnote_leaves_no_description(
        self,
        recipe_payload: dict[str, Any],
    ) -> None:
        payload = {k: v for k, v in recipe_payload.items() if k != "topnote"}
        assert Recipe.model_validate(payload).description is None

    def test_image_url_is_the_largest_crop(self, recipe: Recipe) -> None:
        assert recipe.image is not None
        assert recipe.image.url == "https://img/l.jpg"

    def test_missing_parts_and_directions_are_empty(
        self,
        recipe_payload: dict[str, Any],
    ) -> None:
        payload = {
            k: v for k, v in recipe_payload.items() if k not in {"parts", "directions"}
        }
        parsed = Recipe.model_validate(payload)
        assert len(parsed.ingredients) == 0
        assert len(parsed.steps) == 0

    def test_unknown_fields_are_ignored(self, recipe_payload: dict[str, Any]) -> None:
        payload = {**recipe_payload, "brand_new_field": {"anything": 1}}
        assert Recipe.model_validate(payload).name == "Weeknight Test Soup"

    def test_missing_name_is_a_validation_error(
        self,
        recipe_payload: dict[str, Any],
    ) -> None:
        del recipe_payload["name"]
        with pytest.raises(ValidationError):
            Recipe.model_validate(recipe_payload)

    def test_to_json_uses_field_names_and_json_types(self, recipe: Recipe) -> None:
        data = recipe.to_json()
        assert data["servings"] == "4 servings"
        assert data["total_time"] == {"display": "40 minutes", "minutes": 40.0}
        assert data["ingredients"][1]["name"] == "For the topping"
        assert data["steps"][0]["steps"][1] == {
            "number": 2,
            "description": "Season to taste.",
        }
        assert "parts" not in data
        assert json.loads(json.dumps(data)) == data

    def test_to_string(self, recipe: Recipe) -> None:
        assert recipe.to_string() == (
            "Weeknight Test Soup\n\n"
            "By Ada Tester | 40 minutes | 4 servings | 4.2/5 (12 ratings)\n\n"
            "A simple soup.\n\n"
            "Ingredients\n"
            "- 2 cups stock\n"
            "- Salt\n"
            "For the topping:\n"
            "- 1 lemon (zested)\n\n"
            "Steps\n"
            "1. Warm the stock.\n"
            "2. Season to taste.\n\n"
            "https://cooking.nytimes.com/recipes/42-weeknight-test-soup"
        )
        assert str(recipe) == recipe.to_string()

    def test_to_markdown(self, recipe: Recipe) -> None:
        assert recipe.to_markdown() == (
            "# [Weeknight Test Soup]"
            "(https://cooking.nytimes.com/recipes/42-weeknight-test-soup)\n\n"
            "By Ada Tester · 40 minutes · 4 servings · 4.2/5 (12 ratings)\n\n"
            "A simple soup.\n\n"
            "## Ingredients\n\n"
            "- 2 cups stock\n"
            "- Salt\n\n"
            "### For the topping\n\n"
            "- 1 lemon (zested)\n\n"
            "## Steps\n\n"
            "1. Warm the stock.\n"
            "2. Season to taste."
        )


class TestIngredients:
    def test_items_flattens_every_group(self, recipe: Recipe) -> None:
        assert [str(item) for item in recipe.ingredients.items] == [
            "2 cups stock",
            "Salt",
            "1 lemon (zested)",
        ]
        assert len(recipe.ingredients) == len(recipe.ingredients.items)

    def test_to_json_keeps_the_groups(self, recipe: Recipe) -> None:
        assert recipe.ingredients.to_json()[1] == {
            "name": "For the topping",
            "ingredients": [{"quantity": "1", "text": "lemon (zested)"}],
        }

    def test_quantity_defaults_to_blank(self) -> None:
        parsed = Ingredients.model_validate(
            [{"ingredients": [{"display_text": "Oil"}]}],
        )
        assert parsed.items[0].quantity == ""
        assert parsed.to_markdown() == "- Oil"


class TestSteps:
    def test_items_flattens_every_group(self, recipe: Recipe) -> None:
        assert [step.number for step in recipe.steps.items] == [1, 2]
        assert len(recipe.steps) == len(recipe.steps.items)

    def test_named_groups_become_subheadings(self) -> None:
        parsed = Steps.model_validate(
            [
                {"name": "Dough", "steps": [{"number": 1, "description": "Mix."}]},
                {"name": "Bake", "steps": [{"number": 2, "description": "Bake."}]},
            ],
        )
        assert parsed.to_markdown() == "### Dough\n\n1. Mix.\n\n### Bake\n\n2. Bake."
        assert parsed.to_string() == "Dough:\n1. Mix.\nBake:\n2. Bake."


class TestRecipeBox:
    def test_keeps_only_recipes(self, recipe_box_payload: dict[str, Any]) -> None:
        box = RecipeBox.model_validate(recipe_box_payload)
        assert [recipe.id for recipe in box.recipes] == [42, 43]

    def test_summaries_share_the_recipe_field_mapping(
        self,
        recipe_box_payload: dict[str, Any],
    ) -> None:
        first, second = RecipeBox.model_validate(recipe_box_payload).recipes
        assert first.byline == "Ada Tester"
        assert first.servings == "4 servings"
        assert first.total_time == Duration(display="40 minutes", minutes=40)
        assert str(first) == "Weeknight Test Soup (Ada Tester, 40 minutes) [42]"
        assert str(second) == "Plain Broth [43]"

    def test_pagination_reads_the_meta_block(
        self,
        recipe_box_payload: dict[str, Any],
    ) -> None:
        pagination = RecipeBox.model_validate(recipe_box_payload).pagination
        assert (pagination.page, pagination.max_page, pagination.total) == (1, 2, 3)
