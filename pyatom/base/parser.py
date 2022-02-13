# -*- coding: utf-8 -*-

"""
    Base Parser for html document.
"""

from typing import Union

import regex as re
from selectolax.parser import HTMLParser


__all__ = ("BaseParser",)


class BaseParser:
    """Base Parser, code could be use else where."""

    @staticmethod
    def as_str(document: Union[str, HTMLParser]) -> str:
        """Auto transform HTMLParser to string if not yet."""
        return document if isinstance(document, str) else str(document.html)

    @staticmethod
    def as_node(document: Union[str, HTMLParser]) -> HTMLParser:
        """Auto transform string to HTMLParser if not yet."""
        return document if isinstance(document, HTMLParser) else HTMLParser(document)

    @staticmethod
    def remove_child(node: HTMLParser, selector: str) -> HTMLParser:
        """Decompose node child by css selector."""
        for tag in node.css(selector):
            tag.decompose()
        return node

    @staticmethod
    def collect_list(
        node: HTMLParser, selector: str, strip: bool = False, remove: bool = True
    ) -> tuple[HTMLParser, list[str]]:
        """Collect ordered or un ordered list items, return cleaned node and list of string."""
        list_str: list[str] = []
        child = node.css(selector)
        if child:
            list_str = [tag.text(strip=strip) for tag in child]
            if remove:
                for tag in child:
                    tag.decompose()
        return node, list_str

    @staticmethod
    def crlf(node: HTMLParser) -> HTMLParser:
        """Replace node `<br>` with line break for better operation."""
        for tag in node.css("br"):
            tag.replace_with("\n")
        return node

    @staticmethod
    def attr(node: HTMLParser, name: str) -> str:
        """Get node attribute as string."""
        value = node.attributes.get(name)
        return value if isinstance(value, str) else ""

    def first_attr(self, node: HTMLParser, selector: str, attr_name: str) -> str:
        """Get attribute value string of first child tag."""
        tag = node.css_first(selector)
        return self.attr(tag, attr_name) if tag else ""

    def first_attr_opt(
        self, node: HTMLParser, selector: str, attr_name: str, remove: bool = False
    ) -> tuple[HTMLParser, str]:
        """Get attribute value string of first child tag with option to remove child tag."""
        text = ""
        tag = node.css_first(selector)
        if tag:
            text = self.attr(tag, attr_name)
            if remove:
                tag.decompose()
        return node, text

    @staticmethod
    def first_text(node: HTMLParser, selector: str, strip: bool = False) -> str:
        """First child tag text string."""
        text = ""
        tag = node.css_first(selector)
        if tag:
            text = tag.text(strip=strip)
        return text

    @staticmethod
    def first_text_opt(
        node: HTMLParser, selector: str, strip: bool = False, remove: bool = False
    ) -> tuple[HTMLParser, str]:
        """Get child tag text string with option to remove child tag."""
        text = ""
        tag = node.css_first(selector)
        if tag:
            text = tag.text(strip=strip)
            if remove:
                tag.decompose()
        return node, text

    @staticmethod
    def regex_find(text: str, raw: str, flags: int = 0, index: int = 0) -> str:
        """Find string by regex pattern raw string, pattern flags and index."""
        found = re.compile(raw, flags).findall(text)
        return str(found[index]) if len(found) > index else ""


class TestBaseParser:
    """TestCase for BaseParser."""

    parser = BaseParser()
    document = """<html><head><title>Title</title></head> <body> <div id='div_one'> <ul> <li> list_item_0 </li> <br> <li> list_item_1 </li> </ul> </div> <br> <div id='div_two'> div_two_text </div>  <div id='div_two'> hello Hello</div>  </body></html>"""

    def test_to_node(self) -> None:
        """Return node and string for self.document."""
        doc_str = self.parser.as_str(document=self.document)
        doc_node = self.parser.as_node(document=self.document)
        assert isinstance(doc_str, str)
        assert isinstance(doc_node, HTMLParser)

    def test_remove_child(self) -> None:
        """Test remove child."""
        doc_node = self.parser.as_node(document=self.document)
        node = self.parser.remove_child(node=doc_node, selector="#div_one")
        assert "div_one" not in node.text()

    def test_collect_list(self) -> None:
        """Test collect list."""
        doc_node = self.parser.as_node(document=self.document)
        node, list_text = self.parser.collect_list(node=doc_node, selector="li")
        assert all("list_item" in text for text in list_text)
        assert "list_item" not in self.parser.as_str(node)

        doc_node = self.parser.as_node(document=self.document)
        node, list_text = self.parser.collect_list(
            node=doc_node, selector="li", remove=False
        )
        assert "list_item" in self.parser.as_str(node)

    def test_crlf(self) -> None:
        """Test crlf."""
        doc_node = self.parser.as_node(document=self.document)
        assert "<br>" in self.document
        node = self.parser.crlf(node=doc_node)
        assert "<br>" not in node.text()

    def test_attr(self) -> None:
        """Test attr."""
        doc_node = self.parser.as_node(document=self.document)
        node_div = doc_node.css_first("#div_one")
        assert self.parser.attr(node=node_div, name="id") == "div_one"

        doc_node = self.parser.as_node(document=self.document)
        attr_value = self.parser.first_attr(
            node=doc_node, selector="div", attr_name="id"
        )
        assert attr_value == "div_one"

        doc_node = self.parser.as_node(document=self.document)
        node, attr_value = self.parser.first_attr_opt(
            node=doc_node, selector="div", attr_name="id"
        )
        assert attr_value == "div_one"
        assert "div_one" in self.parser.as_str(node)

        doc_node = self.parser.as_node(document=self.document)
        node, attr_value = self.parser.first_attr_opt(
            node=doc_node, selector="div", attr_name="id", remove=True
        )
        assert attr_value == "div_one"
        assert "div_one" not in self.parser.as_str(node)

    def test_text(self) -> None:
        """Test text."""
        doc_node = self.parser.as_node(document=self.document)
        text = self.parser.first_text(node=doc_node, selector="#div_two")
        assert "div_two_text" in text
        assert len(text) > len("div_two_text")

        doc_node = self.parser.as_node(document=self.document)
        text = self.parser.first_text(node=doc_node, selector="#div_two", strip=True)
        assert "div_two_text" in text
        assert len(text) == len("div_two_text")

        doc_node = self.parser.as_node(document=self.document)
        node, text = self.parser.first_text_opt(node=doc_node, selector="#div_two")
        assert "div_two_text" in text
        assert "div_two_text" in self.parser.as_str(node)

        doc_node = self.parser.as_node(document=self.document)
        node, text = self.parser.first_text_opt(
            node=doc_node, selector="#div_two", remove=True
        )
        assert "div_two_text" in text
        assert "div_two_text" not in self.parser.as_str(node)

    def test_regex_find(self) -> None:
        """Test regex find."""
        found_str = self.parser.regex_find(text=self.document, raw=r"hello")
        assert found_str == "hello"
        found_str = self.parser.regex_find(
            text=self.document, raw=r"hello", flags=re.I, index=1
        )
        assert found_str == "Hello"


if __name__ == "__main__":
    app = TestBaseParser()
