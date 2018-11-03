from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo
# import all of the Qt GUI library
from aqt.qt import *
import aqt

from anki.hooks import addHook, wrap
from aqt.fields import FieldDialog

from . import config

def fieldDialog__init__(self, mw, note, ord=0, parent=None):
    QDialog.__init__(self, parent or mw) #, Qt.Window)
    self.mw = aqt.mw
    self.parent = parent or mw
    self.note = note
    self.col = self.mw.col
    self.mm = self.mw.col.models
    self.model = note.model()
    self.mw.checkpoint(_("Fields"))
    self.form = aqt.forms.fields.Ui_Dialog()
    self.form.setupUi(self)

    self.markdownCheckbox = QCheckBox("Convert to/from markdown automatically")
    row = self.form._2.rowCount() + 1
    self.form._2.addWidget(self.markdownCheckbox, row, 1)

    self.setWindowTitle(_("Fields for %s") % self.model['name'])
    self.form.buttonBox.button(QDialogButtonBox.Help).setAutoDefault(False)
    self.form.buttonBox.button(QDialogButtonBox.Close).setAutoDefault(False)
    self.currentIdx = None
    self.oldSortField = self.model['sortf']
    self.fillFields()
    self.setupSignals()
    self.form.fieldList.setCurrentRow(0)
    self.exec_()
    
# after
def fieldDialogLoadField(self, idx):
    fld = self.model['flds'][self.currentIdx]
    self.markdownCheckbox.setChecked(fld['perform-auto-markdown'] if 'perform-auto-markdown' in fld else False)

# after
def fieldDialogSaveField(self):
    if self.currentIdx is None:
        return
    idx = self.currentIdx
    fld = self.model['flds'][idx]
    fld['perform-auto-markdown'] = self.markdownCheckbox.isChecked()
      


if (config.shouldShowEditFieldCheckbox()):
    FieldDialog.__init__ = fieldDialog__init__ # override until better solution
    FieldDialog.saveField = wrap(FieldDialog.saveField, fieldDialogSaveField)
    FieldDialog.loadField = wrap(FieldDialog.loadField, fieldDialogLoadField)