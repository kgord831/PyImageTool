from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from typing import List
import os
import fnmatch
from .DataMatrix import RegularDataArray
from .CMapEditor import list_cmaps, load_ct, load_ct_icon
from functools import partial


class InfoBar(QtWidgets.QWidget):
    """Based on the input data, create a suitable info bar (maybe with tabs?)"""
    transpose_request = QtCore.pyqtSignal(object)

    def __init__(self, data: RegularDataArray, parent=None):
        super().__init__(parent)
        self.data = data
        labels = ['X', 'Y', 'Z', 'T']
        if data.ndim > 4:
            raise ValueError("Input data for more than 4 dimensions not supported")
        # The main layout for this widget
        self.setLayout(QtWidgets.QHBoxLayout())
        # Create the cursor group box
        self.cursor_group_box = QtWidgets.QGroupBox("Cursor Info")
        self.cursor_grid_layout = QtWidgets.QGridLayout()
        self.cursor_group_box.setLayout(self.cursor_grid_layout)
        self.cursor_index_label = QtWidgets.QLabel("Index")
        self.cursor_coord_label = QtWidgets.QLabel("Coord")
        self.cursor_grid_layout.addWidget(self.cursor_index_label, 0, 1)
        self.cursor_grid_layout.addWidget(self.cursor_coord_label, 0, 2)
        self.cursor_labels = []  # labels for each cursor position
        self.cursor_i = []  # cursor position as index into data
        self.cursor_c = []  # cursor position in coordinate
        # TODO: set minimize size policy for the spinbox labels for Qt 5.14
        for i in range(data.ndim):
            label = QtWidgets.QLabel(self.data.dims[i])
            label.setAlignment(QtCore.Qt.AlignCenter)
            i_sb = QtWidgets.QSpinBox()
            i_sb.setRange(0, data.shape[i] - 1)
            i_sb.setWrapping(True)
            c_sb = QtWidgets.QDoubleSpinBox()
            c_sb.setRange(data.coord_min[i], data.coord_max[i])
            self.cursor_grid_layout.addWidget(label, i + 1, 0)
            self.cursor_grid_layout.addWidget(i_sb, i + 1, 1)
            self.cursor_grid_layout.addWidget(c_sb, i + 1, 2)
            self.cursor_labels.append(label)
            self.cursor_i.append(i_sb)
            self.cursor_c.append(c_sb)
        # Create the binning group box
        self.bin_group_box = QtWidgets.QGroupBox("Binning")
        self.bin_grid_layout = QtWidgets.QGridLayout()
        self.bin_group_box.setLayout(self.bin_grid_layout)
        self.bin_width_label = QtWidgets.QLabel("Width")
        self.bin_grid_layout.addWidget(self.bin_width_label, 0, 1, 1, 2)
        self.bin_labels = []  # labels for each bin
        self.bin_i: List[QtWidgets.QSpinBox] = []  # bin width in index notation
        self.bin_c: List[QtWidgets.QDoubleSpinBox] = []  # bin width in coordinate notation
        for i in range(data.ndim):
            label = QtWidgets.QLabel(self.data.dims[i])
            label.setAlignment(QtCore.Qt.AlignCenter)
            i_sb = QtWidgets.QSpinBox()
            i_sb.setRange(1, data.shape[i])
            c_sb = QtWidgets.QDoubleSpinBox()
            c_sb.setRange(data.delta[i], data.coord_max[i] - data.coord_min[i] + data.delta[i])
            self.bin_grid_layout.addWidget(label, i + 1, 0)
            self.bin_grid_layout.addWidget(i_sb, i + 1, 1)
            self.bin_grid_layout.addWidget(c_sb, i + 1, 2)
            self.bin_labels.append(label)
            self.bin_i.append(i_sb)
            self.bin_c.append(c_sb)
        self.final_column = QtWidgets.QVBoxLayout()
        # Create the data edit group box
        self.data_manip_group_box = QtWidgets.QGroupBox("Data Manipulation")
        self.data_manip_group_box.setLayout(QtWidgets.QHBoxLayout())
        self.transpose_button = QtWidgets.QPushButton('Transpose')
        self.transpose_button.clicked.connect(self.transpose_clicked)
        self.data_manip_group_box.layout().addWidget(self.transpose_button)
        self.data_manip_group_box.layout().addStretch(0)
        # Create the colormap group box
        self.cmap_group_box = QtWidgets.QGroupBox("Colormap")
        self.cmap_form_layout = QtWidgets.QFormLayout()
        self.cmap_group_box.setLayout(self.cmap_form_layout)
        self.cmap_label = QtWidgets.QLabel("Set all Colormaps")
        self.cmap_combobox = QtWidgets.QComboBox()
        self.cmap_form_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.cmap_label)
        self.cmap_form_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.cmap_combobox)
        for cmap in list_cmaps():
            self.cmap_combobox.addItem(load_ct_icon(cmap), cmap)
        self.cmap_combobox.setIconSize(QtCore.QSize(64, 12))
        self.cmap_combobox.setCurrentText('viridis')
        # Add the group boxes to create this widget
        self.layout().addWidget(self.cursor_group_box)
        self.layout().addWidget(self.bin_group_box)
        self.final_column.addWidget(self.data_manip_group_box)
        self.final_column.addWidget(self.cmap_group_box)
        self.layout().addLayout(self.final_column)
        # self.layout().addWidget(self.cmap_group_box)

    def reset(self, data: RegularDataArray):
        self.data = data
        for i in range(data.ndim):
            self.cursor_i[i].setRange(0, data.shape[i] - 1)
            self.cursor_c[i].setRange(data.coord_min[i], data.coord_max[i])
            self.bin_i[i].setRange(1, data.shape[i])
            self.bin_c[i].setRange(data.delta[i], data.coord_max[i] - data.coord_min[i] + data.delta[i])
            self.cursor_labels[i].setText(data.dims[i])
            self.bin_labels[i].setText(data.dims[i])

    def transpose_clicked(self):
        dialog = TransposeDialog(self.data)
        r = dialog.exec()
        if r == 1:
            tr = dialog.widget.get_transpose()
            self.transpose_request.emit(tr)


class AspectRatioForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(150, 24)
        Form.setMaximumSize(QtCore.QSize(150, 16777215))
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setContentsMargins(2, 2, 2, 2)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.aspectRatio = QtWidgets.QLineEdit(Form)
        self.aspectRatio.setObjectName("aspectRatio")
        self.gridLayout.addWidget(self.aspectRatio, 0, 1, 1, 1)
        self.lockAspect = QtWidgets.QCheckBox(Form)
        self.lockAspect.setObjectName("lockAspect")
        self.gridLayout.addWidget(self.lockAspect, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.aspectRatio.setText(_translate("Form", "1"))
        self.lockAspect.setText(_translate("Form", "Lock Aspect"))


class TransposeDialog(QtWidgets.QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.widget = TransposeAxesWidget(data, parent=self)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.widget)
        self.widget.ok_button.clicked.connect(self.accept)
        self.widget.cancel_button.clicked.connect(self.reject)


class TransposeAxesWidget(QtWidgets.QWidget):
    def __init__(self, data: RegularDataArray, parent=None):
        super().__init__(parent)
        self.ndim = data.ndim
        self.main_layout = QtWidgets.QVBoxLayout()
        self.panel_layout = QtWidgets.QGridLayout()
        self.ok_cancel_layout = QtWidgets.QHBoxLayout()

        self.current_dim_label = QtWidgets.QLabel('Current Dim')
        self.separator = QtWidgets.QFrame(self)
        self.separator.setFrameShape(QtWidgets.QFrame.VLine)
        self.separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.new_dim_label = QtWidgets.QLabel('New Dim', parent=self)

        self.dim_labels = [QtWidgets.QLabel(str(i), parent=self) for i in range(self.ndim)]
        self.rows = [QtWidgets.QButtonGroup(self) for _ in range(self.ndim)]
        self.cols = [QtWidgets.QButtonGroup(self) for _ in range(self.ndim)]
        self.buttons = [[QtWidgets.QRadioButton(str(j), parent=self) for j in range(self.ndim)] for _ in range(self.ndim)]
        for i in range(self.ndim):
            for j in range(self.ndim):
                self.buttons[i][j].setAutoExclusive(False)
                self.buttons[i][j].clicked.connect(partial(self.validate_click, i, j))
            self.buttons[i][i].setChecked(True)

        self.ok_button = QtWidgets.QPushButton('OK', parent=self)
        self.cancel_button = QtWidgets.QPushButton('Cancel', parent=self)

        self.panel_layout.addWidget(self.current_dim_label, 0, 0)
        self.panel_layout.addWidget(self.separator, 0, 1, self.ndim + 1, 1)
        self.panel_layout.addWidget(self.new_dim_label, 0, 2, 1, self.ndim)
        for i in range(self.ndim):
            self.panel_layout.addWidget(self.dim_labels[i], i + 1, 0)
            for j in range(self.ndim):
                self.panel_layout.addWidget(self.buttons[i][j], i + 1, j + 2)

        self.ok_cancel_layout.addWidget(self.ok_button)
        self.ok_cancel_layout.addWidget(self.cancel_button)

        self.main_layout.addLayout(self.panel_layout)
        self.main_layout.addLayout(self.ok_cancel_layout)
        self.setLayout(self.main_layout)

    def validate_click(self, i, j, checked):
        """
        If the button i, j was already set (checked = False), then set the i, j button to where it was.
        If the button i, j was not already set, there are exactly two buttons in the same row and column which are also
        checked. Find those two buttons, and then swap their col indices to determine which new buttons should be
        checked.
        """
        coords = []
        if checked:
            for x in range(self.ndim):
                if x != i:
                    if self.buttons[x][j].isChecked():
                        coords.append((x, j))
                        self.buttons[x][j].setChecked(False)
                if x != j:
                    if self.buttons[i][x].isChecked():
                        self.buttons[i][x].setChecked(False)
                        coords.append((i, x))
            self.buttons[coords[0][0]][coords[1][1]].setChecked(True)
            self.buttons[coords[1][0]][coords[0][1]].setChecked(True)
        else:
            self.buttons[i][j].setChecked(True)

    def get_transpose(self):
        """Return a dictionary mapping current index to the new index. Guaranteed to be valid."""
        mapping = {}
        for i in range(self.ndim):
            for j in range(self.ndim):
                if self.buttons[i][j].isChecked():
                    mapping[i] = j
        return mapping


class Ui_TransposeAxes(object):
    def setupUi(self, TransposeAxes):
        TransposeAxes.setObjectName("TransposeAxes")
        TransposeAxes.resize(224, 152)
        self.gridLayout = QtWidgets.QGridLayout(TransposeAxes)
        self.gridLayout.setObjectName("gridLayout")
        self.table20 = QtWidgets.QRadioButton(TransposeAxes)
        self.table20.setObjectName("table20")
        self.row2 = QtWidgets.QButtonGroup(TransposeAxes)
        self.row2.setObjectName("row2")
        self.row2.addButton(self.table20)
        self.gridLayout.addWidget(self.table20, 3, 2, 1, 1)
        self.table11 = QtWidgets.QRadioButton(TransposeAxes)
        self.table11.setObjectName("table11")
        self.row1 = QtWidgets.QButtonGroup(TransposeAxes)
        self.row1.setObjectName("row1")
        self.row1.addButton(self.table11)
        self.gridLayout.addWidget(self.table11, 2, 3, 1, 1)
        self.table30 = QtWidgets.QRadioButton(TransposeAxes)
        self.table30.setObjectName("table30")
        self.row3 = QtWidgets.QButtonGroup(TransposeAxes)
        self.row3.setObjectName("row3")
        self.row3.addButton(self.table30)
        self.gridLayout.addWidget(self.table30, 4, 2, 1, 1)
        self.table12 = QtWidgets.QRadioButton(TransposeAxes)
        self.table12.setObjectName("table12")
        self.row1.addButton(self.table12)
        self.gridLayout.addWidget(self.table12, 2, 4, 1, 1)
        self.okButton = QtWidgets.QPushButton(TransposeAxes)
        self.okButton.setObjectName("okButton")
        self.gridLayout.addWidget(self.okButton, 5, 0, 1, 3)
        self.label = QtWidgets.QLabel(TransposeAxes)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.table33 = QtWidgets.QRadioButton(TransposeAxes)
        self.table33.setObjectName("table33")
        self.row3.addButton(self.table33)
        self.gridLayout.addWidget(self.table33, 4, 5, 1, 1)
        self.table01 = QtWidgets.QRadioButton(TransposeAxes)
        self.table01.setObjectName("table01")
        self.row0 = QtWidgets.QButtonGroup(TransposeAxes)
        self.row0.setObjectName("row0")
        self.row0.addButton(self.table01)
        self.gridLayout.addWidget(self.table01, 1, 3, 1, 1)
        self.table21 = QtWidgets.QRadioButton(TransposeAxes)
        self.table21.setObjectName("table21")
        self.row2.addButton(self.table21)
        self.gridLayout.addWidget(self.table21, 3, 3, 1, 1)
        self.table32 = QtWidgets.QRadioButton(TransposeAxes)
        self.table32.setObjectName("table32")
        self.row3.addButton(self.table32)
        self.gridLayout.addWidget(self.table32, 4, 4, 1, 1)
        self.table02 = QtWidgets.QRadioButton(TransposeAxes)
        self.table02.setObjectName("table02")
        self.row0.addButton(self.table02)
        self.gridLayout.addWidget(self.table02, 1, 4, 1, 1)
        self.table10 = QtWidgets.QRadioButton(TransposeAxes)
        self.table10.setObjectName("table10")
        self.row1.addButton(self.table10)
        self.gridLayout.addWidget(self.table10, 2, 2, 1, 1)
        self.label_5 = QtWidgets.QLabel(TransposeAxes)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)
        self.table13 = QtWidgets.QRadioButton(TransposeAxes)
        self.table13.setObjectName("table13")
        self.row1.addButton(self.table13)
        self.gridLayout.addWidget(self.table13, 2, 5, 1, 1)
        self.label_3 = QtWidgets.QLabel(TransposeAxes)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(TransposeAxes)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.table23 = QtWidgets.QRadioButton(TransposeAxes)
        self.table23.setObjectName("table23")
        self.row2.addButton(self.table23)
        self.gridLayout.addWidget(self.table23, 3, 5, 1, 1)
        self.line = QtWidgets.QFrame(TransposeAxes)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 0, 1, 5, 1)
        self.table22 = QtWidgets.QRadioButton(TransposeAxes)
        self.table22.setObjectName("table22")
        self.row2.addButton(self.table22)
        self.gridLayout.addWidget(self.table22, 3, 4, 1, 1)
        self.label_6 = QtWidgets.QLabel(TransposeAxes)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 0, 2, 1, 4)
        self.table31 = QtWidgets.QRadioButton(TransposeAxes)
        self.table31.setObjectName("table31")
        self.row3.addButton(self.table31)
        self.gridLayout.addWidget(self.table31, 4, 3, 1, 1)
        self.table03 = QtWidgets.QRadioButton(TransposeAxes)
        self.table03.setObjectName("table03")
        self.row0.addButton(self.table03)
        self.gridLayout.addWidget(self.table03, 1, 5, 1, 1)
        self.label_4 = QtWidgets.QLabel(TransposeAxes)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)
        self.table00 = QtWidgets.QRadioButton(TransposeAxes)
        self.table00.setObjectName("table00")
        self.row0.addButton(self.table00)
        self.gridLayout.addWidget(self.table00, 1, 2, 1, 1)
        self.cancelButton = QtWidgets.QPushButton(TransposeAxes)
        self.cancelButton.setObjectName("cancelButton")
        self.gridLayout.addWidget(self.cancelButton, 5, 3, 1, 3)

        self.retranslateUi(TransposeAxes)
        QtCore.QMetaObject.connectSlotsByName(TransposeAxes)

    def retranslateUi(self, TransposeAxes):
        _translate = QtCore.QCoreApplication.translate
        TransposeAxes.setWindowTitle(_translate("TransposeAxes", "Form"))
        self.table20.setText(_translate("TransposeAxes", "0"))
        self.table11.setText(_translate("TransposeAxes", "1"))
        self.table30.setText(_translate("TransposeAxes", "0"))
        self.table12.setText(_translate("TransposeAxes", "2"))
        self.okButton.setText(_translate("TransposeAxes", "OK"))
        self.label.setText(_translate("TransposeAxes", "0"))
        self.table33.setText(_translate("TransposeAxes", "3"))
        self.table01.setText(_translate("TransposeAxes", "1"))
        self.table21.setText(_translate("TransposeAxes", "1"))
        self.table32.setText(_translate("TransposeAxes", "2"))
        self.table02.setText(_translate("TransposeAxes", "2"))
        self.table10.setText(_translate("TransposeAxes", "0"))
        self.label_5.setText(_translate("TransposeAxes", "Current Dim"))
        self.table13.setText(_translate("TransposeAxes", "3"))
        self.label_3.setText(_translate("TransposeAxes", "2"))
        self.label_2.setText(_translate("TransposeAxes", "1"))
        self.table23.setText(_translate("TransposeAxes", "3"))
        self.table22.setText(_translate("TransposeAxes", "2"))
        self.label_6.setText(_translate("TransposeAxes", "New Dim"))
        self.table31.setText(_translate("TransposeAxes", "1"))
        self.table03.setText(_translate("TransposeAxes", "3"))
        self.label_4.setText(_translate("TransposeAxes", "3"))
        self.table00.setText(_translate("TransposeAxes", "0"))
        self.cancelButton.setText(_translate("TransposeAxes", "Cancel"))

