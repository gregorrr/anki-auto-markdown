import re

from aqt import mw
from aqt.utils import showInfo, showText
from aqt.qt import *
import aqt

from anki.utils import json, stripHTML

from .consts import addon_path

from . import markdown

from .markdown.extensions.abbr import AbbrExtension
from .markdown.extensions.codehilite import CodeHiliteExtension
from .markdown.extensions.def_list import DefListExtension
from .markdown.extensions.fenced_code import FencedCodeExtension
from .markdown.extensions.footnotes import FootnoteExtension

import os
import sys

from bs4 import BeautifulSoup, NavigableString, Tag
import base64

from . import config


def js_get_query_selector_by_field_id(field_id: int) -> str:
    """Returns the JavaScript code for selecting the editable area for a field."""

    return f"document.querySelector('.field[ord=\"{field_id}\"]').shadowRoot.querySelector('anki-editable')"


def generateHtmlFromMarkdown(field_plain, field_html):
    generated_html = markdown.markdown(
        field_plain,
        extensions=[
            AbbrExtension(),
            CodeHiliteExtension(
                noclasses=True,
                linenums=config.shouldShowCodeLineNums(),
                pygments_style=config.getCodeColorScheme(),
            ),
            DefListExtension(),
            FencedCodeExtension(),
            FootnoteExtension(),
        ],
        output_format="html5",
    )

    html_tree = BeautifulSoup(generated_html, "html.parser")
    first_tag = findFirstTag(html_tree)

    # No HTML tags in output
    if not first_tag:
        # if not md_text, add space to prevent input field from shrinking in UI
        html_tree = BeautifulSoup(
            "<div>" + ("&nbsp;" if not generated_html else generated_html) + "</div>",
            "html.parser",
        )
        first_tag = findFirstTag(html_tree)

    # store original text as data-attribute on tree root
    encoded_field_html = base64.b64encode(
        field_html.encode("utf-8")
    ).decode()  # needs to be string
    first_tag["data-original-markdown"] = encoded_field_html

    return str(html_tree)


def findFirstTag(tree):
    for c in tree.children:
        if type(c) is Tag:
            return c
    return None


# Get the original markdown text that was used to generate the html
def getOriginalTextFromGenerated(field_html):
    first_tag = findFirstTag(BeautifulSoup(field_html, "html.parser"))

    encoded_bytes = first_tag["data-original-markdown"].encode()
    return base64.b64decode(encoded_bytes).decode("utf-8")


def fieldIsGeneratedHtml(field_html):
    if field_html is None:
        return False

    tree = BeautifulSoup(field_html, "html.parser")
    first_tag = findFirstTag(tree)

    return (
        first_tag is not None
        and first_tag.attrs is not None
        and "data-original-markdown" in first_tag.attrs
    )


def enableFieldEditingJS(field_id):
    return f"""
    (function() {{
        var field = {js_get_query_selector_by_field_id(field_id)};

        if (field.classList.contains("auto-markdown-indicator")) {{
            field.setAttribute("onpaste", "onPaste(this);");
            field.setAttribute("oncut", "onCutOrCopy(this);");
            field.setAttribute("onkeydown", "onKey();");

            field.classList.remove("auto-markdown-indicator");
        }}
    }})()"""


def disableFieldEditingJS(field_id):

    try:
        # Not strictly PEP8 (probably) to import here, but it's cleaner to keep
        # it all contained just in case old Anki versions don't have a theme
        # manager
        from aqt.theme import theme_manager

        # TODO this colour should probably be configurable in the config.
        disable_edit_bg_color = (
            "#444231" if theme_manager.get_night_mode() else "#FFFDE7"
        )
    # Except this version of Anki does not have theme manager and/or Night Mode
    except (AttributeError, ImportError):
        disable_edit_bg_color = "#FFFDE7"

    return f"""
    (function() {{
        // need to create style because element.style.background is being overwritten.
        // from: https://davidwalsh.name/add-rules-stylesheets
        var style = document.getElementById("auto-markdown-style");
        if (!style) {{
            var style = document.createElement("style");
            style.appendChild(document.createTextNode(""));
            document.head.appendChild(style);

            style.setAttribute("id", "auto-markdown-style");
            style.sheet.insertRule(".auto-markdown-indicator {{ background: {disable_edit_bg_color} !important; }}");
        }}

        var field = {js_get_query_selector_by_field_id(field_id)};
        field.classList.add("auto-markdown-indicator");

        field.setAttribute("onpaste", "return false;");
        field.setAttribute("oncut", "return false;");
        // Allow Ctrl +, and Tab key
        field.setAttribute("onkeydown", "if(event.metaKey) return true; else if(event.keyCode === 9) return true; return false;");
    }})()"""

def onMarkdownToggle(editor: aqt.editor.Editor):

    # workaround for problem with editor.note.fields[field_id] sometimes not being populated
    def onHtmlAvailable(field_html):
        if editor and editor.web:
            edited_field_html = re.sub(
                r'<img src="(.*?)".*?>', r"![An image](\1)", field_html
            )
            editor.web.eval(
                f"""{js_get_query_selector_by_field_id(field_id)}.innerHTML = {json.dumps(edited_field_html)};"""
            )
            editor.web.evalWithCallback(
                f"{js_get_query_selector_by_field_id(field_id)}.innerText",
                lambda field_text: onInnerTextAvailable(field_html, field_text),
            )

    def onInnerTextAvailable(field_html, field_text):
        isGenerated = fieldIsGeneratedHtml(field_html)

        # convert back to plaintext
        if isGenerated:
            updated_field_html = getOriginalTextFromGenerated(field_html)
        # convert to html
        else:
            updated_field_html = generateHtmlFromMarkdown(field_text, field_html)

        if editor and editor.web:
            editor.web.eval(
                f"""{js_get_query_selector_by_field_id(field_id)}.innerHTML = {json.dumps(updated_field_html)};"""
            )
            editor.note.fields[field_id] = updated_field_html

            # re-enable editing after converting back to plaintext
            if isGenerated:
                editor.web.eval(enableFieldEditingJS(field_id))
            # disable editing after converting to html
            else:
                editor.web.eval(disableFieldEditingJS(field_id))

    field_id = editor.currentField
    editor.web.evalWithCallback(
        f"{js_get_query_selector_by_field_id(field_id)}.innerHTML", onHtmlAvailable
    )


class EditorController(object):
    def __init__(self):
        self.editor = None

    def emptyLoadNoteHook(self, editor):
        # need to save reference to editor as it's not passed to focus gained/lost hooks
        self.editor = editor

    def emptySetupEditorButtonsFilter(self, buttons, editor):
        self.editor = editor
        return buttons

    def setupEditorButtonsFilter(self, buttons, editor):
        key = QKeySequence(config.getManualMarkdownShortcut())
        keyStr = key.toString(QKeySequence.NativeText)

        b = self.editor.addButton(
            os.path.join(addon_path, "icons", "markdown.png"),
            "markdown_button",
            onMarkdownToggle,
            keys=config.getManualMarkdownShortcut(),
            tip="Convert to/from Markdown ({})".format(keyStr),
        )

        buttons.append(b)
        return buttons

    # automatically convert html back to markdown text
    def editFocusGainedHook(self, note, field_id):

        # changes made to the note object weren't represented in the UI, note.fields[field_id] = md, note.flush() etc.
        # Therefore let's set the value on the form ourselves

        field = note.model()["flds"][field_id]
        field_html = note.fields[field_id]

        if not self.editor or not self.editor.web or not field_html:
            return

        fieldIsAutoMarkdown = (
            "perform-auto-markdown" in field and field["perform-auto-markdown"]
        )
        isGenerated = fieldIsGeneratedHtml(field_html)

        # disable editing if field is generated html but not auto
        if not fieldIsAutoMarkdown and isGenerated:
            self.editor.web.eval(disableFieldEditingJS(field_id))

        elif config.isAutoMarkdownEnabled() and fieldIsAutoMarkdown and isGenerated:
            md = getOriginalTextFromGenerated(field_html)
            note.fields[field_id] = md
            self.editor.web.eval(
                f"""{js_get_query_selector_by_field_id(field_id)}.innerHTML = {json.dumps(md)};"""
            )

    # automatically convert markdown to html
    def editFocusLostFilter(self, _flag, note, field_id):
        def onInnerTextAvailable(field_text):
            updated_field_html = generateHtmlFromMarkdown(field_text, field_html)

            if self.editor and self.editor.web:
                self.editor.web.eval(
                    f"""{js_get_query_selector_by_field_id(field_id)}.innerHTML = {json.dumps(updated_field_html)};"""
                )
                self.editor.note.fields[field_id] = updated_field_html

        field = note.model()["flds"][field_id]
        field_html = note.fields[field_id]

        if not self.editor or not self.editor.web or not field_html:
            return _flag

        # remove markdown indicator
        self.editor.web.eval(enableFieldEditingJS(field_id))

        fieldIsAutoMarkdown = (
            "perform-auto-markdown" in field and field["perform-auto-markdown"]
        )
        isGenerated = fieldIsGeneratedHtml(field_html)

        if config.isAutoMarkdownEnabled() and fieldIsAutoMarkdown and not isGenerated:
            self.editor.web.evalWithCallback(
                f"{js_get_query_selector_by_field_id(field_id)}.innerText",
                onInnerTextAvailable,
            )

        return _flag  # Just pass _flag through, don't need to reload the note.


