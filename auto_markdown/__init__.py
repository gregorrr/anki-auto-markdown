# std
import sys
import os

# anki
from anki.hooks import addHook, wrap
from aqt.fields import FieldDialog

# local
from . import config
from . import fields
from .editor import AnkiMarkdown 

from ._version import __version__

def main():

    for p in sys.path:
        if (p.endswith('addons21')):
            sys.path.append(os.path.join(p, __name__))
            break

    # fields
    if (config.shouldShowEditFieldCheckbox()):
        FieldDialog.__init__ = fields.fieldDialog__init__ # override until better solution
        FieldDialog.saveField = wrap(FieldDialog.saveField, fields.fieldDialogSaveField)
        FieldDialog.loadField = wrap(FieldDialog.loadField, fields.fieldDialogLoadField)

    # editor
    anki_markdown = AnkiMarkdown()
    addHook("setupEditorButtons", anki_markdown.setupEditorButtonsFilter)
    addHook("editFocusGained", anki_markdown.editFocusGainedHook)
    addHook("editFocusLost", anki_markdown.editFocusLostFilter)
    addHook("loadNote", anki_markdown.loadNoteHook)

main()
