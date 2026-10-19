from __future__ import annotations

import pytest

from nyt_cooking.client.models.base import _strip_html


class TestStripHtml:
    @pytest.mark.parametrize(
        ("raw", "plain"),
        [
            ("<p>Hello <b>there</b></p>", "Hello there"),
            ("a &amp; b", "a & b"),
            ("  spaced\n  out  ", "spaced out"),
            ("no tags", "no tags"),
            ("<p>Mix.</p><p>Bake.</p>", "Mix. Bake."),
            ("Salt<br>pepper", "Salt pepper"),
            ("Salt<br/>pepper", "Salt pepper"),
            ("pre<strong>heat</strong> the oven", "preheat the oven"),
        ],
    )
    def test_strips_tags_entities_and_whitespace(self, raw: str, plain: str) -> None:
        assert _strip_html(raw) == plain
