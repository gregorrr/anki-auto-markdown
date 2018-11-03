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

def generateHtmlFromMarkdown(field_text, field_html):
    
    field_text = field_text.replace("\xc2\xa0", " ").replace("\xa0", " ") # non-breaking space

    md_text = markdown.markdown(field_text, extensions=[
        AbbrExtension(),
        AdmonitionExtension(),
        CodeHiliteExtension(
            noclasses = True, 
            linenums = config.shouldShowCodeLineNums(), 
            pygments_style = config.getCodeColorScheme()
        ),
        DefListExtension(),
        FencedCodeExtension(),
        FootnoteExtension(),
        MetaExtension()
        ])

    md_tree = BeautifulSoup(md_text, 'html.parser')

    # store original text as data-attribute on tree root
    encoded_field_html = base64.b64encode(field_html.encode('utf-8')).decode() # needs to be string

    first_tag = findFirstTag(md_tree)
    first_tag['data-original-markdown'] = encoded_field_html

    return str(md_tree)


def findFirstTag(tree):
    for c in tree.children:
        if type(c) is Tag:
            return c
    return None


# Get the original markdown text that was used to generate the html
def getOriginalTextFromGenerated(field_html):
    first_tag = findFirstTag(BeautifulSoup(field_html, 'html.parser'))

    encoded_bytes = first_tag['data-original-markdown'].encode()
    return base64.b64decode(encoded_bytes).decode('utf-8')


def fieldIsGeneratedHtml(field_html):
    if field_html is None:
        return False

    tree = BeautifulSoup(field_html, 'html.parser')
    first_tag = findFirstTag(tree)

    return first_tag is not None and first_tag.attrs is not None and 'data-original-markdown' in first_tag.attrs


def onMarkdownToggle(editor):
    field_id = editor.currentField
    field_html = editor.note.fields[field_id]

    if not field_html:
        return

    def onInnerTextAvailable(field_text):
        isGenerated = fieldIsGeneratedHtml(field_html)
        
        # convert back to plaintext
        if isGenerated:
            updated_field_html = getOriginalTextFromGenerated(field_html)
        # convert to html
        else:
            updated_field_html = generateHtmlFromMarkdown(field_text, field_html)
        
        if editor:
            editor.web.eval("""document.getElementById('f%s').innerHTML = %s;""" % (field_id, json.dumps(updated_field_html)))
            editor.note.fields[field_id] = updated_field_html

    editor_instance.web.evalWithCallback("document.getElementById('f%s').innerText" % (field_id), onInnerTextAvailable)


def setupEditorButtonsFilter(buttons, editor):
    # need to save reference to editor as it's not passed to other hooks
    global editor_instance
    editor_instance = editor

    key = QKeySequence(config.getManualMarkdownShortcut())
    keyStr = key.toString(QKeySequence.NativeText)

    if config.shouldShowFieldMarkdownButton():
        b = editor.addButton(
            os.path.join(addon_path, "icons", "markdown.png"), 
            "markdown_button", onMarkdownToggle, 
            keys=config.getManualMarkdownShortcut(), 
            tip="Convert to/from Markdown ({})".format(keyStr))

        buttons.append(b)

    return buttons


# automatically convert html back to markdown text
def editFocusGainedHook(note, field_id):
    # changes made to the note object weren't represented in the UI, note.fields[field_id] = md, note.flush() etc.
    # Therefore let's set the value on the form ourselves
    global editor_instance

    field = note.model()['flds'][field_id]
    field_html = note.fields[field_id]

    if not editor_instance or not field_html:
        return

    fieldIsAutoMarkdown = field['perform-auto-markdown'] if 'perform-auto-markdown' in field else False
    isGenerated = fieldIsGeneratedHtml(field_html)

    if config.isAutoMarkdownEnabled() and fieldIsAutoMarkdown and isGenerated:
        md = getOriginalTextFromGenerated(field_html)
        note.fields[field_id] = md
        editor_instance.web.eval("""document.getElementById('f%s').innerHTML = %s;""" % (field_id, json.dumps(md)))
       

# automatically convert markdown to html
def editFocusLostFilter(_flag, note, field_id):

    def onInnerTextAvailable(field_text):
        updated_field_html = generateHtmlFromMarkdown(field_text, field_html)

        if editor_instance:
            editor_instance.web.eval("""document.getElementById('f%s').innerHTML = %s;""" % (field_id, json.dumps(updated_field_html)))
            editor_instance.note.fields[field_id] = updated_field_html

    global editor_instance

    field = note.model()['flds'][field_id]
    field_html = note.fields[field_id]

    if not editor_instance or not field_html:
        return _flag

    fieldIsAutoMarkdown = field['perform-auto-markdown'] if 'perform-auto-markdown' in field else False
    isGenerated = fieldIsGeneratedHtml(field_html)

    if config.isAutoMarkdownEnabled() and fieldIsAutoMarkdown and not isGenerated:
        editor_instance.web.evalWithCallback("document.getElementById('f%s').innerText" % (field_id), onInnerTextAvailable)

    return _flag # Just pass _flag through, don't need to reload the note.
    
    

addHook("setupEditorButtons", setupEditorButtonsFilter)
addHook("editFocusGained", editFocusGainedHook)
addHook("editFocusLost", editFocusLostFilter)