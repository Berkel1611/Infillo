"""Validation of product descriptions (TipTap / ProseMirror JSON).

The description is user data shown to other people, so it is a stored-XSS target. The API takes
JSON from any client, not only from our editor, hence an allowlist: every node, mark and
attribute that is not listed below is rejected with an error code (nothing is silently
stripped). The frontend editor (web/src/shared/rich-text/extensions.ts) must offer exactly the
same elements; when you change one list, change the other.

The document is never turned into an HTML string on the server or in the browser: the frontend
renders it through the same TipTap schema, which is why a rejected or odd node can't run code.
"""

import json
import unicodedata
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

MAX_DOCUMENT_CHARS = 100_000
MAX_DEPTH = 10  # doc = 1; text leaves don't count
MAX_HREF_LENGTH = 2048
MAX_ATTR_TEXT_LENGTH = 200
ALLOWED_LINK_SCHEMES = frozenset({"http", "https"})  # no mailto: (working decision, stage 2 spec)
ORDERED_LIST_TYPES = frozenset({"1", "a", "A", "i", "I"})


class InvalidDescription(Exception):
    """`code` is one of: invalid_document, node_not_allowed, mark_not_allowed, attr_not_allowed,
    link_not_allowed, document_too_large (the last one also covers nesting that is too deep)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> InvalidDescription:
    return InvalidDescription(code)


# --- attribute checks: each returns None or raises InvalidDescription ---


def _heading_level(value: Any) -> None:
    # type() is, not isinstance: True is an int in Python and 2.0 is not what the editor sends
    if type(value) is not int or value not in (2, 3):
        raise _fail("attr_not_allowed")


def _list_start(value: Any) -> None:
    if type(value) is not int or value < 1:
        raise _fail("attr_not_allowed")


def _list_type(value: Any) -> None:
    if value is not None and value not in ORDERED_LIST_TYPES:
        raise _fail("attr_not_allowed")


def _link_target(value: Any) -> None:
    if value is not None and value != "_blank":
        raise _fail("attr_not_allowed")


def _short_text(value: Any) -> None:
    if value is not None and (not isinstance(value, str) or len(value) > MAX_ATTR_TEXT_LENGTH):
        raise _fail("attr_not_allowed")


def _link_href(value: Any) -> None:
    """Only absolute http(s) URLs. Anything that could carry a script (javascript:, data:,
    vbscript:...) or that a browser might normalise into one is rejected."""
    if not isinstance(value, str) or not value or len(value) > MAX_HREF_LENGTH:
        raise _fail("link_not_allowed")
    # Browsers drop tabs and newlines inside a scheme ("java\tscript:"), so no whitespace and
    # no control characters anywhere, not only at the start
    if any(ch.isspace() or unicodedata.category(ch).startswith("C") for ch in value):
        raise _fail("link_not_allowed")
    try:
        parts = urlsplit(value)
    except ValueError:  # e.g. "http://[::1"
        raise _fail("link_not_allowed") from None
    if parts.scheme.lower() not in ALLOWED_LINK_SCHEMES or not parts.netloc:
        raise _fail("link_not_allowed")  # also rejects "//evil.pl" and relative paths


AttrCheck = Callable[[Any], None]

# node type -> allowed attributes and their checks
NODE_ATTRS: dict[str, dict[str, AttrCheck]] = {
    "doc": {},
    "paragraph": {},
    "text": {},
    "heading": {"level": _heading_level},
    "bulletList": {},
    "orderedList": {"start": _list_start, "type": _list_type},
    "listItem": {},
    "hardBreak": {},
}
MARK_ATTRS: dict[str, dict[str, AttrCheck]] = {
    "bold": {},
    "italic": {},
    "link": {
        "href": _link_href,
        "target": _link_target,
        "rel": _short_text,
        "class": _short_text,
        "title": _short_text,  # TipTap 3 always emits it (null unless set)
    },
}
# attributes that must be present, and the error code when they are not
REQUIRED_ATTRS: dict[str, tuple[str, str]] = {
    "heading": ("level", "attr_not_allowed"),
    "link": ("href", "link_not_allowed"),
}
NODE_KEYS = frozenset({"type", "attrs", "content"})
TEXT_NODE_KEYS = frozenset({"type", "text", "marks"})
MARK_KEYS = frozenset({"type", "attrs"})


def _check_attrs(kind: str, attrs: Any, allowed: dict[str, AttrCheck]) -> None:
    if attrs is None:
        attrs = {}
    if not isinstance(attrs, dict):
        raise _fail("invalid_document")
    for key, value in attrs.items():
        check = allowed.get(key)
        if check is None:
            raise _fail("attr_not_allowed")
        check(value)
    required = REQUIRED_ATTRS.get(kind)
    if required and required[0] not in attrs:
        raise _fail(required[1])


def _check_mark(mark: Any) -> None:
    if not isinstance(mark, dict) or not isinstance(mark.get("type"), str):
        raise _fail("invalid_document")
    kind = mark["type"]
    if kind not in MARK_ATTRS:
        raise _fail("mark_not_allowed")
    if not set(mark) <= MARK_KEYS:
        raise _fail("attr_not_allowed")
    _check_attrs(kind, mark.get("attrs"), MARK_ATTRS[kind])


def _check_node(node: Any, depth: int) -> None:
    if not isinstance(node, dict) or not isinstance(node.get("type"), str):
        raise _fail("invalid_document")
    kind = node["type"]
    if kind not in NODE_ATTRS or (kind == "doc" and depth > 1):
        raise _fail("node_not_allowed")

    if kind == "text":  # a leaf: not counted in the depth
        if not set(node) <= TEXT_NODE_KEYS:
            raise _fail("attr_not_allowed")
        if not isinstance(node.get("text"), str):
            raise _fail("invalid_document")
        marks = node.get("marks", [])
        if not isinstance(marks, list):
            raise _fail("invalid_document")
        for mark in marks:
            _check_mark(mark)
        return

    if depth > MAX_DEPTH:
        raise _fail("document_too_large")  # checked before descending: recursion stays shallow
    if not set(node) <= NODE_KEYS:
        raise _fail("attr_not_allowed")
    _check_attrs(kind, node.get("attrs"), NODE_ATTRS[kind])
    content = node.get("content", [])
    if not isinstance(content, list):
        raise _fail("invalid_document")
    for child in content:
        _check_node(child, depth + 1)


def validate_description(doc: object) -> None:
    """Raises InvalidDescription unless `doc` is a document made only of allowed elements."""
    if not isinstance(doc, dict) or doc.get("type") != "doc":
        raise _fail("invalid_document")
    try:
        size = len(json.dumps(doc, ensure_ascii=False))
    except RecursionError:
        raise _fail("document_too_large") from None
    except (TypeError, ValueError):
        raise _fail("invalid_document") from None
    if size > MAX_DOCUMENT_CHARS:
        raise _fail("document_too_large")
    _check_node(doc, 1)


def is_empty_description(doc: object) -> bool:
    """True when there is nothing to read: no document, or no text other than whitespace."""
    if not isinstance(doc, dict):
        return True
    stack: list[Any] = [doc]  # a stack instead of recursion: safe on any depth
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        text = node.get("text")
        if isinstance(text, str) and text.strip():
            return False
        content = node.get("content")
        if isinstance(content, list):
            stack.extend(content)
    return True
