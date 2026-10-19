from __future__ import annotations

from typing import Any

from nyt_cooking.client.models import Folder, Folders, SavedRecipe


class TestFolders:
    def test_reads_the_collections(self, folders_payload: dict[str, Any]) -> None:
        folders = Folders.model_validate(folders_payload).folders
        assert [(folder.id, folder.recipe_count) for folder in folders] == [
            (7, 2),
            (8, 0),
        ]

    def test_description_is_plain_text_or_none(
        self,
        folders_payload: dict[str, Any],
    ) -> None:
        soups, stews = Folders.model_validate(folders_payload).folders
        assert soups.description is None
        assert stews.description == "Slow and low"

    def test_url_points_into_the_recipe_box(
        self,
        folders_payload: dict[str, Any],
    ) -> None:
        folder = Folder.model_validate(folders_payload["collections"][0])
        assert folder.url == "https://cooking.nytimes.com/recipe-box/7"
        assert folder.to_json()["url"] == folder.url

    def test_str_shows_the_name_count_and_id(
        self,
        folders_payload: dict[str, Any],
    ) -> None:
        soups, stews = Folders.model_validate(folders_payload).folders
        assert str(soups) == "Soups (2 recipes) [7]"
        assert str(stews) == "Stews (0 recipes) [8]"
        assert str(soups.model_copy(update={"recipe_count": 1})) == (
            "Soups (1 recipe) [7]"
        )


class TestSavedRecipe:
    def test_str_lists_the_folders(self, folders_payload: dict[str, Any]) -> None:
        soups, stews = Folders.model_validate(folders_payload).folders
        saved = SavedRecipe(id=42, name="Soup", saved=True, folders=[soups, stews])
        assert str(saved) == "Soup [42]: saved, in Soups, Stews"

    def test_str_without_folders(self) -> None:
        assert str(SavedRecipe(id=42, name="Soup", saved=True)) == "Soup [42]: saved"

    def test_str_when_not_saved(self) -> None:
        assert str(SavedRecipe(id=42, name="Soup", saved=False)) == (
            "Soup [42]: not saved"
        )

    def test_collection_ids_are_matched_against_the_folders_context(
        self,
        interactions_payload: dict[str, Any],
        folders_payload: dict[str, Any],
    ) -> None:
        folders = Folders.model_validate(folders_payload).folders
        saved = SavedRecipe.model_validate(
            interactions_payload,
            context={"folders": folders},
        )
        assert [folder.id for folder in saved.folders] == [7]

    def test_collection_ids_without_folders_context_are_dropped(
        self,
        interactions_payload: dict[str, Any],
    ) -> None:
        assert SavedRecipe.model_validate(interactions_payload).folders == []
