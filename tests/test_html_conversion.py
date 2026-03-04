"""Tests for HTML to Markdown conversion."""

from azwork.utils import ImageCollector, html_to_markdown, slugify


class TestHtmlToMarkdown:
    def test_empty_string(self):
        assert html_to_markdown("") == ""

    def test_plain_text(self):
        assert html_to_markdown("Hello world") == "Hello world"

    def test_bold(self):
        assert "**bold**" in html_to_markdown("<b>bold</b>")
        assert "**strong**" in html_to_markdown("<strong>strong</strong>")

    def test_italic(self):
        assert "*italic*" in html_to_markdown("<i>italic</i>")
        assert "*emphasis*" in html_to_markdown("<em>emphasis</em>")

    def test_inline_code(self):
        assert "`code`" in html_to_markdown("<code>code</code>")

    def test_pre_block(self):
        result = html_to_markdown("<pre>some code</pre>")
        assert "```" in result
        assert "some code" in result

    def test_link(self):
        result = html_to_markdown('<a href="https://example.com">click</a>')
        assert "[click](https://example.com)" in result

    def test_image(self):
        result = html_to_markdown('<img src="pic.png" alt="photo">')
        assert "![photo](pic.png)" in result

    def test_unordered_list(self):
        html = "<ul><li>one</li><li>two</li><li>three</li></ul>"
        result = html_to_markdown(html)
        assert "- one" in result
        assert "- two" in result
        assert "- three" in result

    def test_ordered_list(self):
        html = "<ol><li>first</li><li>second</li></ol>"
        result = html_to_markdown(html)
        assert "1. first" in result
        assert "2. second" in result

    def test_paragraph(self):
        result = html_to_markdown("<p>paragraph one</p><p>paragraph two</p>")
        assert "paragraph one" in result
        assert "paragraph two" in result

    def test_br(self):
        result = html_to_markdown("line one<br>line two")
        assert "line one\nline two" in result

    def test_table(self):
        html = "<table><tr><th>Name</th><th>Age</th></tr><tr><td>Alice</td><td>30</td></tr></table>"
        result = html_to_markdown(html)
        assert "| Name | Age |" in result
        assert "| --- | --- |" in result
        assert "| Alice | 30 |" in result

    def test_div(self):
        result = html_to_markdown("<div>content</div>")
        assert "content" in result

    def test_nested_tags(self):
        result = html_to_markdown("<p><b>bold</b> and <i>italic</i></p>")
        assert "**bold**" in result
        assert "*italic*" in result

    def test_heading(self):
        result = html_to_markdown("<h2>Title</h2>")
        assert "## Title" in result

    def test_strips_unknown_tags(self):
        result = html_to_markdown("<custom>text</custom>")
        assert "text" in result

    def test_empty_bold(self):
        result = html_to_markdown("<b></b>")
        assert "**" not in result

    def test_image_no_alt(self):
        result = html_to_markdown('<img src="pic.png">')
        assert "![image](pic.png)" in result


class TestImageCollector:
    def test_rewrites_http_url(self):
        c = ImageCollector(assets_prefix="./assets")
        result = c.rewrite("https://dev.azure.com/org/_apis/wit/attachments/abc.png", "shot")
        assert result == "./assets/image-1.png"
        assert len(c.images) == 1
        assert c.images[0][0] == "https://dev.azure.com/org/_apis/wit/attachments/abc.png"

    def test_preserves_relative_path(self):
        c = ImageCollector(assets_prefix="./assets")
        result = c.rewrite("images/local.png", "local")
        assert result == "images/local.png"
        assert len(c.images) == 0

    def test_preserves_extension(self):
        c = ImageCollector(assets_prefix="./assets")
        c.rewrite("https://example.com/photo.jpg", "photo")
        assert c.images[0][1] == "image-1.jpg"

    def test_defaults_to_png(self):
        c = ImageCollector(assets_prefix="./assets")
        c.rewrite("https://example.com/noext", "img")
        assert c.images[0][1] == "image-1.png"

    def test_sequential_numbering(self):
        c = ImageCollector(assets_prefix="./assets")
        c.rewrite("https://example.com/a.png", "a")
        c.rewrite("https://example.com/b.png", "b")
        assert c.images[0][1] == "image-1.png"
        assert c.images[1][1] == "image-2.png"

    def test_empty_src(self):
        c = ImageCollector(assets_prefix="./assets")
        result = c.rewrite("", "alt")
        assert result == ""
        assert len(c.images) == 0

    def test_no_prefix(self):
        c = ImageCollector(assets_prefix="")
        result = c.rewrite("https://example.com/a.png", "a")
        assert result == "image-1.png"


class TestImageCollectorInHtml:
    def test_img_tag_rewritten(self):
        c = ImageCollector(assets_prefix="./1234-assets")
        result = html_to_markdown(
            '<p><img src="https://dev.azure.com/img.png" alt="screenshot"></p>',
            image_collector=c,
        )
        assert "![screenshot](./1234-assets/image-1.png)" in result
        assert len(c.images) == 1

    def test_multiple_images(self):
        c = ImageCollector(assets_prefix="./assets")
        html_to_markdown(
            '<img src="https://a.com/1.png" alt="one"><img src="https://b.com/2.jpg" alt="two">',
            image_collector=c,
        )
        assert len(c.images) == 2

    def test_no_collector_preserves_urls(self):
        result = html_to_markdown('<img src="https://dev.azure.com/img.png" alt="ss">')
        assert "https://dev.azure.com/img.png" in result

    def test_local_image_not_rewritten(self):
        c = ImageCollector(assets_prefix="./assets")
        result = html_to_markdown('<img src="local.png" alt="loc">', image_collector=c)
        assert "![loc](local.png)" in result
        assert len(c.images) == 0


class TestSlugify:
    def test_basic(self):
        assert slugify("Login fails with special chars") == "login-fails-with-special-chars"

    def test_special_chars(self):
        assert slugify("Test & verify <things>") == "test-verify-things"

    def test_max_length(self):
        result = slugify("A" * 100, max_length=20)
        assert len(result) <= 20

    def test_empty(self):
        assert slugify("") == ""
