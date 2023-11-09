from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo
# import all of the Qt GUI library
from aqt.qt import *
import aqt

from aqt import AnkiQt
from anki.models import NoteType
from aqt.schema_change_tracker import ChangeTracker

# local
from . import config

def FieldDialog____init__(self, mw: AnkiQt, nt: NoteType, parent=None):
    QDialog.__init__(self, parent or mw)
    self.mw = mw
    self.col = self.mw.col
    self.mm = self.mw.col.models
    self.model = nt
    self.mm._remove_from_cache(self.model["id"])
    self.mw.checkpoint(_("Fields"))
    self.change_tracker = ChangeTracker(self.mw)
    self.form = aqt.forms.fields.Ui_Dialog()
    self.form.setupUi(self)

    # Added for auto markdown
    self.markdownCheckbox = QCheckBox("Convert to/from markdown automatically")
    row = self.form._2.rowCount() + 1
    self.form._2.addWidget(self.markdownCheckbox, row, 1)


    self.setWindowTitle(_("Fields for %s") % self.model["name"])
    self.form.buttonBox.button(QDialogButtonBox.Help).setAutoDefault(False)
    self.form.buttonBox.button(QDialogButtonBox.Cancel).setAutoDefault(False)
    self.form.buttonBox.button(QDialogButtonBox.Save).setAutoDefault(False)
    self.currentIdx = None
    self.oldSortField = self.model["sortf"]
    self.fillFields()
    self.setupSignals()
    self.form.fieldList.setDragDropMode(QAbstractItemView.InternalMove)
    self.form.fieldList.dropEvent = self.onDrop
    self.form.fieldList.setCurrentRow(0)
    self.exec_()

