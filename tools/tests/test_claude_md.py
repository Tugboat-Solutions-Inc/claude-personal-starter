import textwrap

import pytest

from tools.lib import claude_md as cm


def test_parse_blocks_returns_empty_for_empty_string():
    assert cm.parse_blocks("") == ({}, "")


def test_parse_blocks_extracts_single_block():
    text = textwrap.dedent("""\
        # >>> claude-personal-starter: tool-gmail
        Gmail content here.
        # <<< claude-personal-starter: tool-gmail
        """)
    blocks, free = cm.parse_blocks(text)
    assert "tool-gmail" in blocks
    assert blocks["tool-gmail"].strip() == "Gmail content here."
    assert free.strip() == ""


def test_parse_blocks_preserves_freeform_content_outside_markers():
    text = textwrap.dedent("""\
        Top freeform line.

        # >>> claude-personal-starter: tool-gmail
        Gmail content.
        # <<< claude-personal-starter: tool-gmail

        Middle freeform.

        # >>> claude-personal-starter: tool-calendar
        Calendar content.
        # <<< claude-personal-starter: tool-calendar

        Bottom freeform.
        """)
    blocks, free = cm.parse_blocks(text)
    assert set(blocks.keys()) == {"tool-gmail", "tool-calendar"}
    assert "Top freeform line." in free
    assert "Middle freeform." in free
    assert "Bottom freeform." in free
    assert "Gmail content" not in free


def test_parse_blocks_raises_on_mismatched_markers():
    text = textwrap.dedent("""\
        # >>> claude-personal-starter: a
        x
        # <<< claude-personal-starter: b
        """)
    with pytest.raises(cm.ClaudeMdError, match="mismatched"):
        cm.parse_blocks(text)


def test_parse_blocks_raises_on_unclosed_block():
    text = "# >>> claude-personal-starter: a\nx\n"
    with pytest.raises(cm.ClaudeMdError, match="unclosed"):
        cm.parse_blocks(text)


def test_compose_writes_blocks_in_id_order_then_freeform():
    blocks = {"b": "B content", "a": "A content"}
    free = "User's own notes."
    result = cm.compose(blocks, free)
    a_pos = result.index("a")
    b_pos = result.index("b")
    assert a_pos < b_pos
    assert "User's own notes." in result


def test_compose_then_parse_is_identity():
    blocks = {"x": "X", "y": "Y"}
    free = "freeform stuff"
    result = cm.compose(blocks, free)
    blocks2, free2 = cm.parse_blocks(result)
    assert blocks2 == blocks
    assert free2.strip() == free.strip()


def test_apply_changes_adds_new_block():
    blocks, free = ({}, "")
    new_blocks, new_free = cm.apply_changes(
        blocks, free, add={"tool-gmail": "Gmail fragment"}, remove=set()
    )
    assert new_blocks == {"tool-gmail": "Gmail fragment"}


def test_apply_changes_removes_block_but_keeps_others_and_freeform():
    blocks = {"a": "A", "b": "B"}
    free = "user notes"
    new_blocks, new_free = cm.apply_changes(blocks, free, add={}, remove={"a"})
    assert new_blocks == {"b": "B"}
    assert new_free == "user notes"


def test_apply_changes_replaces_block_when_added_with_same_id():
    blocks = {"a": "old"}
    new_blocks, _ = cm.apply_changes(blocks, "", add={"a": "new"}, remove=set())
    assert new_blocks == {"a": "new"}
