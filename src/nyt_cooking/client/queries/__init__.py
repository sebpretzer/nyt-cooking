"""GraphQL queries sent to NYT's GraphQL API, one `.graphql` file per query."""

from importlib.resources import files


def _load(name: str) -> str:
    return files(__name__).joinpath(name).read_text()


RECIPE_COMMENTS = _load("recipe_comments.graphql")
