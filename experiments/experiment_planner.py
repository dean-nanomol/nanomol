# -*- coding: utf-8 -*-
"""
Experiment planner: make a list of measurements and run them one after the other.

The plan is a table of groups. Each group holds one or more actions (measurements), each with its
own settings, and can be repeated a number of times. Groups are run from top to bottom.

The planner does not measure anything itself. Each action type is one of the existing windows
(transistor_transfer, transistor_output, current_vs_time, keithley_2600A_ui, ...). There are two kinds
of actions:
    - measurement actions: the planner copies the settings of the table row into the experiment window,
      starts the measurement, waits until it has finished, and moves on to the next action.
    - settings actions, e.g. instrument settings or the multiplexer: the planner copies the settings
      into the window, which sends them to the instrument as when a user changes its widgets, then
      moves on to the next action.

To make a new window available in the planner, pass it in the experiments dictionary when creating
the planner. Its settings are the widgets named as in interactive_ui (e.g. V_GS_doubleSpinBox), found
automatically. A measurement window must also have:
    - start_measurement(datafile=..., path=...) to start the measurement in a thread and save data
      in the hdf5 group at path
    - stop_measurement()
    - measurement_is_running flag and measurement_thread attribute
Any other window is a settings action. Labels, order and default values of the settings can be adjusted
in settings_hints below.
"""

import inspect
import json
import re
import sys
import threading
import traceback
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QTimer, QRect, QSize, QPoint
from PyQt6.QtGui import QFont

# Optional hints on how to show the settings of each experiment, by experiment class name.
# labels : setting name -> label shown in the table. Settings without a label use their name.
# order : settings shown first, in this order. All other settings follow in the order of the experiment window.
# hidden : settings not shown in the table. They stay as they are set in the experiment window.
# defaults : setting name -> value used for a new action. Settings without a default use the value that
#            the experiment window has when the planner is created.
# settings : function(window) returning the list of settings, instead of finding them from the widget names.
# record_in_measurements : the current settings of this window are saved as attributes of the hdf5 group of
#         every measurement action, named <record_in_measurements>_<setting name>.
keithley_channel_settings = ['V_source_range', 'V_source_limit', 'V_measure_range',
                             'I_source_range', 'I_source_limit', 'I_measure_range', 'nplc']
keithley_labels = {'V_source_range': 'V source range [V]', 'V_source_limit': 'V source limit [V]',
                   'V_measure_range': 'V measure range [V]', 'I_source_range': 'I source range [A]',
                   'I_source_limit': 'I source limit [A]', 'I_measure_range': 'I measure range [A]',
                   'nplc': 'measure nplc'}
settings_hints = {
    'transistor_transfer': {
        'labels': {'V_DS_min_transfer': 'V_DS min [V]',
                   'V_DS_max_transfer': 'V_DS max [V]',
                   'V_DS_step_transfer': 'V_DS step [V]',
                   'V_GS_min_transfer': 'V_GS min [V]',
                   'V_GS_max_transfer': 'V_GS max [V]',
                   'V_GS_step_transfer': 'V_GS step [V]',
                   'first_point_delay': 'delay first point [s]',
                   'delay_points': 'delay points [s]',
                   'delay_curves': 'delay curves [s]',
                   'ch_GS': 'GS channel',
                   'ch_DS': 'DS channel',
                   'N_measurements': 'number of transfers'},
        'order': ['V_DS_min_transfer', 'V_DS_max_transfer', 'V_DS_step_transfer',
                  'V_GS_min_transfer', 'V_GS_max_transfer', 'V_GS_step_transfer',
                  'first_point_delay', 'delay_points', 'delay_curves',
                  'sweep_direction', 'sweep_mode', 'curve_direction', 'curve_mode',
                  'ch_GS', 'ch_DS', 'smu_interaction_mode', 'idle_behaviour', 'live_plotting',
                  'description', 'N_measurements'],
        'hidden': ['save_data'],  # the planner always saves data
        },
    'transistor_output': {
        'labels': {'V_DS_min_output': 'V_DS min [V]',
                   'V_DS_max_output': 'V_DS max [V]',
                   'V_DS_step_output': 'V_DS step [V]',
                   'V_GS_min_output': 'V_GS min [V]',
                   'V_GS_max_output': 'V_GS max [V]',
                   'V_GS_step_output': 'V_GS step [V]',
                   'first_point_delay': 'delay first point [s]',
                   'delay_points': 'delay points [s]',
                   'delay_curves': 'delay curves [s]',
                   'ch_GS': 'GS channel',
                   'ch_DS': 'DS channel',
                   'N_measurements': 'number of outputs'},
        'order': ['V_DS_min_output', 'V_DS_max_output', 'V_DS_step_output',
                  'V_GS_min_output', 'V_GS_max_output', 'V_GS_step_output',
                  'first_point_delay', 'delay_points', 'delay_curves',
                  'sweep_direction', 'sweep_mode', 'curve_direction', 'curve_mode',
                  'ch_GS', 'ch_DS', 'live_plotting',
                  'description', 'N_measurements'],
        'hidden': ['save_data'],
        'defaults': {'live_plotting': True},
        },
    'current_vs_time': {
        'labels': {'V_GS': 'V_GS [V]',
                   'V_DS': 'V_DS [V]',
                   't_limit': 'duration [s]',
                   'ch_GS': 'GS channel',
                   'ch_DS': 'DS channel'},
        'order': ['V_GS', 'V_DS', 't_limit', 'ch_GS', 'ch_DS', 'description'],
        # in the experiment window the default time limit is -1, which runs until stopped manually
        'defaults': {'t_limit': 60.0},
        },
    'keithley_2600A_ui': {
        'labels': {'{}_{}'.format(name, ch): '{}: {}'.format(ch.upper(), label)
                   for name, label in keithley_labels.items() for ch in 'ab'},
        'order': ['{}_{}'.format(name, ch) for ch in 'ab' for name in keithley_channel_settings],
        },
    'arduino_multiplexer_3_to_12_12_1_ui': {
        'settings': lambda window: multiplexer_channel_settings(window),
        'record_in_measurements': 'multiplexer',
        },
    }


class experiment_setting():
    """
    One setting of an experiment, linked to the widget(s) of the experiment window that control it.
    Reads and writes the value in the experiment window, and creates editor widgets for the planner table.

    kind : str
        'float' (QDoubleSpinBox), 'int' (QSpinBox), 'text' (QLineEdit), 'choice' (QComboBox),
        'bool' (QCheckBox), 'option' (group of QRadioButton)
    """

    widget_name_endings = ['doublespinbox', 'spinbox', 'lineedit', 'combobox', 'checkbox', 'radiobutton']

    def __init__(self, name, label, kind, widgets):
        self.name = name
        self.label = label
        self.kind = kind
        self.widgets = widgets  # list of widgets in the experiment window. More than one only for 'option'
        self.default = None  # value for new actions, set in get_experiment_settings()

    @classmethod
    def strip_widget_type(cls, widget_name):
        """ V_GS_doubleSpinBox -> V_GS, as in interactive_ui.connect_widgets_by_name() """
        widget_name_parsed = widget_name.rsplit(sep='_', maxsplit=1)
        if len(widget_name_parsed) == 2 and widget_name_parsed[-1].lower() in cls.widget_name_endings:
            return widget_name_parsed[0]
        return widget_name

    def get_value(self):
        """ read the current value from the experiment window """
        widget = self.widgets[0]
        if self.kind in ['float', 'int']:
            return widget.value()
        elif self.kind == 'text':
            return widget.text()
        elif self.kind == 'choice':
            return widget.currentText()
        elif self.kind == 'bool':
            return widget.isChecked()
        elif self.kind == 'option':
            for radiobutton in self.widgets:
                if radiobutton.isChecked():
                    return self.strip_widget_type(radiobutton.objectName())
            return self.strip_widget_type(self.widgets[0].objectName())

    def set_value(self, value):
        """ write a value to the experiment window, as if the user had changed the widget """
        widget = self.widgets[0]
        if self.kind in ['float', 'int']:
            widget.setValue(value)
        elif self.kind == 'text':
            widget.setText(value)
        elif self.kind == 'choice':
            widget.setCurrentText(value)
        elif self.kind == 'bool':
            widget.setChecked(value)
        elif self.kind == 'option':
            for radiobutton in self.widgets:
                if self.strip_widget_type(radiobutton.objectName()) == value:
                    radiobutton.setChecked(True)
                    # experiments update their attributes when a radiobutton is clicked
                    radiobutton.clicked.emit(True)

    def choices(self):
        """ options of a 'choice' setting, as shown in its drop-down menu """
        widget = self.widgets[0]
        return [widget.itemText(i) for i in range(widget.count())]

    def create_editor(self):
        """
        Returns
        editor : QWidget
            new widget to edit this setting in the planner table, with the same limits and options
            as the widget in the experiment window
        """
        widget = self.widgets[0]
        if self.kind == 'float':
            editor = QtWidgets.QDoubleSpinBox()
            editor.setDecimals(widget.decimals())
            editor.setRange(widget.minimum(), widget.maximum())
            editor.setSingleStep(widget.singleStep())
        elif self.kind == 'int':
            editor = QtWidgets.QSpinBox()
            editor.setRange(widget.minimum(), widget.maximum())
            editor.setSingleStep(widget.singleStep())
        elif self.kind == 'text':
            editor = QtWidgets.QLineEdit()
            editor.setFixedWidth(130)
        elif self.kind == 'choice':
            editor = QtWidgets.QComboBox()
            editor.addItems(self.choices())
        elif self.kind == 'bool':
            editor = QtWidgets.QCheckBox()
        elif self.kind == 'option':
            editor = QtWidgets.QComboBox()
            for radiobutton in self.widgets:
                editor.addItem(radiobutton.text(), self.strip_widget_type(radiobutton.objectName()))
        if self.kind in ['float', 'int', 'choice', 'option']:
            # do not change values by accident when scrolling the table with the mouse wheel
            editor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            editor.wheelEvent = lambda event: event.ignore()
        self.write_editor(editor, self.default)
        return editor

    def read_editor(self, editor):
        if self.kind in ['float', 'int']:
            return editor.value()
        elif self.kind == 'text':
            return editor.text()
        elif self.kind == 'choice':
            return editor.currentText()
        elif self.kind == 'bool':
            return editor.isChecked()
        elif self.kind == 'option':
            return editor.currentData()

    def write_editor(self, editor, value):
        """ returns False if value is not valid for this setting, and leaves the editor unchanged """
        try:
            if self.kind in ['float', 'int']:
                editor.setValue(value)
            elif self.kind == 'text':
                editor.setText(value)
            elif self.kind == 'choice':
                if editor.findText(value) < 0:
                    return False
                editor.setCurrentText(value)
            elif self.kind == 'bool':
                editor.setChecked(bool(value))
            elif self.kind == 'option':
                if editor.findData(value) < 0:
                    return False
                editor.setCurrentIndex(editor.findData(value))
        except TypeError:
            return False
        return True


class checkbox_choice_setting(experiment_setting):
    """
    Group of checkboxes of which one, or none, is checked, shown in the planner as a drop-down menu.
    Used for the channels of the multiplexer, where each checkbox switches one pin.
    Values are the text of the checked checkbox, e.g. 'pin 8', or 'off' if none is checked.
    """

    off = 'off'

    def __init__(self, name, label, checkboxes):
        super().__init__(name, label, 'choice', checkboxes)

    def choices(self):
        return [self.off] + [checkbox.text() for checkbox in self.widgets]

    def get_value(self):
        checked = [checkbox.text() for checkbox in self.widgets if checkbox.isChecked()]
        if len(checked) == 0:
            return self.off
        # more than one only if pins were switched in the window without exclusive mode
        return ', '.join(checked)

    def set_value(self, value):
        """
        Check the checkbox whose text is value, uncheck the others. The checkboxes to uncheck are changed
        first, so that the window switches pins OFF before switching the new pin ON.
        """
        for checkbox in self.widgets:
            if checkbox.text() != value:
                checkbox.setChecked(False)
        for checkbox in self.widgets:
            if checkbox.text() == value:
                checkbox.setChecked(True)


def multiplexer_channel_settings(multiplexer_window):
    """
    One setting for each channel of the multiplexer window, i.e. each group box of pin checkboxes,
    to choose which pin of the channel is ON.

    multiplexer_window : arduino_multiplexer_3_to_12_12_1_ui

    Returns
    settings : list of checkbox_choice_setting
    """
    settings = []
    for groupbox in multiplexer_window.findChildren(QtWidgets.QGroupBox):
        checkboxes = [checkbox for checkbox in groupbox.findChildren(QtWidgets.QCheckBox)
                      if checkbox in multiplexer_window.pin_checkboxes]
        if len(checkboxes) == 0:
            continue
        # sort by pin number
        checkboxes.sort(key=multiplexer_window.pin_checkboxes.index)
        title = groupbox.title().strip()
        settings.append(checkbox_choice_setting(title.replace(' ', '_'), title, checkboxes))
    settings.sort(key=lambda setting: setting.name)
    return settings


def is_measurement_action(experiment):
    """ measurement actions start a measurement, all other actions only change settings """
    return hasattr(experiment, 'start_measurement')


def get_experiment_settings(experiment):
    """
    Find the settings of an experiment from the widgets of its window.

    experiment : QWidget
        experiment window, usually created from a .ui file

    Returns
    settings : list of experiment_setting
    """
    hints = settings_hints.get(type(experiment).__name__, {})
    labels = hints.get('labels', {})
    if 'settings' in hints:
        settings = {setting.name: setting for setting in hints['settings'](experiment)}
    else:
        settings = find_widget_settings(experiment, labels)
    for name, setting in settings.items():
        setting.default = hints.get('defaults', {}).get(name, setting.get_value())
    names = [name for name in hints.get('order', []) if name in settings]
    names += [name for name in settings if name not in names]
    return [settings[name] for name in names if name not in hints.get('hidden', [])]


def find_widget_settings(experiment, labels):
    """
    Find the settings of an experiment from the names of the widgets of its window.

    Returns
    settings : dict
        {setting name: experiment_setting}, in the order of the widgets in the window
    """
    widget_kinds = [(QtWidgets.QDoubleSpinBox, 'float'), (QtWidgets.QSpinBox, 'int'), (QtWidgets.QLineEdit, 'text'),
                    (QtWidgets.QComboBox, 'choice'), (QtWidgets.QCheckBox, 'bool')]
    settings = {}  # setting name : experiment_setting
    radiobutton_groups = {}  # button group or parent widget : experiment_setting
    for widget in experiment.findChildren(QtWidgets.QWidget):
        widget_name = widget.objectName()
        if widget_name == '' or getattr(experiment, widget_name, None) is not widget:
            # only widgets defined in the experiment ui, not e.g. widgets inside plots
            continue
        if isinstance(widget, QtWidgets.QRadioButton):
            # radiobuttons of the same group are one setting
            group = widget.group() if widget.group() is not None else widget.parentWidget()
            if group in radiobutton_groups:
                radiobutton_groups[group].widgets.append(widget)
                continue
            if isinstance(widget.parentWidget(), QtWidgets.QGroupBox):
                name = widget.parentWidget().title().strip().replace(' ', '_')
            else:
                name = experiment_setting.strip_widget_type(widget_name)
            setting = experiment_setting(name, labels.get(name, name.replace('_', ' ')), 'option', [widget])
            radiobutton_groups[group] = setting
            settings[name] = setting
            continue
        for widget_type, kind in widget_kinds:
            if isinstance(widget, widget_type):
                name = experiment_setting.strip_widget_type(widget_name)
                settings[name] = experiment_setting(name, labels.get(name, default_label(name)), kind, [widget])
                break
    return settings


def default_label(name):
    """ first_point_delay -> 'first point delay', V_GS_min -> 'V_GS min' """
    label = name.replace('_', ' ')
    return re.sub(r'\b([VI]) (?=[A-Z])', r'\1_', label)


class flow_layout(QtWidgets.QLayout):
    """
    Layout placing widgets from left to right, continuing on a new line when the width is filled.
    Used for the action settings, so that actions with many settings do not need horizontal scrolling.
    """

    def __init__(self, parent=None, spacing=6):
        super().__init__(parent)
        self.items = []
        self.setSpacing(spacing)
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.arrange_items(QRect(0, 0, width, 0), move_items=False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.arrange_items(rect, move_items=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def arrange_items(self, rect, move_items):
        """ place items line by line within rect, return the total height needed """
        margins = self.contentsMargins()
        x0 = rect.x() + margins.left()
        x_max = rect.right() - margins.right()
        x, y = x0, rect.y() + margins.top()
        line_height = 0
        for item in self.items:
            item_size = item.sizeHint()
            if x + item_size.width() > x_max and line_height > 0:
                # item does not fit, start a new line
                x = x0
                y += line_height + self.spacing()
                line_height = 0
            if move_items:
                item.setGeometry(QRect(QPoint(x, y), item_size))
            x += item_size.width() + self.spacing()
            line_height = max(line_height, item_size.height())
        return y + line_height - rect.y() + margins.bottom()


class action_row(QtWidgets.QFrame):
    """
    One line of the plan: an action (type of measurement) selected from a drop-down menu, and its settings.
    """

    def __init__(self, planner, action=None):
        """
        planner : experiment_planner
        action : dict, optional
            action as returned by get_action(), to create the row with a given action type and settings
        """
        super().__init__()
        self.planner = planner
        self.setObjectName('action_row')
        self.editors = {}  # setting name : (experiment_setting, editor widget)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        # action cell, with drop-down menu and buttons to move, copy and remove the row
        action_cell = QtWidgets.QFrame()
        action_cell.setObjectName('table_cell')
        action_cell.setFixedWidth(experiment_planner.action_column_width)
        action_cell_layout = QtWidgets.QVBoxLayout(action_cell)
        action_cell_layout.setContentsMargins(6, 6, 6, 6)
        action_cell_layout.setSpacing(4)
        self.action_comboBox = QtWidgets.QComboBox()
        self.action_comboBox.addItems(self.planner.experiments.keys())
        self.action_comboBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.action_comboBox.wheelEvent = lambda event: event.ignore()
        action_cell_layout.addWidget(self.action_comboBox)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(2)
        for text, tooltip, function in [('▲', 'move action up', lambda: self.planner.move_action(self, -1)),
                                        ('▼', 'move action down', lambda: self.planner.move_action(self, 1)),
                                        ('copy', 'add a copy of this action below', lambda: self.planner.copy_action(self)),
                                        ('✕', 'remove action', lambda: self.planner.remove_action(self))]:
            button = QtWidgets.QToolButton()
            button.setText(text)
            button.setToolTip(tooltip)
            button.clicked.connect(function)
            buttons_layout.addWidget(button)
        buttons_layout.addStretch()
        action_cell_layout.addLayout(buttons_layout)
        action_cell_layout.addStretch()
        layout.addWidget(action_cell)
        # settings cell, filled with the settings of the selected action
        self.settings_cell = QtWidgets.QFrame()
        self.settings_cell.setObjectName('table_cell')
        self.settings_layout = flow_layout(self.settings_cell, spacing=8)
        self.settings_layout.setContentsMargins(6, 4, 6, 6)
        layout.addWidget(self.settings_cell, stretch=1)
        # settings of action that could not be applied, see set_action()
        self.problems = []
        if action is not None:
            self.problems = self.set_action(action)
        else:
            self.setup_settings()
        self.action_comboBox.currentTextChanged.connect(self.setup_settings)

    def setup_settings(self):
        """ show the settings of the currently selected action, with default values """
        while self.settings_layout.count() > 0:
            setting_widget = self.settings_layout.takeAt(0).widget()
            setting_widget.setParent(None)
            setting_widget.deleteLater()
        self.editors = {}
        label_font = QFont(self.font())
        label_font.setPointSizeF(label_font.pointSizeF() * 0.85)
        # button to copy the settings from the window of the action, with an empty label to align it with the editors
        load_widget = QtWidgets.QWidget()
        load_layout = QtWidgets.QVBoxLayout(load_widget)
        load_layout.setContentsMargins(0, 0, 0, 0)
        load_layout.setSpacing(1)
        load_label = QtWidgets.QLabel(' ')
        load_label.setFont(label_font)
        load_layout.addWidget(load_label)
        self.load_from_window_pushbutton = QtWidgets.QToolButton()
        self.load_from_window_pushbutton.setText('load from window')
        self.load_from_window_pushbutton.setToolTip('copy all settings of this action from its window, as they are now')
        self.load_from_window_pushbutton.clicked.connect(self.load_from_window)
        load_layout.addWidget(self.load_from_window_pushbutton)
        self.settings_layout.addWidget(load_widget)
        for setting in self.planner.experiment_settings[self.action_comboBox.currentText()]:
            editor = setting.create_editor()
            setting_widget = QtWidgets.QWidget()
            setting_layout = QtWidgets.QVBoxLayout(setting_widget)
            setting_layout.setContentsMargins(0, 0, 0, 0)
            setting_layout.setSpacing(1)
            label = QtWidgets.QLabel(setting.label)
            label.setFont(label_font)
            setting_layout.addWidget(label)
            setting_layout.addWidget(editor)
            setting_widget.setToolTip(setting.label)
            self.settings_layout.addWidget(setting_widget)
            self.editors[setting.name] = (setting, editor)

    def load_from_window(self):
        """ copy the current settings of the window of the action into this row """
        action_name = self.action_comboBox.currentText()
        problems = []
        for name, (setting, editor) in self.editors.items():
            value = setting.get_value()
            if not setting.write_editor(editor, value):
                problems.append('{}: value {} of {} cannot be set in the planner'.format(action_name, value, name))
        self.planner.log('loaded settings of {} from its window'.format(action_name))
        for problem in problems:
            self.planner.log('    not loaded: {}'.format(problem))

    def get_action(self):
        """
        Returns
        action : dict
            {'action': name of the action, 'settings': {setting name: value} }
        """
        settings = {name: setting.read_editor(editor) for name, (setting, editor) in self.editors.items()}
        return {'action': self.action_comboBox.currentText(), 'settings': settings}

    def set_action(self, action):
        """
        action : dict
            as returned by get_action(). Settings not included in the dict are left at default values.

        Returns
        problems : list of str
            settings that could not be applied, for example because the experiment no longer has them
        """
        problems = []
        self.action_comboBox.setCurrentText(action['action'])
        self.setup_settings()
        for name, value in action.get('settings', {}).items():
            if name not in self.editors:
                problems.append('{}: unknown setting {}'.format(action['action'], name))
            else:
                setting, editor = self.editors[name]
                if not setting.write_editor(editor, value):
                    problems.append('{}: invalid value {} for {}'.format(action['action'], value, name))
        return problems

    def set_active(self, active):
        """ highlight the row while its measurement is running """
        self.setProperty('active', active)
        for widget in [self] + self.findChildren(QtWidgets.QFrame):
            widget.style().unpolish(widget)
            widget.style().polish(widget)


class action_group(QtWidgets.QFrame):
    """
    Group of actions that are run one after the other, and repeated a number of times.
    """

    def __init__(self, planner):
        super().__init__()
        self.planner = planner
        self.setObjectName('action_group')
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        # group cell, with group number and buttons to move and remove the group
        group_cell = QtWidgets.QFrame()
        group_cell.setObjectName('table_cell')
        group_cell.setFixedWidth(experiment_planner.group_column_width)
        group_cell_layout = QtWidgets.QVBoxLayout(group_cell)
        group_cell_layout.setContentsMargins(6, 6, 6, 6)
        self.number_label = QtWidgets.QLabel()
        number_font = QFont(self.font())
        number_font.setPointSizeF(number_font.pointSizeF() * 1.3)
        self.number_label.setFont(number_font)
        group_cell_layout.addWidget(self.number_label)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(2)
        for text, tooltip, function in [('▲', 'move group up', lambda: self.planner.move_group(self, -1)),
                                        ('▼', 'move group down', lambda: self.planner.move_group(self, 1)),
                                        ('✕', 'remove group', lambda: self.planner.remove_group(self))]:
            button = QtWidgets.QToolButton()
            button.setText(text)
            button.setToolTip(tooltip)
            button.clicked.connect(function)
            buttons_layout.addWidget(button)
        buttons_layout.addStretch()
        group_cell_layout.addLayout(buttons_layout)
        group_cell_layout.addStretch()
        layout.addWidget(group_cell)
        # actions of the group, followed by the button to add an action
        actions_widget = QtWidgets.QWidget()
        actions_layout = QtWidgets.QVBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(2)
        self.rows_layout = QtWidgets.QVBoxLayout()
        self.rows_layout.setSpacing(2)
        actions_layout.addLayout(self.rows_layout)
        add_action_cell = QtWidgets.QFrame()
        add_action_cell.setObjectName('table_cell')
        add_action_layout = QtWidgets.QHBoxLayout(add_action_cell)
        add_action_layout.setContentsMargins(6, 3, 6, 3)
        self.add_action_pushbutton = QtWidgets.QPushButton('+ add action')
        self.add_action_pushbutton.clicked.connect(lambda: self.add_action())
        add_action_layout.addWidget(self.add_action_pushbutton)
        add_action_layout.addStretch()
        actions_layout.addWidget(add_action_cell)
        layout.addWidget(actions_widget, stretch=1)
        # repeat cell. Its width is set by experiment_planner.update_repeat_column_width() from its content
        self.repeat_cell = QtWidgets.QFrame()
        self.repeat_cell.setObjectName('table_cell')
        repeat_cell_layout = QtWidgets.QVBoxLayout(self.repeat_cell)
        repeat_cell_layout.setContentsMargins(6, 6, 6, 6)
        self.repeat_spinBox = QtWidgets.QSpinBox()
        self.repeat_spinBox.setRange(1, 99999)
        self.repeat_spinBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.repeat_spinBox.wheelEvent = lambda event: event.ignore()
        repeat_cell_layout.addWidget(self.repeat_spinBox)
        self.repeat_progress_label = QtWidgets.QLabel()
        repeat_cell_layout.addWidget(self.repeat_progress_label)
        repeat_cell_layout.addStretch()
        layout.addWidget(self.repeat_cell)

    def rows(self):
        return [self.rows_layout.itemAt(i).widget() for i in range(self.rows_layout.count())]

    def add_action(self, action=None, index=None):
        """
        action : dict, optional
            as returned by action_row.get_action(). If None add an action with default settings.
        index : int, optional
            position of the new action within the group. If None add at the end.
        """
        row = action_row(self.planner, action)
        self.rows_layout.insertWidget(self.rows_layout.count() if index is None else index, row)
        return row

    def get_group(self):
        """
        Returns
        group : dict
            {'repeat': number of times the group is run, 'actions': list of actions}
        """
        return {'repeat': self.repeat_spinBox.value(), 'actions': [row.get_action() for row in self.rows()]}


class experiment_planner(QtWidgets.QWidget):
    """
    User interface to plan a sequence of measurements and run them automatically one after the other.

    datafile : hdf5_datafile
        data file where the data of all measurements of a plan is saved
    experiments : dict
        {name: window}. name is shown in the action drop-down menu, window is the object that does the
        measurement, for example transistor_transfer(smu, datafile=datafile), or a settings window, for
        example keithley_2600A_ui(smu).
    instruments : list, optional
        instruments closed by the shut down button, for example [smu, multiplexer]
    """

    group_column_width = 86
    action_column_width = 170
    repeat_cell_margins = 12  # left + right margins of the repeat cell, added to the width of its content

    def __init__(self, datafile, experiments, instruments=None):
        super().__init__()
        self.datafile = datafile
        self.experiments = experiments
        self.instruments = instruments if instruments is not None else []
        self.is_shut_down = False
        self.experiment_settings = {name: get_experiment_settings(experiment)
                                    for name, experiment in experiments.items()}
        self.plan_is_running = False
        self.stop_requested = False
        self.active_row = None
        self.active_experiment = None
        self.measurement_error = None
        # timer to check regularly if the running measurement has finished
        self.measurement_timer = QTimer(self)
        self.measurement_timer.setInterval(100)
        self.measurement_timer.timeout.connect(self.check_measurement)
        self.setup_ui()
        self.add_group()

    def setup_ui(self):
        self.setWindowTitle('experiment planner')
        self.resize(1500, 800)
        self.setStyleSheet("""
            QWidget#plan_table { background-color: white; }
            QFrame#table_cell { background-color: #e6e9ed; }
            QFrame#table_header { background-color: #cdd1d9; }
            QFrame#table_cell[active="true"], QFrame#action_row[active="true"] QFrame#table_cell { background-color: #ffe9a8; }
            QFrame#table_cell QLabel, QFrame#table_header QLabel, QFrame#table_cell QCheckBox { color: #202020; }
            """)
        layout = QtWidgets.QVBoxLayout(self)
        # buttons to run the plan
        controls_layout = QtWidgets.QHBoxLayout()
        self.start_pushbutton = QtWidgets.QPushButton('start plan')
        self.skip_pushbutton = QtWidgets.QPushButton('skip action')
        self.skip_pushbutton.setToolTip('stop the measurement that is running now and continue with the next action')
        self.stop_pushbutton = QtWidgets.QPushButton('stop plan')
        self.stop_pushbutton.setToolTip('stop the measurement that is running now and do not run the rest of the plan')
        self.save_plan_pushbutton = QtWidgets.QPushButton('save plan')
        self.load_plan_pushbutton = QtWidgets.QPushButton('load plan')
        self.start_pushbutton.clicked.connect(self.start_plan)
        self.skip_pushbutton.clicked.connect(self.skip_action)
        self.stop_pushbutton.clicked.connect(self.stop_plan)
        self.save_plan_pushbutton.clicked.connect(self.save_plan)
        self.load_plan_pushbutton.clicked.connect(self.load_plan)
        self.shutdown_pushbutton = QtWidgets.QPushButton('shut down')
        self.shutdown_pushbutton.setToolTip('close the datafile and the connections to the instruments')
        self.shutdown_pushbutton.clicked.connect(self.shutdown)
        for button in [self.start_pushbutton, self.skip_pushbutton, self.stop_pushbutton]:
            controls_layout.addWidget(button)
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setFormat('%v / %m actions')
        self.progressBar.setRange(0, 1)
        self.progressBar.setValue(0)
        controls_layout.addWidget(self.progressBar, stretch=1)
        controls_layout.addWidget(self.save_plan_pushbutton)
        controls_layout.addWidget(self.load_plan_pushbutton)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.shutdown_pushbutton)
        layout.addLayout(controls_layout)
        self.status_label = QtWidgets.QLabel('plan not running')
        layout.addWidget(self.status_label)
        # table header
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(2)
        for text, width in [('group', self.group_column_width), ('action', self.action_column_width),
                            ('action settings', None), ('repeat group # times', 'content')]:
            header_cell = QtWidgets.QFrame()
            header_cell.setObjectName('table_header')
            header_cell_layout = QtWidgets.QHBoxLayout(header_cell)
            header_cell_layout.setContentsMargins(6, 6, 6, 6)
            header_label = QtWidgets.QLabel(text)
            header_cell_layout.addWidget(header_label)
            if width is None:
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                header_layout.addWidget(header_cell, stretch=1)
            elif width == 'content':
                # repeat column: as narrow as its content, the header text wraps onto several lines
                header_label.setWordWrap(True)
                self.repeat_header_cell, self.repeat_header_label = header_cell, header_label
                header_layout.addWidget(header_cell)
            else:
                header_cell.setFixedWidth(width)
                header_layout.addWidget(header_cell)
        # table of groups, in a scroll area so the plan can be arbitrarily long
        self.table_widget = QtWidgets.QWidget()
        self.table_widget.setObjectName('plan_table')
        table_layout = QtWidgets.QVBoxLayout(self.table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(2)
        self.groups_layout = QtWidgets.QVBoxLayout()
        self.groups_layout.setSpacing(2)
        table_layout.addLayout(self.groups_layout)
        add_group_cell = QtWidgets.QFrame()
        add_group_cell.setObjectName('table_header')
        add_group_layout = QtWidgets.QHBoxLayout(add_group_cell)
        add_group_layout.setContentsMargins(6, 6, 6, 6)
        self.add_group_pushbutton = QtWidgets.QPushButton('+ add group')
        self.add_group_pushbutton.clicked.connect(lambda: self.add_group())
        add_group_layout.addWidget(self.add_group_pushbutton)
        add_group_layout.addStretch()
        table_layout.addWidget(add_group_cell)
        table_layout.addStretch(1)
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea.setWidget(self.table_widget)
        # keep header aligned with the table columns, which are narrower by the width of the scroll bar
        header_layout.addSpacing(self.scrollArea.verticalScrollBar().sizeHint().width())
        layout.addLayout(header_layout)
        layout.addWidget(self.scrollArea, stretch=1)
        # log of what the planner has done
        self.log_plainTextEdit = QtWidgets.QPlainTextEdit()
        self.log_plainTextEdit.setReadOnly(True)
        self.log_plainTextEdit.setMaximumBlockCount(5000)
        self.log_plainTextEdit.setFixedHeight(120)
        layout.addWidget(self.log_plainTextEdit)
        self.set_plan_controls()

    # ---- editing the plan

    def groups(self):
        return [self.groups_layout.itemAt(i).widget() for i in range(self.groups_layout.count())]

    def add_group(self, group=None):
        """
        group : dict, optional
            as returned by action_group.get_group(). If None add a group with one action with default settings.

        Returns
        problems : list of str
            actions and settings of group that could not be applied
        """
        problems = []
        new_group = action_group(self)
        if group is None:
            new_group.add_action()
        else:
            try:
                new_group.repeat_spinBox.setValue(group.get('repeat', 1))
            except TypeError:
                problems.append('invalid number of repeats {}'.format(group.get('repeat')))
            for action in group.get('actions', []):
                if action.get('action') not in self.experiments:
                    problems.append('unknown action {}'.format(action.get('action')))
                else:
                    row = new_group.add_action(action)
                    problems.extend(row.problems)
        self.groups_layout.addWidget(new_group)
        self.update_group_numbers()
        self.update_repeat_column_width()
        return problems

    def remove_group(self, group):
        self.groups_layout.removeWidget(group)
        group.setParent(None)
        group.deleteLater()
        self.update_group_numbers()

    def move_group(self, group, step):
        """ step : int, -1 to move the group up, +1 to move it down """
        index = self.groups_layout.indexOf(group)
        new_index = index + step
        if 0 <= new_index < self.groups_layout.count():
            self.groups_layout.removeWidget(group)
            self.groups_layout.insertWidget(new_index, group)
            self.update_group_numbers()

    def update_repeat_column_width(self):
        """
        Make the repeat column as wide as its content needs: the repeat spin boxes, the progress labels,
        and the longest word of the header, which wraps onto several lines. All cells of the column, in
        the header and in every group, get the same width so that the column stays aligned.
        """
        font_metrics = self.repeat_header_label.fontMetrics()
        widths = [font_metrics.horizontalAdvance(word) for word in self.repeat_header_label.text().split()]
        for group in self.groups():
            widths.append(group.repeat_spinBox.sizeHint().width())
            widths.append(group.repeat_progress_label.sizeHint().width())
        width = max(widths) + self.repeat_cell_margins
        self.repeat_header_cell.setFixedWidth(width)
        for group in self.groups():
            group.repeat_cell.setFixedWidth(width)

    def update_group_numbers(self):
        for i, group in enumerate(self.groups()):
            group.number_label.setText(str(i + 1))

    def group_of_action(self, row):
        for group in self.groups():
            if row in group.rows():
                return group

    def remove_action(self, row):
        group = self.group_of_action(row)
        group.rows_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()

    def copy_action(self, row):
        group = self.group_of_action(row)
        group.add_action(row.get_action(), index=group.rows_layout.indexOf(row) + 1)

    def move_action(self, row, step):
        """
        Move an action up or down. At the top or bottom of its group the action moves to the neighbouring group.

        step : int, -1 to move the action up, +1 to move it down
        """
        groups = self.groups()
        group = self.group_of_action(row)
        index = group.rows_layout.indexOf(row)
        new_index = index + step
        if 0 <= new_index < group.rows_layout.count():
            group.rows_layout.removeWidget(row)
            group.rows_layout.insertWidget(new_index, row)
        else:
            new_group_index = groups.index(group) + step
            if 0 <= new_group_index < len(groups):
                new_group = groups[new_group_index]
                group.rows_layout.removeWidget(row)
                new_group.rows_layout.insertWidget(new_group.rows_layout.count() if step < 0 else 0, row)

    def get_plan(self):
        """
        Returns
        plan : dict
            {'groups': [ {'repeat': N, 'actions': [ {'action': name, 'settings': {name: value} }, ...] }, ...] }
        """
        return {'groups': [group.get_group() for group in self.groups()]}

    def set_plan(self, plan):
        """
        Replace the plan in the table.

        plan : dict
            as returned by get_plan()

        Returns
        problems : list of str
            actions and settings of plan that could not be applied
        """
        for group in self.groups():
            self.remove_group(group)
        problems = []
        for group in plan.get('groups', []):
            problems.extend(self.add_group(group))
        return problems

    def save_plan(self):
        """ save the plan to a text file in json format """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'save plan', 'experiment_plan.json', 'plan (*.json)')
        if filename != '':
            with open(filename, 'w', encoding='utf-8') as plan_file:
                json.dump(self.get_plan(), plan_file, indent=2, ensure_ascii=False)
            self.log('plan saved to {}'.format(filename))

    def load_plan(self):
        """ replace the plan in the table with one saved with save_plan() """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'load plan', '', 'plan (*.json)')
        if filename != '':
            try:
                with open(filename, 'r', encoding='utf-8') as plan_file:
                    plan = json.load(plan_file)
                if not isinstance(plan, dict) or not isinstance(plan.get('groups'), list):
                    raise ValueError('file does not contain a plan')
            except (OSError, ValueError) as exception:
                self.log('could not load plan from {}: {}'.format(filename, exception))
                return
            problems = self.set_plan(plan)
            self.log('plan loaded from {}'.format(filename))
            for problem in problems:
                self.log('    not loaded: {}'.format(problem))

    # ---- running the plan

    def start_plan(self):
        if self.plan_is_running:
            return
        for name, experiment in self.experiments.items():
            if getattr(experiment, 'measurement_is_running', False):
                self.log('cannot start plan: a {} measurement is already running'.format(name))
                return
        # list all actions to run, in order
        self.steps = []
        for group_index, group in enumerate(self.groups()):
            N_repeats = group.repeat_spinBox.value()
            for repeat_index in range(N_repeats):
                for action_index, row in enumerate(group.rows()):
                    self.steps.append({'group': group, 'group_index': group_index,
                                       'repeat_index': repeat_index, 'N_repeats': N_repeats,
                                       'row': row, 'action_index': action_index})
        if len(self.steps) == 0:
            self.log('cannot start plan: no actions in the plan')
            return
        if not self.datafile:
            self.log('cannot start plan: the datafile is closed')
            return
        # each run of a plan is saved in its own group of the datafile, together with the plan itself
        plan_group_name = self.datafile.get_unique_group_name(self.datafile, basename='plan')
        self.plan_group = self.datafile.create_group(plan_group_name)
        self.plan_group.attrs.create('timestamp', self.datafile.timestamp())
        self.plan_group.attrs.create('plan', json.dumps(self.get_plan(), ensure_ascii=False))
        self.datafile.flush()
        self.plan_is_running = True
        self.stop_requested = False
        self.measurement_error = None
        # catch errors in the measurement threads, otherwise the planner would wait forever
        self.threading_excepthook = threading.excepthook
        threading.excepthook = self.measurement_thread_error
        self.step_index = -1
        self.progressBar.setRange(0, len(self.steps))
        self.progressBar.setValue(0)
        for group in self.groups():
            group.repeat_progress_label.setText('')
        self.update_repeat_column_width()
        self.set_plan_controls()
        self.log('plan started, {} actions, saving in {}'.format(len(self.steps), self.plan_group.name))
        self.start_next_action()

    def start_next_action(self):
        self.step_index += 1
        if self.step_index >= len(self.steps):
            self.finish_plan('plan completed')
            return
        step = self.steps[self.step_index]
        action = step['row'].get_action()
        action_name = action['action']
        experiment = self.experiments[action_name]
        # show what is running
        self.active_row = step['row']
        self.active_row.set_active(True)
        self.scrollArea.ensureWidgetVisible(self.active_row, 0, 40)
        step['group'].repeat_progress_label.setText('{} of {}'.format(step['repeat_index'] + 1, step['N_repeats']))
        self.update_repeat_column_width()
        description = 'group {}, repeat {} of {}, action {}: {}'.format(step['group_index'] + 1, step['repeat_index'] + 1,
                                                                       step['N_repeats'], step['action_index'] + 1, action_name)
        self.status_label.setText('running {}'.format(description))
        self.log('started {}'.format(description))
        self.active_experiment = experiment
        try:
            action_data_group = self.create_action_data_group(step, action)
            if is_measurement_action(experiment):
                # copy settings of the table row to the experiment window
                for setting in self.experiment_settings[action_name]:
                    setting.set_value(action['settings'][setting.name])
                self.save_recorded_settings(action_data_group)
                if 'path' in inspect.signature(experiment.start_measurement).parameters:
                    experiment.start_measurement(datafile=self.datafile, path=action_data_group.name)
                else:
                    # experiment cannot be told where to save, it saves where it does when started from its own window
                    experiment.start_measurement()
            else:
                self.apply_settings_action(action_name, action['settings'])
        except Exception:
            self.measurement_error = traceback.format_exc()
        # check_measurement() continues with the next action when this one has finished
        self.measurement_timer.start()

    def create_action_data_group(self, step, action):
        """
        Create the hdf5 group of an action, where a measurement saves its data, with the settings of the
        action as attributes.

        step : dict
            step of the plan, see start_plan()
        action : dict
            as returned by action_row.get_action()

        Returns
        action_data_group : h5py group
        """
        repeat_group_name = 'group_{}_repeat_{:0{}d}'.format(step['group_index'] + 1, step['repeat_index'],
                                                            max(3, len(str(step['N_repeats'] - 1))))
        repeat_group = self.plan_group.require_group(repeat_group_name)
        action_group_name = 'action_{}_{}'.format(step['action_index'] + 1, action['action'].replace(' ', '_'))
        action_data_group = repeat_group.create_group(action_group_name)
        action_data_group.attrs.create('timestamp', self.datafile.timestamp())
        action_data_group.attrs.create('action', action['action'])
        for name, value in action['settings'].items():
            action_data_group.attrs.create(name, value)
        self.datafile.flush()
        return action_data_group

    def save_recorded_settings(self, action_data_group):
        """
        Save the current settings of the windows marked record_in_measurements in settings_hints, e.g. the
        multiplexer channels, as attributes <record_in_measurements>_<setting name> of the group of a measurement.
        """
        for name, experiment in self.experiments.items():
            prefix = settings_hints.get(type(experiment).__name__, {}).get('record_in_measurements')
            if prefix is not None:
                for setting in self.experiment_settings[name]:
                    action_data_group.attrs.create('{}_{}'.format(prefix, setting.name), setting.get_value())
        self.datafile.flush()

    def apply_settings_action(self, action_name, settings):
        """
        Copy the settings of a settings action to its window. The window sends them to the instrument, as
        when a user changes its widgets. Errors raised while doing so stop the plan.

        action_name : str
        settings : dict
            {setting name: value}
        """
        # errors raised in the slots of the window do not reach this code: PyQt passes them to sys.excepthook,
        # and aborts the program if that is Python's default one. Collect them instead, and stop at the first.
        slot_errors = []
        previous_excepthook = sys.excepthook
        sys.excepthook = lambda error_type, error, error_traceback: slot_errors.append(
            ''.join(traceback.format_exception(error_type, error, error_traceback)))
        try:
            for setting in self.experiment_settings[action_name]:
                setting.set_value(settings[setting.name])
                if len(slot_errors) > 0:
                    break
        finally:
            sys.excepthook = previous_excepthook
        if len(slot_errors) > 0:
            raise RuntimeError('error in the {} window while setting {}:\n{}'.format(
                action_name, setting.name, '\n'.join(slot_errors)))

    def check_measurement(self):
        """ called regularly by measurement_timer while a measurement is running """
        experiment = self.active_experiment
        measurement_thread = getattr(experiment, 'measurement_thread', None)
        if self.measurement_error is None and is_measurement_action(experiment):
            if measurement_thread is not None and measurement_thread.is_alive():
                return
            if measurement_thread is None and experiment.measurement_is_running:
                return
        # action has finished. Settings actions finish as soon as their settings are sent
        self.measurement_timer.stop()
        self.active_row.set_active(False)
        if self.measurement_error is not None or getattr(experiment, 'measurement_is_running', False):
            # the action ended with an error, do not continue as the state of the instruments is not known.
            # measurement_is_running is left as the experiment set it: each experiment resets it when it has
            # turned off its outputs, so if it is still True the experiment did not end correctly
            if self.measurement_error is None:
                self.measurement_error = 'the measurement ended without resetting measurement_is_running'
            self.log('ERROR in the measurement:\n{}'.format(self.measurement_error))
            self.finish_plan('plan stopped by an error at action {} of {}. Check that instrument outputs are off.'.format(
                self.step_index + 1, len(self.steps)))
            return
        self.progressBar.setValue(self.step_index + 1)
        if self.stop_requested:
            self.finish_plan('plan stopped at action {} of {}'.format(self.step_index + 1, len(self.steps)))
        else:
            self.start_next_action()

    def measurement_thread_error(self, args):
        """ replaces threading.excepthook while a plan is running """
        self.measurement_error = ''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
        self.threading_excepthook(args)

    def finish_plan(self, message):
        threading.excepthook = self.threading_excepthook
        self.plan_is_running = False
        self.active_row = None
        self.active_experiment = None
        self.datafile.flush()
        self.status_label.setText(message)
        self.log(message)
        self.set_plan_controls()

    def skip_action(self):
        """ stop the measurement that is running, the plan continues with the next action """
        if self.plan_is_running and is_measurement_action(self.active_experiment):
            self.log('skipping action')
            self.status_label.setText('skipping action, waiting for the measurement to stop')
            self.active_experiment.stop_measurement()

    def stop_plan(self):
        """ stop the measurement that is running and do not run the remaining actions """
        if self.plan_is_running and self.active_experiment is not None:
            self.stop_requested = True
            self.status_label.setText('stopping plan, waiting for the measurement to stop')
            if is_measurement_action(self.active_experiment):
                self.active_experiment.stop_measurement()

    def set_plan_controls(self):
        """
        The plan cannot be edited, and measurements cannot be started from their own windows, while a plan
        is running. After shut down only the plan can be saved.
        """
        can_edit = not self.plan_is_running and not self.is_shut_down
        self.start_pushbutton.setEnabled(can_edit)
        self.skip_pushbutton.setEnabled(self.plan_is_running)
        self.stop_pushbutton.setEnabled(self.plan_is_running)
        self.load_plan_pushbutton.setEnabled(can_edit)
        self.shutdown_pushbutton.setEnabled(can_edit)
        self.table_widget.setEnabled(can_edit)
        for experiment in self.experiments.values():
            if hasattr(experiment, 'start_pushbutton'):
                experiment.start_pushbutton.setEnabled(can_edit)

    def running_measurements(self):
        """ names of the measurement actions whose measurement is running, also if started from their own window """
        running = []
        for name, experiment in self.experiments.items():
            measurement_thread = getattr(experiment, 'measurement_thread', None)
            if getattr(experiment, 'measurement_is_running', False) or (
                    measurement_thread is not None and measurement_thread.is_alive()):
                running.append(name)
        return running

    def shutdown(self):
        """
        Close the datafile and the connections to the instruments, at the end of the experiments.
        Not possible while a plan or a measurement is running, as its outputs could then not be turned off.
        Afterwards the windows of all actions are disabled, as their instruments can no longer be used.
        """
        if self.is_shut_down:
            return
        if self.plan_is_running:
            self.log('cannot shut down while a plan is running, stop the plan first')
            return
        running = self.running_measurements()
        if len(running) > 0:
            self.log('cannot shut down while a measurement is running: {}'.format(', '.join(running)))
            return
        reply = QtWidgets.QMessageBox.question(self, 'experiment planner',
                                               'Close the datafile and the connections to the instruments?\n'
                                               'Measurements cannot be started again until the program is restarted.')
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.is_shut_down = True
        items_to_close = [('datafile {}'.format(self.datafile.filename), self.datafile)]
        items_to_close += [(type(instrument).__name__, instrument) for instrument in self.instruments]
        for name, item in items_to_close:
            try:
                item.close()
                self.log('closed {}'.format(name))
            except Exception as exception:
                self.log('could not close {}: {}'.format(name, exception))
        for experiment in self.experiments.values():
            experiment.setEnabled(False)
        self.status_label.setText('shut down: datafile and instruments closed')
        self.set_plan_controls()

    def log(self, message):
        self.log_plainTextEdit.appendPlainText('{}  {}'.format(self.datafile.timestamp(), message))

    def closeEvent(self, event):
        if self.plan_is_running:
            reply = QtWidgets.QMessageBox.question(self, 'experiment planner',
                                                   'A plan is running. Stop the plan and close the planner?')
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.stop_plan()
        event.accept()


if __name__ == '__main__' :

    from nanomol.instruments.keithley_2600A import keithley_2600A, keithley_2600A_ui
    from nanomol.instruments.arduino_multiplexer_3_to_12_12_1 import arduino_multiplexer_3_to_12_12_1, arduino_multiplexer_3_to_12_12_1_ui
    from nanomol.utils.hdf5_datafile import hdf5_datafile
    from nanomol.utils.hdf5_viewer import hdf5_viewer
    from nanomol.experiments.transistor_transfer import transistor_transfer
    from nanomol.experiments.transistor_output import transistor_output
    from nanomol.experiments.current_vs_time import current_vs_time

    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('USB0::0x05E6::0x2612::4651966::INSTR')
    multiplexer = arduino_multiplexer_3_to_12_12_1('COM10')

    experiment_app = QtWidgets.QApplication([])

    # actions available in the planner: measurements, and settings of the smu and of the multiplexer
    experiments = {'transfer': transistor_transfer(smu, datafile=datafile),
                   'output': transistor_output(smu, datafile=datafile),
                   'current vs time': current_vs_time(datafile, smu),
                   'keithley settings': keithley_2600A_ui(smu),
                   'multiplexer set active pins': arduino_multiplexer_3_to_12_12_1_ui(multiplexer) }

    # instruments are closed by the shut down button of the planner
    planner = experiment_planner(datafile, experiments, instruments=[smu, multiplexer])
    datafile_viewer = hdf5_viewer(datafile)

    datafile_viewer.show()
    for experiment in experiments.values():
        experiment.show()
    planner.show()

    experiment_app.exec()
