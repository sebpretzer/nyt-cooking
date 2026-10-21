from collections.abc import Generator
from contextlib import contextmanager

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from fastmcp.exceptions import ToolError

from nyt_cooking.client import Client, Settings
from nyt_cooking.client.models import (
    Comments,
    Folder,
    Folders,
    IsAuthenticated,
    RecentlyViewed,
    Recipe,
    RecipeBox,
    SavedRecipe,
    SearchCriteria,
    SearchFilters,
    SearchResults,
)


@contextmanager
def _session_client() -> Generator[Client]:
    try:
        client = Client()
    except ValueError as exc:
        msg = f"Not logged in to NYT Cooking: {exc}"
        raise ToolError(msg) from exc
    with client:
        yield client


SessionClient = Depends(_session_client)

mcp = FastMCP(
    "nyt-cooking",
    instructions=(
        "Every NYT Cooking tool needs the user to be logged in with an NYT Cooking "
        "subscription. If a tool fails because they are not, ask the user for the "
        "`NYT-S` cookie from a browser signed in to cooking.nytimes.com with an NYT "
        "Cooking subscription, and call `auth_login`."
    ),
)


@mcp.tool(title="Get Search Filters", annotations={"readOnlyHint": True})
def get_search_filters(
    query: str = "",
    criteria: SearchCriteria | None = None,
    client: Client = SessionClient,
) -> SearchFilters:
    """List the tags and time limits worth filtering a recipe search by.

    Call this before filtering `search_recipes`. It takes the same `query` as
    `search_recipes`, and the counts are for that query, so only tags with at
    least one result are returned. An empty `query` returns every tag NYT Cooking
    has.

    Tag names are returned exactly as `search_recipes` expects them, such as
    `five ingredient` or `sheet-pan`. Pass `criteria` to see what is left once it
    is applied: counts shrink as filters are added, so use this to check that
    another tag would still leave results.

    Also returns the number of results within each total-time limit (in minutes)
    and the number that are top rated.

    Args:
        query (str): Search terms, such as a dish, ingredient or cuisine.
        criteria (SearchCriteria | None): Limits already chosen, such as tags from
            an earlier call. Leave unset on the first call.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SearchFilters: The tags, time limits and top-rated count, each with how
            many results it leaves.
    """
    return client.search_filters(query, criteria)


@mcp.tool(title="Search Recipes", annotations={"readOnlyHint": True})
def search_recipes(
    query: str,
    max_results: int = 48,
    criteria: SearchCriteria | None = None,
    client: Client = SessionClient,
) -> SearchResults:
    """Search NYT Cooking for recipes.

    Returns each match's ID, title, author and total time, plus the total number
    of matches. Pass an ID to `get_recipe` for ingredients and steps.

    To filter, call `get_search_filters` with the same `query` first and use the
    tag names it returns in `criteria`. Tags combine with AND, so each one narrows
    the results, and a misspelled or invented tag returns 0 results rather than an
    error.

    NYT stops at 960 results, however many match, so `max_results` above that
    returns no more.

    Args:
        query (str): Search terms, such as a dish, ingredient or cuisine.
        max_results (int): Most recipes to return.
        criteria (SearchCriteria | None): Tags, a time limit, top-rated only, sort
            order to narrow by. Leave unset for no limits.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SearchResults: The matching recipes.
    """
    return client.search_recipes_paginated(
        query,
        max_results=max_results,
        criteria=criteria,
    )


@mcp.tool(title="Get Recipe", annotations={"readOnlyHint": True})
def get_recipe(recipe_id: int, client: Client = SessionClient) -> Recipe:
    """Get a full NYT Cooking recipe.

    Includes the ingredients and steps (both grouped under any headings the recipe
    uses), times, servings, rating and introduction.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `search_recipes`,
            `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Recipe: The recipe.
    """
    return client.get_recipe(recipe_id)


@mcp.tool(title="Get Recipe Comments", annotations={"readOnlyHint": True})
def get_recipe_comments(
    recipe_id: int,
    max_results: int = 20,
    *,
    helpful_only: bool = False,
    client: Client = SessionClient,
) -> Comments:
    """Get the public reader comments on an NYT Cooking recipe.

    Readers use comments to share substitutions, fixes and results, and NYT Cooking
    staff sometimes reply to answer questions; their comments are marked
    `is_staff`. Each comment includes all of its replies.

    Comments come newest first. Set `helpful_only` to get only the comments readers
    picked as most helpful, most helpful first, as on the recipe page's "Most
    Helpful" tab. `total` counts every comment on the recipe, replies included,
    and `helpful_total` the most helpful ones.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `search_recipes`,
            `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`.
        max_results (int): Most top-level comments to return, replies aside.
        helpful_only (bool): Whether to get only the most helpful comments.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Comments: The comments, with the recipe's comment totals.
    """
    return client.get_recipe_comments_paginated(
        recipe_id,
        max_results=max_results,
        helpful_only=helpful_only,
    )


@mcp.tool(title="Get Recipe Box", annotations={"readOnlyHint": True})
def get_recipe_box(
    max_results: int = 48,
    folder_id: int | None = None,
    client: Client = SessionClient,
) -> RecipeBox:
    """List the recipes the user has saved to their NYT Cooking recipe box.

    Pass `folder_id` to list one folder's recipes.

    Args:
        max_results (int): Most saved recipes to return.
        folder_id (int | None): NYT Cooking folder ID, from `get_folders`. Leave
            unset for the whole recipe box.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        RecipeBox: The saved recipes and the total number saved.
    """
    return client.get_recipe_box_paginated(
        max_results=max_results,
        folder_id=folder_id,
    )


@mcp.tool(title="Get Recently Viewed", annotations={"readOnlyHint": True})
def get_recently_viewed(
    max_results: int = 20,
    client: Client = SessionClient,
) -> RecentlyViewed:
    """List the recipes the user has recently viewed on NYT Cooking.

    Most recent first.

    Args:
        max_results (int): Most recently viewed recipes to return.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        RecentlyViewed: The recently viewed recipes.
    """
    return client.get_recently_viewed(max_results=max_results)


@mcp.tool(title="Get Folders", annotations={"readOnlyHint": True})
def get_folders(client: Client = SessionClient) -> Folders:
    """List the folders in the user's NYT Cooking recipe box.

    Alphabetical, with each folder's ID and number of recipes.

    Args:
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Folders: The recipe box folders.
    """
    return client.get_folders()


@mcp.tool(title="Get Folder Recipes", annotations={"readOnlyHint": True})
def get_folder_recipes(folder_id: int, client: Client = SessionClient) -> RecipeBox:
    """List every recipe in a folder of the user's NYT Cooking recipe box.

    Args:
        folder_id (int): NYT Cooking folder ID, from `get_folders`.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        RecipeBox: The folder's recipes and how many it holds.
    """
    return client.get_folder_recipes(folder_id)


@mcp.tool(title="Add Folder", annotations={"destructiveHint": False})
def add_folder(name: str, client: Client = SessionClient) -> Folder:
    """Add an empty folder to the user's NYT Cooking recipe box.

    Args:
        name (str): Name of the new folder.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Folder: The new folder.
    """
    name = _folder_name(name)
    return client.create_folder(name)


@mcp.tool(title="Rename Folder", annotations={"destructiveHint": True})
def rename_folder(folder_id: int, name: str, client: Client = SessionClient) -> Folder:
    """Rename a folder in the user's NYT Cooking recipe box.

    Args:
        folder_id (int): NYT Cooking folder ID, from `get_folders`.
        name (str): New name for the folder.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Folder: The renamed folder.
    """
    name = _folder_name(name)
    return client.rename_folder(folder_id, name)


@mcp.tool(title="Remove Folder", annotations={"destructiveHint": True})
def remove_folder(folder_id: int, client: Client = SessionClient) -> Folders:
    """Remove a folder from the user's NYT Cooking recipe box, deleting it.

    The folder's recipes stay saved to the recipe box.

    Args:
        folder_id (int): NYT Cooking folder ID, from `get_folders`.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Folders: The folders left in the recipe box.
    """
    return client.delete_folder(folder_id)


@mcp.tool(title="Get Recipe Save Status", annotations={"readOnlyHint": True})
def get_recipe_save_status(
    recipe_id: int,
    client: Client = SessionClient,
) -> SavedRecipe:
    """Check whether a recipe is saved to the user's NYT Cooking recipe box.

    Also lists the recipe box folders it is in.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `search_recipes`,
            `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SavedRecipe: Whether the recipe is saved, and its folders.
    """
    return client.get_saved_recipe(recipe_id)


@mcp.tool(title="Add Recipe", annotations={"destructiveHint": False})
def add_recipe(
    recipe_id: int,
    folder_id: int | None = None,
    client: Client = SessionClient,
) -> SavedRecipe:
    """Add a recipe to the user's NYT Cooking recipe box, or to a folder in it.

    Without `folder_id`, the recipe is saved to the recipe box. With `folder_id`, it
    is also added to that folder, since every recipe in a folder is saved to the
    recipe box. Adding a recipe that is already saved, or already in the folder,
    changes nothing.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `search_recipes`,
            `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`.
        folder_id (int | None): NYT Cooking folder ID to also add the recipe to,
            from `get_folders`. Leave unset to add it to the recipe box only.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SavedRecipe: Whether the recipe is saved, and its folders, afterwards.
    """
    return client.save_recipe(recipe_id, folder_id)


@mcp.tool(title="Remove Recipe", annotations={"destructiveHint": True})
def remove_recipe(
    recipe_id: int,
    folder_id: int | None = None,
    client: Client = SessionClient,
) -> SavedRecipe:
    """Remove a recipe from the user's NYT Cooking recipe box, or from one folder.

    Without `folder_id`, the recipe is removed from the recipe box and from every
    folder it is in. Removing a recipe that is not saved changes nothing. With
    `folder_id`, the recipe is removed from that folder only, and stays saved to the
    recipe box and its other folders; it fails if the recipe is not in the folder.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `get_recipe_box`,
            `get_folder_recipes` or `get_recipe_save_status`.
        folder_id (int | None): NYT Cooking folder ID to remove the recipe from,
            from `get_recipe_save_status` or `get_folders`. Leave unset to remove it
            from the recipe box and every folder.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SavedRecipe: Whether the recipe is saved, and its folders, afterwards.
    """
    return client.unsave_recipe(recipe_id, folder_id)


def _folder_name(name: str) -> str:
    name = name.strip()
    if not name:
        msg = "A folder name is required."
        raise ToolError(msg)
    return name


@mcp.tool(title="Log In", annotations={"destructiveHint": True})
def auth_login(cookie: str) -> IsAuthenticated:
    """Check the user's NYT Cooking cookie and save it if NYT accepts it.

    The user copies the cookie from their browser while signed in to cooking.nytimes.com
    (developer tools, then cookies, then `NYT-S`). NYT must recognise it as an account
    with an active NYT Cooking subscription; otherwise this fails, and nothing is saved.

    Args:
        cookie (str): Value of the `NYT-S` cookie.

    Returns:
        IsAuthenticated: That the user is now logged in.

    Raises:
        ToolError: If the cookie is empty, or NYT does not accept it.
    """
    cookie = cookie.strip()
    if not cookie:
        msg = "The NYT-S cookie is required."
        raise ToolError(msg)
    try:
        Client(cookie).close()
    except ValueError as exc:
        msg = f"{exc} The cookie was not saved."
        raise ToolError(msg) from exc
    Settings.save_credentials(cookie)
    return IsAuthenticated(authenticated=True)


@mcp.tool(title="Log Out", annotations={"destructiveHint": True})
def auth_logout() -> IsAuthenticated:
    """Remove the saved NYT Cooking cookie.

    Returns whether the user is still logged in afterwards, which is only true when
    a cookie is also configured outside the saved login, such as in the
    `NYT_COOKING_COOKIE` environment variable.

    Returns:
        IsAuthenticated: Whether the user is still logged in.
    """
    Settings.clear_credentials()
    return get_auth_status()


@mcp.tool(title="Get Login Status", annotations={"readOnlyHint": True})
def get_auth_status() -> IsAuthenticated:
    """Check with NYT whether the user is logged in with an NYT Cooking subscription.

    Returns false when no cookie is saved, NYT no longer recognises it, or the
    account's NYT Cooking subscription has lapsed.

    Returns:
        IsAuthenticated: Whether the user is logged in.
    """
    try:
        Client().close()
    except ValueError:
        return IsAuthenticated(authenticated=False)
    return IsAuthenticated(authenticated=True)
