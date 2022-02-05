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
            for tag in child:
                if remove:
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
    def regex_found(text: str, pattern: str, index: int = 0) -> str:
        """Regex found string by pattern and index."""
        found = re.compile(pattern, re.I).findall(text)
        return str(found[index]) if len(found) > index else ""
