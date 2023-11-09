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

FieldDialog__saveField__old = FieldDialog.saveField
FieldDialog__loadField__old = FieldDialog.loadField

# This function used to exist in fields.py, but since it needs access to
# FieldDialog, it makes sense to define it all in one file
def FieldDialog__loadField__new(self, *args, **kwargs):
    FieldDialog__loadField__old(self, *args, **kwargs)
    if self.currentIdx is None:
        return
    fld = self.model['flds'][self.currentIdx]
    self.markdownCheckbox.setChecked(fld['perform-auto-markdown'] if 'perform-auto-markdown' in fld else False)

# This function used to exist in fields.py, but since it needs access to
# FieldDialog, it makes sense to define it all in one file
def FieldDialog__saveField__new(self, *args, **kwargs):
    FieldDialog__saveField__old(self, *args, **kwargs)

    if self.currentIdx is None:
        return

    fld = self.model['flds'][self.currentIdx]
    perform_auto_markdown = self.markdownCheckbox.isChecked()
    # This is part of a change tracker introduced in later (at least 2.1.33+) versions of Anki
    if fld.get("perform-auto-markdown") != perform_auto_markdown:
        fld["perform-auto-markdown"] = perform_auto_markdown
        self.change_tracker.mark_basic()

def main():
    # fields
    if config.shouldShowEditFieldCheckbox():
        FieldDialog.__init__ = fields.FieldDialog____init__ # override until better solution
        FieldDialog.saveField = wrap(FieldDialog.saveField, FieldDialog__saveField__new)
        FieldDialog.loadField = wrap(FieldDialog.loadField, FieldDialog__loadField__new)

    # editor
    controller = EditorController()
    addHook("setupEditorButtons", controller.emptySetupEditorButtonsFilter)
    addHook("loadNote", controller.emptyLoadNoteHook)

    if config.shouldShowFieldMarkdownButton():
        addHook("setupEditorButtons", controller.setupEditorButtonsFilter)

    addHook("editFocusGained", controller.editFocusGainedHook)
    addHook("editFocusLost", controller.editFocusLostFilter)
    
main()
