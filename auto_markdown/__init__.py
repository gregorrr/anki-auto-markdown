# std
import sys
import os

# first add directory to path so pygments will resolve correctly
for p in sys.path:
    if p.endswith('addons21'):
        sys.path.append(os.path.join(p, __name__))
        break

# anki
from anki.hooks import addHook, wrap
from aqt.fields import FieldDialog
from aqt.editor import Editor

# local
from . import config
from . import fields
from .editor import EditorController 

def main():
    # fields
    if config.shouldShowEditFieldCheckbox():
        FieldDialog.__init__ = fields.fieldDialog__init__ # override until better solution
        FieldDialog.saveField = wrap(FieldDialog.saveField, fields.fieldDialogSaveField)
        FieldDialog.loadField = wrap(FieldDialog.loadField, fields.fieldDialogLoadField)

    # editor
    controller = EditorController()
    addHook("setupEditorButtons", controller.emptySetupEditorButtonsFilter)
    addHook("loadNote", controller.emptyLoadNoteHook)

    if config.shouldShowFieldMarkdownButton():
        addHook("setupEditorButtons", controller.setupEditorButtonsFilter)

    addHook("editFocusGained", controller.editFocusGainedHook)
    addHook("editFocusLost", controller.editFocusLostFilter)
    
main()
