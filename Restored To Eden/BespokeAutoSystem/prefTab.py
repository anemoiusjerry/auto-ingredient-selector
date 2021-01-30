from PySide2.QtCore import Qt
from PySide2.QtWidgets import *
from PySide2 import QtCore, QtGui, QtWidgets

class PrefTab(QTabWidget):

    def __init__(self, config, parent=None):
        super(PrefTab, self).__init__(parent)
        self.setTabPosition(QTabWidget.West)
        self.setTabShape
        self.config = config

        # Have individual class for each config rab
        for key, value in config.masterDict.items():
            if key == "Product":
                self.addTab(ProductBlade(value, self.config), key)
            elif key == "Column names":
                self.addTab(ColumnBlade(value, self.config), key)
            elif key == "Values":
                self.addTab(ValuesBlade(value, self.config), key)
            elif key == "Misc":
                self.addTab(MiscBlade(value, self.config), key)
            else:
                pass

class sliderWrapper:
    def __init__(self, lowBound, upBound, cur_value, tick_interval):

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(lowBound, upBound)
        self.slider.setValue(cur_value)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(tick_interval)
        self.slider.setSingleStep(tick_interval)
        self.slider.valueChanged.connect(self.updateVal)

        self.label = QLabel(f"{cur_value}%")

        # Ticklabel
        self.tick_layout = QGridLayout()
        for i in range((upBound-lowBound)//tick_interval + 1):
            tick_label = QLabel(str(lowBound + i*tick_interval))
            self.tick_layout.addWidget(tick_label, 0, i, 1, -1)

    def updateVal(self):
        self.label.setText(f"{self.slider.value()}%")

class ProductBlade(QWidget):

    def __init__(self, product_dict, config):
        QWidget.__init__(self)
        self.config = config
        self.layout = QGridLayout()  # Main layout

        # Get range of values for ea. constraint
        self.constraint_const_dict = {
            "comedogenic": config.getConst("comedogenicRating"),
            "absorbency": config.getConst("absorbency"),
            "viscosity": config.getConst("viscosity")
        }

        # All widgets stored to save to config
        self.wids = {}
        # Dict is the dict for each product type with all their settings
        for i, item in enumerate(product_dict.items()):
            prod_type = item[0]
            prod_dict = item[1]
            self.wids[prod_type] = {}

            # Get the actual int values for product type constraints
            # [Como, visc, absorp]
            constraint_vals = config.getTarget(prod_type)
            constraint_dict = {
                "comedogenic": constraint_vals[0],
                "absorbency": constraint_vals[2],
                "viscosity": constraint_vals[1]
            }
            
            prod_layout = QVBoxLayout()
            # Bold product type label
            header = QtGui.QFont("Avenir", 10, QtGui.QFont.Bold)
            prod_label = QLabel(prod_type.title())
            prod_label.setFont(header)
            prod_layout.addWidget(prod_label)

            # Display the constraint values
            for constraint, value in prod_dict.items():
                if constraint == "types":
                    continue
                slider_layout = QGridLayout()
                # Constraint name
                header2 = QtGui.QFont("Avenir", 8, QtGui.QFont.Bold)
                l = QLabel(constraint.title())
                l.setFont(header2)
                slider_layout.addWidget(l, 0 ,0)

                # Create sliders for all 3 constraint options
                tick_num = len(self.constraint_const_dict[constraint])
                # x10 everything to get slider mouse click working
                sliderObj = sliderWrapper(0, (tick_num-1)*10, constraint_dict[constraint]*10, 10)
                slider_layout.addWidget(sliderObj.slider, 0, 1)

                # Tick labels
                tick_layout = QGridLayout()
                for j, tick in enumerate(self.constraint_const_dict[constraint]):
                    tick_label = QLabel(str(tick))
                    # This line trys to line up tick labels with ticks above
                    tick_layout.addWidget(tick_label, 0, j, 1, -1)
                slider_layout.addLayout(tick_layout, 1, 1)
                
                prod_layout.addLayout(slider_layout)
                # Save slider object
                self.wids[prod_type][constraint] = sliderObj
            
            self.layout.addLayout(prod_layout, i//2, i%2)

        # Save button
        pos = self.layout.rowCount()
        self.save_button = QPushButton("Save")
        self.save_button.setFixedWidth(100)
        self.save_button.clicked.connect(self.saveSettings)
        self.layout.addWidget(self.save_button, pos+1, 0)
        self.setLayout(self.layout)

    def saveSettings(self):
        for prod_type in self.wids.keys():
            for setting, slider in self.wids[prod_type].items():
                int_val = slider.value()/10  # int x10 actual value
                actual_val = self.constraint_const_dict[setting][int_val] # string
                self.config.setProduct(prod_type, setting, self.constraint_const_dict[setting][int_val])

class ColumnBlade(QWidget):

    def __init__(self, columns_dict, config):
        QWidget.__init__(self)
        self.config = config
        self.layout = QGridLayout()
        # Dict to store all line edit widgets
        self.colSettings = {}

        for i, item in enumerate(columns_dict.items()):
            spreadsheet = item[0]
            col_dict = item[1]
            self.colSettings[spreadsheet] = {}

            scroll = QScrollArea()
            widget = QWidget()
            scroll.setWidgetResizable(True)
            scroll.setWidget(widget)

            sheet_layout = QVBoxLayout()
            sheet_layout.addWidget(QLabel(spreadsheet))
            # Add edit boxes for each column
            for col_name, cur_value in col_dict.items():
                col_name_label = QLabel(col_name)
                if type(cur_value) == list:
                    cur_value = ','.join(cur_value)
                edit_box = QLineEdit(cur_value)
                # Put label and editable box in same line
                edit_layout = QVBoxLayout()
                edit_layout.addWidget(col_name_label)
                edit_layout.addWidget(edit_box)

                sheet_layout.addLayout(edit_layout)

                # Save line widget to dict for saving to config
                self.colSettings[spreadsheet][col_name] = edit_box
            
            widget.setLayout(sheet_layout)
            self.layout.addWidget(scroll, i//2, i%2)
            #self.layout.addLayout(sheet_layout, i//2, i%2)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setFixedWidth(100)
        self.save_button.clicked.connect(self.saveSettings)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def saveSettings(self):
        for spreadsheet in self.colSettings.keys():
            for col_name in self.colSettings[spreadsheet].keys():
                wid_value = self.colSettings[spreadsheet][col_name].text()
                # Save necessary cols as list
                wid_value = wid_value.split(',')
                if len(wid_value) == 1:
                    wid_value = wid_value[0]
                self.config.setColname(spreadsheet, col_name, wid_value)


class ValuesBlade(QWidget):

    def __init__(self, values_dict, config):
        QWidget.__init__(self)
        self.config = config
        # Define more readable names for settings
        nice_names = {
            "lowBound": "Skin Needs Overlap: Min",
            "upBound": "Skin Needs Overlap: Max",
            "maxupBound": "Max Skin Needs Overlap",
            "tpyeoverlap_low": "Ingredient Type Overlap: Min",
            "typeoverlap_up": "Ingredient Type Overlap: Max",
            "maxsols": "Max Solutions",
            "fitweight": "Constraint Fit Weight",
            "numingredweight": "Number of Ingredients Weight",
            "addedbenefitweight": "Additional Benefits Weight"
        }
        self.sliders = []
        self.incre_boxes = []
        
        self.layout = QVBoxLayout()
        incre_layout = QGridLayout()  # Layout for all numeric boxes
        weight_layout = QVBoxLayout() # Layout for all weight sliders

        for i, item in enumerate(values_dict.items()):
            setting = item[0]
            value = item[1]

            if setting == "darkmode":
                continue
            # Layout for spinbox/slide + label grouping
            edit_layout = QGridLayout()  
            setting_label = QLabel(nice_names[setting])
            edit_layout.addWidget(setting_label, 0, 0)

            if "weight" in setting:
                w_slider = sliderWrapper(0, 100, int(value*100), 10)
                w_slider.label.setFixedWidth(25)

                edit_layout.addWidget(w_slider.label, 1, 0)
                edit_layout.addWidget(w_slider.slider, 1, 1)
                edit_layout.addLayout(w_slider.tick_layout, 2, 1)

                weight_layout.addLayout(edit_layout)
                self.sliders.append((setting, w_slider))
            else:
                incre_box = QSpinBox()
                incre_box.setFixedWidth(50)
                incre_box.setValue(value)
                edit_layout.addWidget(incre_box, 0, 1)

                incre_layout.addLayout(edit_layout, i//2, i%2)
                self.incre_boxes.append((setting, incre_box))

        self.layout.addLayout(incre_layout)
        self.layout.addLayout(weight_layout)
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setFixedWidth(100)
        self.save_button.clicked.connect(self.saveSettings)
        self.layout.addWidget(self.save_button)
        self.setLayout(self.layout)

    def saveSettings(self):
        for setting, w_slider in self.sliders:
            self.config.setVal(setting, w_slider.slider.value()/100)
        for setting, spinbox in self.incre_boxes:
            self.config.setVal(setting, spinbox.value())

class MiscBlade(QWidget):
    def __init__(self, misc_dict, config):
        QWidget.__init__(self)
        self.config = config
        self.layout = QVBoxLayout()

        self.misc_widgets = {}
        for i, item in enumerate(misc_dict.items()):
            setting = item[0]
            value = item[1]
            
            self.layout.addWidget(QLabel(setting))
            editField = QLineEdit(self.config.getMisc(setting))
            self.misc_widgets[setting] = editField
            self.layout.addWidget(editField)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setFixedWidth(100)
        self.save_button.clicked.connect(self.saveSettings)
        self.layout.addWidget(self.save_button)
        self.setLayout(self.layout)

    def saveSettings(self):
        for setting in self.misc_widgets.keys():
            wid_value = self.misc_widgets[setting].text()
            self.config.setMisc(setting, wid_value)