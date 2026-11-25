"""Tests for ao3fetch.toMarkdown HTML-to-Markdown conversion."""

from __future__ import annotations

import ao3fetch


def test_to_markdown_handles_fiction_formatting() -> None:
    """toMarkdown preserves italics, bold, outer spaces, scene breaks, quotes, and links."""
    html = (
        "<p>Hello <em> world </em> and <strong>bold</strong>.</p>"
        + "<p>&nbsp;</p>"
        + "<hr />"
        + '<blockquote><p>A quote with <a href="https://example.com">a link</a>.</p></blockquote>'
        + "<ul><li>First</li><li>Second</li></ul>"
    )
    md = ao3fetch.toMarkdown(html)
    assert "Hello _world_ and **bold**." in md
    assert "\n\n---\n\n" in md
    assert "> A quote with [a link](https://example.com)." in md
    assert "- First\n- Second" in md


def test_to_markdown_preserves_setext_headings_and_line_breaks() -> None:
    """`<br>\\n` stays a single break, preserving underlined Markdown headings instead of `<p>+<hr>`."""
    assert ao3fetch.toMarkdown("<p>Waking<br />\n------</p>\n<p>Ithari wakes.</p>") == "Waking\n------\n\nIthari wakes."
    assert ao3fetch.toMarkdown("<p>Part One<br />\n========</p>") == "Part One\n========"

    # Regular `<br>\n` (including source indentation) remains a single Markdown hard line break.
    assert ao3fetch.toMarkdown("<p>\n  As always:\n  <br>\n  Elvhen names\n</p>") == "As always:  \nElvhen names"

    # Double `<br>` collapses cleanly into a paragraph break without dangling trailing spaces.
    assert ao3fetch.toMarkdown("<div>First para.<br />\n<br />\nSecond para.</div>") == "First para.\n\nSecond para."

    # List continuation indentation, multi-paragraph blockquotes, and `<pre>` spacing stay intact.
    assert ao3fetch.toMarkdown("<ul><li>First<br />\nSecond</li></ul>") == "- First  \n  Second"
    assert ao3fetch.toMarkdown("<blockquote>\n  <p>One.</p>\n  <p>Two.</p>\n</blockquote>") == "> One.\n>\n> Two."
    assert ao3fetch.toMarkdown("<pre><code>  x   =   1\n    y = 2</code></pre>") == "```\n  x   =   1\n    y = 2\n```"
