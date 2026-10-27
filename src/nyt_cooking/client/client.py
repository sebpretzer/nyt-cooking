from __future__ import annotations

import json
from functools import partial
from typing import TYPE_CHECKING, Any, Literal

import httpx
from pydantic import SecretStr

from nyt_cooking.client.models import (
    SITE_URL,
    Comments,
    Folder,
    Folders,
    Identity,
    Pagination,
    RecentlyViewed,
    Recipe,
    RecipeBox,
    SavedRecipe,
    SearchCriteria,
    SearchFilters,
    SearchResults,
)
from nyt_cooking.client.queries import RECIPE_COMMENTS
from nyt_cooking.client.settings import Settings

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Self

_MAX_COMMENTS_PER_REQUEST = 500


class Client:
    """Client for the NYT Cooking website's JSON API, for NYT Cooking subscribers.

    Every call needs the `NYT-S` session cookie of an NYT account with an active
    NYT Cooking subscription. The cookie comes from the `cookie` argument or from
    `Settings`, and creating the client checks it with NYT, so a client only
    exists for a subscriber.

    Use it as a context manager, or call `close`, to release its connections.

    ??? example "Example"
        ```python
        from nyt_cooking.client import Client

        with Client() as client:
            recipe = client.get_recipe(1019049)
        print(recipe.name)
        ```

        will output:
        ```text
        Bacon and Egg Pizza
        ```
    """

    def __init__(self, cookie: str | None = None, timeout: int = 30) -> None:
        """Create a client, loading the cookie from `Settings` if none is passed.

        Checks with NYT that the cookie belongs to an NYT Cooking subscriber. A
        passed-in cookie is used for this client only and is never saved; use
        `Settings.save_credentials` to save one.

        Args:
            cookie (str | None): Value of the `NYT-S` cookie.
            timeout (int): Seconds to wait on each request.

        Raises:
            pydantic.ValidationError: If no cookie is passed or configured.
            ValueError: If NYT does not recognise the cookie, or the account has
                no active NYT Cooking subscription.
            httpx.HTTPStatusError: If NYT responds with an error.
        """
        self.settings = (
            Settings() if cookie is None else Settings(cookie=SecretStr(cookie))
        )
        self._rest_client = self._init_rest_client(timeout)
        self._graphql_client = self._init_graphql_client(timeout)
        try:
            self.regi_id = self._subscriber_regi_id()
        except Exception:
            self.close()
            raise

    def _init_rest_client(self, timeout: int) -> httpx.Client:
        return httpx.Client(
            base_url=str(self.settings.rest.base_url),
            headers={
                "User-Agent": self.settings.user_agent,
                **self.settings.rest.headers,
            },
            cookies={"NYT-S": self.settings.cookie.get_secret_value()},
            timeout=timeout,
            follow_redirects=True,
        )

    def _init_graphql_client(self, timeout: int) -> httpx.Client:
        return httpx.Client(
            headers={
                "User-Agent": self.settings.user_agent,
                **self.settings.graphql.headers,
            },
            cookies={"NYT-S": self.settings.cookie.get_secret_value()},
            timeout=timeout,
            follow_redirects=True,
        )

    def __enter__(self) -> Self:
        """Return the client for use in a `with` block."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the client when the `with` block exits.

        Args:
            exc_type (type[BaseException] | None): The exception's type, if one was
                raised in the block.
            exc (BaseException | None): The exception, if one was raised.
            traceback (TracebackType | None): The exception's traceback, if any.
        """
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP connections."""
        self._rest_client.close()
        self._graphql_client.close()

    def _subscriber_regi_id(self) -> str:
        response = self._rest_client.get(str(self.settings.rest.identity_url))
        identity = Identity.model_validate(response.raise_for_status().json())
        if identity.regi_id is None:
            msg = (
                "NYT does not recognise the NYT-S cookie as a signed-in account; "
                "it may have expired."
            )
            raise ValueError(msg)
        if not identity.cooking_subscriber:
            msg = "The NYT account has no active NYT Cooking subscription."
            raise ValueError(msg)
        return identity.regi_id

    def _get(
        self,
        path: str,
        params: dict[str, str | int] | None = None,
    ) -> httpx.Response:
        return self._rest_client.get(path, params=params).raise_for_status()

    def _send(
        self,
        method: Literal["POST", "PUT", "DELETE"],
        path: str,
        body: dict[str, str | int] | None = None,
    ) -> httpx.Response:
        return self._rest_client.request(method, path, json=body).raise_for_status()

    def _query(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = self._graphql_client.post(
            str(self.settings.graphql.url),
            json={"query": query, "variables": variables},
        )
        try:
            payload = response.json()
        except json.JSONDecodeError:
            response.raise_for_status()
            raise
        if isinstance(payload, dict) and (errors := payload.get("errors")):
            messages = "; ".join(str(error.get("message", error)) for error in errors)
            msg = (
                f"NYT's GraphQL API rejected the query "
                f"(HTTP {response.status_code}): {messages}"
            )
            raise ValueError(msg)
        response.raise_for_status()
        return payload["data"]

    def get_recipe(self, recipe_id: int | str) -> Recipe:
        """Get a full recipe, including its ingredients and steps.

        Calls the `GET /api/v2/recipes/{recipe_id}` endpoint.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                recipe = client.get_recipe(1019049)
            print(recipe.byline, recipe.total_time, len(recipe.ingredients))
            ```

            will output:
            ```text
            Melissa Clark 30 minutes 12
            ```

        Args:
            recipe_id (int | str): NYT Cooking recipe ID, such as `1019049`.

        Returns:
            Recipe: The recipe.

        Raises:
            httpx.HTTPStatusError: If NYT responds with an error, such as a 404 for
                an unknown ID.
        """
        return Recipe.model_validate(self._get(f"/api/v2/recipes/{recipe_id}").json())

    def get_recipe_comments(
        self,
        recipe_id: int | str,
        after: str | None = None,
        per_page: int = 15,
        *,
        helpful_only: bool = False,
    ) -> Comments:
        """Get one page of a recipe's public comments, with all their replies.

        Runs the `communityComments` GraphQL query. Comments come newest first, or,
        with `helpful_only`, only those readers picked as most helpful, most helpful
        first: the "All Comments" and "Most Helpful" tabs on the recipe page.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                page = client.get_recipe_comments(775244489, helpful_only=True)
            print(page.total, page.helpful_total, page.comments[0].author.name)
            ```

            will output:
            ```text
            33 9 muriel
            ```

        Args:
            recipe_id (int | str): NYT Cooking recipe ID, such as `1019049`.
            after (str | None): `next_cursor` of the previous page, or `None` for
                the first page.
            per_page (int): Top-level comments per page, at most 500.
            helpful_only (bool): Whether to get only the most helpful comments.

        Returns:
            Comments: The page of comments.

        Raises:
            ValueError: If NYT has no comments for the recipe, which means the ID
                is unknown, or rejects the query.
            httpx.HTTPStatusError: If NYT responds with an error.
        """
        variables = {
            "uri": f"{SITE_URL}/recipes/{recipe_id}",
            "input": {
                "first": per_page,
                "after": after,
                "view": "READER_PICKS" if helpful_only else "ALL",
                "replies": _MAX_COMMENTS_PER_REQUEST,
                **({} if helpful_only else {"asc": False}),
            },
        }
        found = self._query(RECIPE_COMMENTS, variables)["communityComments"]
        if found["summary"]["totalCount"] is None:
            msg = f"NYT Cooking has no comments for recipe {recipe_id}; check the ID."
            raise ValueError(msg)
        return Comments.model_validate(found)

    def get_recipe_comments_paginated(
        self,
        recipe_id: int | str,
        max_results: int | None = None,
        *,
        helpful_only: bool = False,
    ) -> Comments:
        """Get a recipe's public comments across as many pages as needed.

        Calls `get_recipe_comments` with pages of up to 500 comments, the most NYT
        returns at once, until it has `max_results` comments or runs out.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                comments = client.get_recipe_comments_paginated(
                    1015819, max_results=600
                )
            print(len(comments.comments), comments.total)
            ```

            will output:
            ```text
            600 1712
            ```

        Args:
            recipe_id (int | str): NYT Cooking recipe ID, such as `1019049`.
            max_results (int | None): Most top-level comments to return, replies
                aside. `None` fetches every page.
            helpful_only (bool): Whether to get only the most helpful comments.

        Returns:
            Comments: The joined comments, with the cursor of the last page fetched,
                or `None` once every comment has been fetched.

        Raises:
            ValueError: If `max_results` is negative, NYT has no comments for the
                recipe, or NYT rejects the query.
        """
        self._check_max_results(max_results)

        def fetch(after: str | None, collected: int) -> Comments:
            remaining = _MAX_COMMENTS_PER_REQUEST
            if max_results is not None:
                remaining = min(remaining, max_results - collected)
            return self.get_recipe_comments(
                recipe_id,
                after,
                per_page=remaining,
                helpful_only=helpful_only,
            )

        last = fetch(None, 0)
        comments = list(last.comments)
        while last.next_cursor and (max_results is None or len(comments) < max_results):
            last = fetch(last.next_cursor, len(comments))
            comments.extend(last.comments)
        return last.model_copy(update={"comments": comments[:max_results]})

    def _search_params(
        self,
        query: str,
        criteria: SearchCriteria | None,
    ) -> dict[str, str | int]:
        return {"q": query, **(criteria or SearchCriteria()).to_params()}

    def search_filters(
        self,
        query: str = "",
        criteria: SearchCriteria | None = None,
    ) -> SearchFilters:
        """Get the filters a search offers, with how many results each leaves.

        Loads the `GET /search` page and reads the filters it embeds. NYT has no
        separate endpoint for them. The counts are for the query and criteria
        passed, so they shrink as tags are added, and tags with no results are
        left out. An empty query lists every tag.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client
            from nyt_cooking.client.models import SearchCriteria

            with Client() as client:
                filters = client.search_filters(
                    "chili",
                    SearchCriteria(tags=["healthy"]),
                )
            print(filters.total, filters.tags["dinner"], filters.cook_times[30])
            ```

            will output:
            ```text
            45 30 20
            ```

        Args:
            query (str): Search terms, such as `lemon pasta`. Empty for no terms.
            criteria (SearchCriteria | None): Limits already applied, using tags
                from an earlier call. `None` applies none.

        Returns:
            SearchFilters: The filters and their counts.

        Raises:
            ValueError: If the page does not carry its search data.
        """
        response = self._get("/search", params=self._search_params(query, criteria))
        return SearchFilters.from_search_page(response.text)

    def search_recipes(
        self,
        query: str,
        page: int = 1,
        criteria: SearchCriteria | None = None,
    ) -> SearchResults:
        """Get one page of recipes matching a search query.

        Calls the `GET /api/v3/search` endpoint, which returns up to 48 recipes per
        page. Use `search_recipes_paginated` to collect more than one page. Use
        `search_filters` to find the tags that match a query.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client
            from nyt_cooking.client.models import SearchCriteria

            with Client() as client:
                results = client.search_recipes(
                    "chili",
                    criteria=SearchCriteria(tags=["healthy", "dinner"], max_minutes=30),
                )
            print(results.pagination)
            ```

            will output:
            ```text
            total=11 page=1 max_page=1
            ```

        Args:
            query (str): Search terms, such as `lemon pasta`.
            page (int): Page number, starting at 1.
            criteria (SearchCriteria | None): Tags, time limit, rating and sort order
                to narrow by. NYT ignores the case of a tag but not
                its spelling, and a tag it does not know matches nothing rather
                than raising an error. `None` applies none.

        Returns:
            SearchResults: The matching recipes on that page.
        """
        params = {**self._search_params(query, criteria), "page": page}
        response = self._get("/api/v3/search", params=params)
        return SearchResults.model_validate(response.json())

    def search_recipes_paginated(
        self,
        query: str,
        max_results: int | None = None,
        criteria: SearchCriteria | None = None,
    ) -> SearchResults:
        """Get recipes matching a search query across as many pages as needed.

        Calls `search_recipes` page by page until it has `max_results` recipes or
        reaches the last page, then joins the results without repeats. NYT stops at
        960 results (20 pages of 48), however many match. When it caps a search, a
        few of those results only come back after the last page, so this keeps
        going until a page adds no new recipes.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                results = client.search_recipes_paginated("lemon pasta", max_results=60)
            print(len(results.results), results.pagination)
            ```

            will output:
            ```text
            60 total=311 page=2 max_page=7
            ```

        Args:
            query (str): Search terms, such as `lemon pasta`.
            max_results (int | None): Most recipes to return. `None` fetches every
                page.
            criteria (SearchCriteria | None): Limits to narrow by, as in
                `search_recipes`. `None` applies none.

        Returns:
            SearchResults: The joined results, with the pagination of the last page
                fetched.

        Raises:
            ValueError: If `max_results` is negative.
        """
        self._check_max_results(max_results)
        search = partial(self.search_recipes, query, criteria=criteria)
        last = search()
        results = {result.id: result for result in last.results}
        while self._should_fetch_next_page(
            collected=len(results),
            max_results=max_results,
            pagination=last.pagination,
        ):
            last = search(page=last.pagination.page + 1)
            results |= {r.id: r for r in last.results if r.id not in results}
        while len(results) < last.pagination.total and (
            max_results is None or len(results) < max_results
        ):
            last = search(page=last.pagination.page + 1)
            new = {r.id: r for r in last.results if r.id not in results}
            if not new:
                break
            results |= new
        return last.model_copy(update={"results": list(results.values())[:max_results]})

    def get_recipe_box(
        self,
        page: int = 1,
        per_page: int = 48,
        folder_id: int | str | None = None,
    ) -> RecipeBox:
        """Get one page of the recipes saved to the user's recipe box.

        Calls the `GET /api/v2/users/{regi_id}/search/recipe_box_search` endpoint. Use
        `get_recipe_box_paginated` to collect more than one page.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                box = client.get_recipe_box(per_page=3)
            print(box.pagination)
            ```

            will output:
            ```text
            total=218 page=1 max_page=73
            ```

        Args:
            page (int): Page number, starting at 1.
            per_page (int): Recipes per page.
            folder_id (int | str | None): NYT Cooking folder ID to limit the
                recipes to, from `get_folders`. `None` gets the whole recipe box.

        Returns:
            RecipeBox: The saved recipes on that page.
        """
        return self._recipe_box_page(self.regi_id, page, per_page, folder_id)

    def _recipe_box_page(
        self,
        regi_id: str,
        page: int,
        per_page: int,
        folder_id: int | str | None,
    ) -> RecipeBox:
        params: dict[str, str | int] = {"q": "", "page": page, "per_page": per_page}
        if folder_id is not None:
            params["collection_id"] = folder_id
        response = self._get(
            f"/api/v2/users/{regi_id}/search/recipe_box_search",
            params=params,
        )
        return RecipeBox.model_validate(response.json())

    def get_recipe_box_paginated(
        self,
        per_page: int = 48,
        max_results: int | None = None,
        folder_id: int | str | None = None,
    ) -> RecipeBox:
        """Get the recipes saved to the user's recipe box across many pages.

        Fetches pages until it has `max_results` recipes or reaches the last page, and
        joins the results.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                box = client.get_recipe_box_paginated(max_results=50)
            print(len(box.recipes), box.pagination)
            ```

            will output:
            ```text
            50 total=218 page=2 max_page=5
            ```

        Args:
            per_page (int): Recipes per page requested.
            max_results (int | None): Most recipes to return. `None` fetches the
                whole recipe box.
            folder_id (int | str | None): NYT Cooking folder ID to limit the
                recipes to, from `get_folders`. `None` gets the whole recipe box.

        Returns:
            RecipeBox: The joined recipes, with the pagination of the last page
                fetched.

        Raises:
            ValueError: If `max_results` is negative.
        """
        self._check_max_results(max_results)
        last = self._recipe_box_page(self.regi_id, 1, per_page, folder_id)
        recipes = list(last.recipes)
        while self._should_fetch_next_page(
            collected=len(recipes),
            max_results=max_results,
            pagination=last.pagination,
        ):
            last = self._recipe_box_page(
                self.regi_id,
                last.pagination.page + 1,
                per_page,
                folder_id,
            )
            recipes.extend(last.recipes)
        return last.model_copy(update={"recipes": recipes[:max_results]})

    def get_folder_recipes(self, folder_id: int | str) -> RecipeBox:
        """Get every recipe in a folder of the user's recipe box.

        Calls `get_recipe_box_paginated` for the folder, fetching every page.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                stew = client.get_folder_recipes(38433723)
            print([recipe.name for recipe in stew.recipes])
            ```

            will output:
            ```text
            ['Thai-Inspired Chicken Meatball Soup', 'Old-Fashioned Beef Stew', ...]
            ```

        Args:
            folder_id (int | str): NYT Cooking folder ID, such as `38433723`.

        Returns:
            RecipeBox: The folder's recipes.
        """
        return self.get_recipe_box_paginated(folder_id=folder_id)

    def get_folders(self) -> Folders:
        """Get the folders in the user's recipe box, in alphabetical order.

        Calls the `GET /api/v5/users/me/collections` endpoint.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                folders = client.get_folders()
            print(folders.folders[0])
            ```

            will output:
            ```text
            Chicken Dinners (28 recipes) [43932270]
            ```

        Returns:
            Folders: The recipe box folders.
        """
        return self._folders()

    def _folders(self) -> Folders:
        response = self._get(
            "/api/v5/users/me/collections",
            params={"sort": "alphanumeric", "per_page": 9999},
        )
        return Folders.model_validate(response.json())

    def create_folder(self, name: str) -> Folder:
        """Create an empty folder in the user's recipe box.

        Calls the `POST /api/v5/users/me/collections` endpoint.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                folder = client.create_folder("Weeknight Dinners")
            print(folder.url)
            ```

            will output:
            ```text
            https://cooking.nytimes.com/recipe-box/138753082
            ```

        Args:
            name (str): Name of the new folder.

        Returns:
            Folder: The new folder.
        """
        response = self._send("POST", "/api/v5/users/me/collections", {"name": name})
        return Folder.model_validate(response.json())

    def rename_folder(self, folder_id: int | str, name: str) -> Folder:
        """Rename a folder in the user's recipe box.

        Calls the `PUT /api/v2/users/{regi_id}/collections/{folder_id}` endpoint.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                folder = client.rename_folder(138753082, "Quick Dinners")
            print(folder)
            ```

            will output:
            ```text
            Quick Dinners (0 recipes) [138753082]
            ```

        Args:
            folder_id (int | str): NYT Cooking folder ID, such as `138753082`.
            name (str): New name for the folder.

        Returns:
            Folder: The renamed folder.
        """
        response = self._send(
            "PUT",
            f"/api/v2/users/{self.regi_id}/collections/{folder_id}",
            {"name": name},
        )
        return Folder.model_validate(response.json())

    def delete_folder(self, folder_id: int | str) -> Folders:
        """Delete a folder from the user's recipe box.

        Calls the `DELETE /api/v2/users/{regi_id}/collections/{folder_id}` endpoint,
        then lists the folders that are left. The folder's recipes stay saved to the
        recipe box.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                folders = client.delete_folder(138753082)
            print(len(folders.folders))
            ```

            will output:
            ```text
            7
            ```

        Args:
            folder_id (int | str): NYT Cooking folder ID, such as `138753082`.

        Returns:
            Folders: The folders left in the recipe box.
        """
        self._send("DELETE", f"/api/v2/users/{self.regi_id}/collections/{folder_id}")
        return self._folders()

    def get_saved_recipe(self, recipe_id: int | str) -> SavedRecipe:
        """Get whether a recipe is saved to the user's recipe box, and where.

        Calls the `GET /api/v5/users/me/recipes/{recipe_id}/interactions` endpoint and
        matches the recipe's collections against `get_folders`.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                print(client.get_saved_recipe(4735))
            ```

            will output:
            ```text
            Old-Fashioned Beef Stew [4735]: saved, in Stew
            ```

        Args:
            recipe_id (int | str): NYT Cooking recipe ID, such as `1019049`.

        Returns:
            SavedRecipe: Whether the recipe is saved, and its folders.
        """
        return self._saved_recipe(recipe_id)

    def _saved_recipe(self, recipe_id: int | str) -> SavedRecipe:
        response = self._get(f"/api/v5/users/me/recipes/{recipe_id}/interactions")
        return SavedRecipe.model_validate(
            response.json(),
            context={"folders": self._folders().folders},
        )

    def save_recipe(
        self,
        recipe_id: int | str,
        folder_id: int | str | None = None,
    ) -> SavedRecipe:
        """Save a recipe to the user's recipe box, optionally into a folder.

        Calls the `POST /api/v5/users/me/saved_recipes` endpoint. Adding a recipe to a
        folder also saves it to the recipe box. Saving a recipe that is already saved,
        or already in the folder, changes nothing.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                print(client.save_recipe(1019049, folder_id=38433723))
            ```

            will output:
            ```text
            Bacon and Egg Pizza [1019049]: saved, in Stew
            ```

        Args:
            recipe_id (int | str): NYT Cooking recipe ID, such as `1019049`.
            folder_id (int | str | None): NYT Cooking folder ID to add the recipe
                to, from `get_folders`. `None` saves it to the recipe box only.

        Returns:
            SavedRecipe: The recipe's saved state afterwards.
        """
        body: dict[str, str | int] = {"recipe_id": recipe_id}
        if folder_id is not None:
            body["collection_id"] = folder_id
        self._send("POST", "/api/v5/users/me/saved_recipes", body)
        return self._saved_recipe(recipe_id)

    def unsave_recipe(
        self,
        recipe_id: int | str,
        folder_id: int | str | None = None,
    ) -> SavedRecipe:
        """Remove a recipe from one folder, or from the user's whole recipe box.

        Calls the `DELETE /api/v5/users/me/saved_recipes/{recipe_id}` endpoint. Without
        a folder, the recipe is removed from the recipe box and every folder, and
        removing a recipe that is not saved changes nothing. With a folder, the recipe
        stays saved and in its other folders.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                print(client.unsave_recipe(1019049, folder_id=38433723))
            ```

            will output:
            ```text
            Bacon and Egg Pizza [1019049]: saved
            ```

        Args:
            recipe_id (int | str): NYT Cooking recipe ID, such as `1019049`.
            folder_id (int | str | None): NYT Cooking folder ID to remove the
                recipe from, from `get_folders`. `None` removes it from the whole
                recipe box.

        Returns:
            SavedRecipe: The recipe's saved state afterwards.

        Raises:
            httpx.HTTPStatusError: If NYT responds with an error, such as a 404
                when the recipe is not in the folder.
        """
        body: dict[str, str | int] | None = None
        if folder_id is not None:
            body = {"collection_id": folder_id, "recipe_id": recipe_id}
        self._send("DELETE", f"/api/v5/users/me/saved_recipes/{recipe_id}", body)
        return self._saved_recipe(recipe_id)

    def get_recently_viewed(self, max_results: int = 20) -> RecentlyViewed:
        """Get the recipes the user has recently viewed, most recent first.

        Calls the `GET /api/v5/users/me/recently_viewed` endpoint, which identifies
        the user from the cookie alone.

        ??? example "Example"
            ```python
            from nyt_cooking.client import Client

            with Client() as client:
                viewed = client.get_recently_viewed(max_results=3)
            print([recipe.name for recipe in viewed.recipes])
            ```

            will output:
            ```text
            ['Eggplant Lasagna', 'Bacon and Egg Pizza', 'Chili']
            ```

        Args:
            max_results (int): Most recipes to return. Sent to NYT as `per_page`,
                the only size control the endpoint has; it is not paginated.

        Returns:
            RecentlyViewed: The recently viewed recipes.

        Raises:
            ValueError: If `max_results` is negative.
            httpx.HTTPStatusError: If NYT responds with an error.
        """
        self._check_max_results(max_results)
        response = self._get(
            "/api/v5/users/me/recently_viewed",
            params={"per_page": max_results},
        )
        viewed = RecentlyViewed.model_validate(response.json())
        return viewed.model_copy(update={"recipes": viewed.recipes[:max_results]})

    @staticmethod
    def _check_max_results(max_results: int | None) -> None:
        if max_results is not None and max_results < 0:
            msg = "max_results must not be negative."
            raise ValueError(msg)

    @staticmethod
    def _should_fetch_next_page(
        *,
        collected: int,
        max_results: int | None,
        pagination: Pagination,
    ) -> bool:
        under_limit = max_results is None or collected < max_results
        return under_limit and pagination.page < pagination.max_page
