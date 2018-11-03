from aqt import mw
from aqt.utils import showInfo, showText
from aqt.qt import *

from anki.hooks import addHook, wrap
from anki.utils import json, stripHTML

from .consts import addon_path

from . import markdown

from .markdown.extensions.abbr import AbbrExtension
from .markdown.extensions.admonition import AdmonitionExtension
from .markdown.extensions.codehilite import CodeHiliteExtension
from .markdown.extensions.def_list import DefListExtension
from .markdown.extensions.fenced_code import FencedCodeExtension
from .markdown.extensions.footnotes import FootnoteExtension
from .markdown.extensions.meta import MetaExtension

#from .markdown.extensions.attr_list import AttrListExtension
#from .markdown.extensions.headerid import HeaderIdExtension
#from .markdown.extensions.nl2br import Nl2BrExtension
#from .markdown.extensions.sane_lists import SaneListExtension
#from .markdown.extensions.smart_strong import SmartEmphasisExtension
#from .markdown.extensions.smarty import SmartyExtension
#from .markdown.extensions.toc import TocExtension
#from .markdown.extensions.wikilinks import WikiLinkExtension


import os
import sys

from bs4 import BeautifulSoup, NavigableString, Tag
import base64

from . import config


editor_instance = None

# Tags like <div><br /></div> are included automatically by Html editor
# See https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Editable_content
def getPlainTextFromHtmlEditorField(field_text):
    parts = []

    def getPlainTextHelper(node):
        if type(node) is BeautifulSoup:
            for child in node.children:
                getPlainTextHelper(child)

        elif type(node) is Tag:
            # ignore <br /> in <div></div>
            if node.name == 'br' and node.parent.name == 'div' and len(node.parent.contents) == 1:
                pass

            elif node.name in ['div', 'br']:
                parts.append('\n')
                for child in node.children:
                    getPlainTextHelper(child)

            else:
                parts.append('<{0}>' % node.name)
                for child in node.children:
                    getPlainTextHelper(child)
                parts.append('</{0}>' % node.name)

        elif type(node) is NavigableString:
            parts.append(str(node.string))


    getPlainTextHelper(BeautifulSoup(field_text, 'html.parser'))
    return ''.join(parts)

def generateHtmlFromMarkdown(field_text):
    plain = getPlainTextFromHtmlEditorField(field_text)

    md_text = markdown.markdown(plain, extensions=[
        AbbrExtension(),
        AdmonitionExtension(),
        CodeHiliteExtension(noclasses = True, 
        linenums = config.shouldShowCodeLineNums(), 
        pygments_style = config.getCodeColorScheme()),
        DefListExtension(),
        FencedCodeExtension(), 
        FootnoteExtension(),
        MetaExtension()
        ])
    
    md_tree = BeautifulSoup(md_text, 'html.parser')

    # store original text as data-attribute on tree root
    encoded_field_text = base64.b64encode(field_text.encode('utf-8')).decode() # needs to be string

    first_tag = findFirstTag(md_tree)
    first_tag['data-original-markdown'] = encoded_field_text

    return str(md_tree)


def findFirstTag(tree):
    for c in tree.children:
        if type(c) is Tag:
            return c
    return None


# Get the original markdown text that was used to generate the html
def getOriginalTextFromGenerated(field_text):
    first_tag = findFirstTag(BeautifulSoup(field_text, 'html.parser'))

    encoded_bytes = first_tag['data-original-markdown'].encode()
    return base64.b64decode(encoded_bytes).decode('utf-8')



def fieldIsGeneratedHtml(field_text):

    if field_text is None:
        return False

    tree = BeautifulSoup(field_text, 'html.parser')
    first_tag = findFirstTag(tree)

    return first_tag is not None and first_tag.attrs is not None and 'data-original-markdown' in first_tag.attrs


def onMarkdownToggle(editor):
    field_id = editor.currentField
    field_text = editor.note.fields[field_id]

    if not field_text:
        return

    isGenerated = fieldIsGeneratedHtml(field_text)

    # convert back to plaintext
    if isGenerated:
        updated_field_text = getOriginalTextFromGenerated(field_text)
    # convert to html
    else:
        updated_field_text = generateHtmlFromMarkdown(field_text)
        
    editor.web.eval("""document.getElementById('f%s').innerHTML = %s;""" % (field_id, json.dumps(updated_field_text)))
    editor.note.fields[field_id] = updated_field_text


def setupEditorButtonsFilter(buttons, editor):
    global editor_instance
    editor_instance = editor

    key = QKeySequence(config.getManualMarkdownShortcut())
    keyStr = key.toString(QKeySequence.NativeText)

    b = editor.addButton(
        os.path.join(addon_path, "icons", "markdown.png"), 
        "markdown_button", 
        onMarkdownToggle, 
        keys=config.getManualMarkdownShortcut(), 
        tip="Convert to/from Markdown ({})".format(keyStr))
    buttons.append(b)

    return buttons

# automatically convert back to markdown text
def editFocusGainedHook(note, field_id):
    # changes made to the note object weren't represented in the UI, 
    # note.fields[field_id] = md
    # note.flush() etc.
    # therefore let's set the value on the form ourselves

    global editor_instance

    field = note.model()['flds'][field_id]
    field_text = note.fields[field_id]

    if not editor_instance or not field_text:
        return

    fieldIsAutoMarkdown = field['perform-auto-markdown'] if 'perform-auto-markdown' in field else False
    isGenerated = fieldIsGeneratedHtml(field_text)

    if config.isAutoMarkdownEnabled() and fieldIsAutoMarkdown and isGenerated:
        md = getOriginalTextFromGenerated(field_text)
        note.fields[field_id] = md
        editor_instance.web.eval("""document.getElementById('f%s').innerHTML = %s;""" % (field_id, json.dumps(md)))


# automatically convert to html
def editFocusLostFilter(_flag, note, field_id):

    field = note.model()['flds'][field_id]
    field_text = note.fields[field_id]

    if not field_text:
        return _flag

    fieldIsAutoMarkdown = field['perform-auto-markdown'] if 'perform-auto-markdown' in field else False
    isGenerated = fieldIsGeneratedHtml(field_text)

    if config.isAutoMarkdownEnabled() and fieldIsAutoMarkdown and not isGenerated:
        note.fields[field_id] = generateHtmlFromMarkdown(field_text)
        return True
    else:
        return _flag
    

addHook("setupEditorButtons", setupEditorButtonsFilter)
addHook("editFocusGained", editFocusGainedHook)
addHook("editFocusLost", editFocusLostFilter)