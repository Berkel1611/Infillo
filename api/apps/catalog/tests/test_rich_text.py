"""The description validator is the only protection against stored XSS: the API takes JSON
from any client, not only from our editor, so every element must be on an allowlist."""

import copy
import json
from pathlib import Path

import pytest

from apps.catalog.rich_text import (
    MAX_DEPTH,
    MAX_DOCUMENT_CHARS,
    InvalidDescription,
    is_empty_description,
    validate_description,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tiptap_description.json"


def doc(*content) -> dict:
    return {"type": "doc", "content": list(content)}


def paragraph(*content) -> dict:
    return {"type": "paragraph", "content": list(content)}


def text(value: str = "tekst", *marks: dict) -> dict:
    node = {"type": "text", "text": value}
    if marks:
        node["marks"] = list(marks)
    return node


def link(href, **attrs) -> dict:
    return {"type": "link", "attrs": {"href": href, **attrs}}


def code_of(document) -> str:
    with pytest.raises(InvalidDescription) as exc:
        validate_description(document)
    return exc.value.code


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def nested(levels: int) -> dict:
    """A valid chain of lists whose node depth (doc = 1) equals `levels`."""
    node: dict = {"type": "paragraph", "content": [text()]}
    wrappers = ["listItem", "bulletList"]
    for index in range(levels - 2):
        node = {"type": wrappers[index % 2], "content": [node]}
    return doc(node)


# --- accepted ---


def test_editor_document_is_accepted():
    validate_description(load_fixture())


def test_empty_documents_are_accepted():
    validate_description({"type": "doc", "content": []})
    validate_description({"type": "doc"})
    validate_description(doc(paragraph()))


@pytest.mark.parametrize("href", ["https://example.com", "http://example.com/a?b=c#d"])
def test_http_and_https_links_are_accepted(href):
    validate_description(doc(paragraph(text("x", link(href)))))


def test_link_with_blank_target_rel_and_class_is_accepted():
    mark = link("https://a.pl", target=None, rel=None, **{"class": None})
    validate_description(doc(paragraph(text("x", mark))))


def test_nesting_up_to_the_limit_is_accepted():
    validate_description(nested(MAX_DEPTH))


# --- unknown nodes, marks, attributes ---


@pytest.mark.parametrize(
    "node",
    [
        {"type": "script", "content": []},
        {"type": "image", "attrs": {"src": "x.png"}},
        {"type": "codeBlock", "content": []},
        {"type": "blockquote", "content": [paragraph()]},
        {"type": "doc", "content": []},  # a doc nested inside a doc
        {"type": "horizontalRule"},
    ],
)
def test_unknown_node_rejected(node):
    assert code_of(doc(node)) == "node_not_allowed"


@pytest.mark.parametrize("mark", ["underline", "code", "strike", "highlight"])
def test_unknown_mark_rejected(mark):
    assert code_of(doc(paragraph(text("x", {"type": mark})))) == "mark_not_allowed"


@pytest.mark.parametrize("attrs", [{"onclick": "alert(1)"}, {"style": "color:red"}, {"id": "x"}])
def test_unknown_attribute_rejected_on_nodes_and_marks(attrs):
    heading = {"type": "heading", "attrs": {"level": 2, **attrs}, "content": [text()]}
    assert code_of(doc(heading)) == "attr_not_allowed"

    bold = {"type": "bold", "attrs": attrs}
    assert code_of(doc(paragraph(text("x", bold)))) == "attr_not_allowed"

    assert code_of(doc(paragraph(text("x", link("https://a.pl", **attrs))))) == "attr_not_allowed"


def test_unknown_key_on_a_node_rejected():
    assert code_of(doc({"type": "paragraph", "onclick": "alert(1)"})) == "attr_not_allowed"
    html = {"type": "text", "text": "x", "html": "<b>"}
    assert code_of(doc(paragraph(html))) == "attr_not_allowed"


@pytest.mark.parametrize("level", [1, 4, 7, 0, -2, "2", 2.0, True, None])
def test_heading_level_must_be_2_or_3(level):
    heading = {"type": "heading", "attrs": {"level": level}, "content": [text()]}
    assert code_of(doc(heading)) == "attr_not_allowed"


def test_heading_without_level_rejected():
    assert code_of(doc({"type": "heading", "content": [text()]})) == "attr_not_allowed"


@pytest.mark.parametrize("attrs", [{"start": 0}, {"start": -1}, {"start": "1"}, {"start": True}])
def test_ordered_list_start_must_be_a_positive_integer(attrs):
    node = {"type": "orderedList", "attrs": attrs, "content": []}
    assert code_of(doc(node)) == "attr_not_allowed"


@pytest.mark.parametrize("target", ["_self", "_top", "blank", "javascript:x", 1])
def test_link_target_must_be_blank_or_missing(target):
    mark = link("https://a.pl", target=target)
    assert code_of(doc(paragraph(text("x", mark)))) == "attr_not_allowed"


@pytest.mark.parametrize("attr", ["rel", "class"])
def test_link_rel_and_class_must_be_short_text(attr):
    for value in ("x" * 201, 5, ["a"]):
        mark = link("https://a.pl", **{attr: value})
        assert code_of(doc(paragraph(text("x", mark)))) == "attr_not_allowed"


# --- links ---


@pytest.mark.parametrize(
    "href",
    [
        "javascript:alert(1)",
        "javascript://example.com/%0Aalert(1)",  # has a host, so only the scheme check stops it
        "JAVASCRIPT://example.com/%0aalert(1)",
        "ftp://example.com/file",
        "ws://example.com/socket",
        "JaVaScRiPt:x",
        "java\tscript:x",
        "java\nscript:x",
        " javascript:x",
        "\x01javascript:x",
        " javascript:x",
        "data:text/html,x",
        "vbscript:x",
        "file:///etc/passwd",
        "//evil.pl",
        "/relative/path",
        "evil.pl",
        "mailto:a@b.pl",
        "tel:+48123456789",
        "http:///no-host",
        "http://[::1",  # urlparse raises ValueError
        "",
        "https://a.pl/" + "x" * 2100,
        "https://a.pl/ with space",
    ],
)
def test_dangerous_or_unsupported_href_rejected(href):
    assert code_of(doc(paragraph(text("x", link(href))))) == "link_not_allowed"


@pytest.mark.parametrize("href", [None, 5, ["https://a.pl"], {"a": 1}])
def test_non_string_href_rejected(href):
    assert code_of(doc(paragraph(text("x", link(href))))) == "link_not_allowed"


def test_link_without_href_rejected():
    mark = {"type": "link", "attrs": {"target": "_blank"}}
    assert code_of(doc(paragraph(text("x", mark)))) == "link_not_allowed"
    assert code_of(doc(paragraph(text("x", {"type": "link"})))) == "link_not_allowed"


# --- structure ---


@pytest.mark.parametrize(
    "document",
    [
        None,
        "x",
        5,
        [],
        [doc()],
        {},
        {"content": []},  # no type
        {"type": "paragraph", "content": []},  # the root is not a doc
        {"type": "doc", "content": "x"},  # content is not a list
        {"type": "doc", "content": {"type": "paragraph"}},
        {"type": "doc", "content": ["x"]},  # a child is not an object
        {"type": "doc", "content": [{"content": []}]},  # a child without type
        {"type": "doc", "content": [{"type": ["paragraph"]}]},  # type is not a string
        {"type": "doc", "attrs": "x"},
    ],
)
def test_malformed_document_rejected(document):
    assert code_of(document) == "invalid_document"


def test_text_node_must_have_string_text_and_list_marks():
    assert code_of(doc(paragraph({"type": "text"}))) == "invalid_document"
    assert code_of(doc(paragraph({"type": "text", "text": 5}))) == "invalid_document"
    string_marks = {"type": "text", "text": "x", "marks": "bold"}
    assert code_of(doc(paragraph(string_marks))) == "invalid_document"
    mark_not_object = {"type": "text", "text": "x", "marks": ["bold"]}
    assert code_of(doc(paragraph(mark_not_object))) == "invalid_document"


def test_text_node_cannot_have_content():
    node = {"type": "text", "text": "x", "content": []}
    assert code_of(doc(paragraph(node))) == "attr_not_allowed"


# --- limits ---


def test_document_over_the_size_limit_rejected():
    big = doc(paragraph(text("x" * (MAX_DOCUMENT_CHARS + 1))))
    assert code_of(big) == "document_too_large"


def test_document_under_the_size_limit_accepted():
    validate_description(doc(paragraph(text("x" * 90_000))))


def test_nesting_over_the_limit_rejected():
    assert code_of(nested(MAX_DEPTH + 1)) == "document_too_large"


def test_extremely_deep_document_is_rejected_not_crashing():
    node: dict = {"type": "paragraph"}
    for _ in range(5000):
        node = {"type": "bulletList", "content": [node]}
    assert code_of(doc(node)) == "document_too_large"


def test_validation_does_not_modify_the_document():
    document = load_fixture()
    before = copy.deepcopy(document)
    validate_description(document)
    assert document == before


# --- is_empty_description ---


@pytest.mark.parametrize(
    "document",
    [
        None,
        {},
        "x",
        {"type": "doc"},
        {"type": "doc", "content": []},
        doc(paragraph()),
        doc(paragraph(), paragraph()),
        doc(paragraph(text("   "))),
        doc(paragraph({"type": "hardBreak"})),
    ],
)
def test_empty_descriptions(document):
    assert is_empty_description(document) is True


def test_descriptions_with_content_are_not_empty():
    assert is_empty_description(doc(paragraph(text("Opis")))) is False
    assert is_empty_description(load_fixture()) is False
    item = {"type": "listItem", "content": [paragraph(text("punkt"))]}
    assert is_empty_description(doc({"type": "bulletList", "content": [item]})) is False
