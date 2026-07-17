"""Tests for code structure compression masks."""

from dataclasses import dataclass, field

from headroom.compression.handlers import code_handler
from headroom.compression.handlers.code_handler import CodeStructureHandler


@dataclass
class _Node:
    type: str
    start_byte: int
    end_byte: int
    children: list["_Node"] = field(default_factory=list)


class _Parser:
    def __init__(self, root: _Node):
        self.root = root

    def parse(self, _content: bytes):
        return type("Tree", (), {"root_node": self.root})()


def test_tree_sitter_byte_offsets_are_mapped_to_characters(monkeypatch):
    """Non-ASCII text before code must not shift the structural mask."""
    content = "# café\ndef foo():\n    return 1\n"
    encoded = content.encode("utf-8")
    function_start = encoded.index(b"def")
    body_start = encoded.index(b"\n    return") + 1
    body_end = len(encoded)
    body = _Node("block", body_start, body_end)
    function = _Node("function_definition", function_start, body_end, [body])
    root = _Node("module", 0, body_end, [function])
    monkeypatch.setattr(code_handler, "_get_parser", lambda _language: _Parser(root))

    tokens = list(content)
    result = CodeStructureHandler()._extract_with_tree_sitter(content, tokens, "python")

    signature_start = content.index("def")
    assert result.mask.mask[signature_start] is True
    assert result.mask.mask[signature_start - 1] is False
