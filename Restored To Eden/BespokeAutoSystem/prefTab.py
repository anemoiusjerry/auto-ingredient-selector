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
            elif key == "Constants":
                continue
            elif key == "Column names":
                self.addTab(ColumnBlade(value, self.config), key)
            elif key == "Values":
                self.addTab(ValuesBlade(value, self.config), key)
            else:
                pass

class ProductBlade(QWidget):

    def __init__(self, product_dict, config):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()  # Main layout

        # Dict is the dict for each product type with all their settings
        for prod_type, prod_dict in product_dict.items():
            self.layout.addWidget(QLabel(prod_type))

            # Get the actual int values for product type constraints
            # [Como, visc, absorp]
            constraint_vals = config.getTarget(prod_type)
            constraint_dict = {
                "comedogenic": constraint_vals[0],
                "absorbency": constraint_vals[2],
                "viscosity": constraint_vals[1]
            }
            # Get range of values for ea. constraint
            constraint_const_dict = {
                "comedogenic": config.getConst("comedogenicRating"),
                "absorbency": config.getConst("absorbency"),
                "viscosity": config.getConst("viscosity")
            }
            
            # Display the constraint values
            for constraint, value in prod_dict.items():
                if constraint == "types":
                    continue
                # Constraint name
                self.layout.addWidget(QLabel(constraint))

                slider_layout = QGridLayout()
                # Create sliders for all 3 constraint options
                slider = QSlider(Qt.Horizontal)
                # number of ticks
                tick_num = len(constraint_const_dict[constraint]) - 1
                slider.setRange(0, tick_num)
                slider.setValue(constraint_dict[constraint])

                # Slider tick settingss
                slider.setTickPosition(QSlider.TicksBelow)
                slider.setTickInterval(1)  # Freq of ticks shown
                slider.setSingleStep(1)    # Step of slider click (does work here)

                # This line trys to line up ticks with tick labels
                slider_layout.addWidget(slider, 0, 0, 1, tick_num)

                # Tick labels
                for i, tick in enumerate(constraint_const_dict[constraint]):
                    tick_label = QLabel(str(tick))
                    # This line trys to line up tick labels with ticks above
                    slider_layout.addWidget(tick_label, 1, i, 1, i+1)

                self.layout.addLayout(slider_layout)
            self.setLayout(self.layout)

class ColumnBlade(QWidget):

    def __init__(self, columns_dict, config):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        for spreadsheet, col_dict in columns_dict.items():
            self.layout.addWidget(QLabel(spreadsheet))

            # Add edit boxes for each column
            for col_name, cur_value in col_dict.items():
                edit_layout = QGridLayout()
                col_name_label = QLabel(col_name)
                edit_box = QLineEdit(str(cur_value))
                # Put label and editable box in same line
                edit_layout.addWidget(col_name_label, 0, 0)
                edit_layout.addWidget(edit_box, 0, 1)

                self.layout.addLayout(edit_layout)
        self.setLayout(self.layout)

class ValuesBlade(QWidget):

    def __init__(self, values_dict, config):
        QWidget.__init__(self)
        self.config = config
        # Define more readable names for settings
        nice_names = {
            "lowBound": "Skin Needs Overlap: Lower Bound",
            "upBound": "Skin Needs Overlap: Upper Bound",
            "maxupBound": "Maximum Skin Needs Overlap bound",
            "tpyeoverlap_low": "Ingredient Type Overlap Lower Bound",
            "typeoverlap_up": "Ingredient Type Ovrelap Upper Bound",
            "maxsols": "Maximum solutions returned",
            "fitweight": "Best constraint fit Weight",
            "numingredweight": "Number of ingredients weight",
            "addedbenefitweight": "Additional benefits weight"
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
        self.save_button.clicked.connect(self.saveSettings)
        self.layout.addWidget(self.save_button)
        self.setLayout(self.layout)

    def saveSettings(self):
        for setting, w_slider in self.sliders:
            self.config.setVal(setting, w_slider.slider.value()/100)
        for setting, spinbox in self.incre_boxes:
            self.config.setVal(setting, spinbox.value())

class sliderWrapper:
    def __init__(self, lowBound, upBound, cur_value, tick_interval):

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(lowBound, upBound)
        self.slider.setValue(cur_value)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(tick_interval)
        self.slider.valueChanged.connect(self.updateVal)
        self.label = QLabel(f"{cur_value}%")

        # Ticklabel
        self.tick_layout = QGridLayout()
        for i in range((upBound-lowBound)//tick_interval + 1):
            tick_label = QLabel(str(lowBound + i*tick_interval))
            self.tick_layout.addWidget(tick_label, 0, i, -1, -1)

    def updateVal(self):
        self.label.setText(f"{self.slider.value()}%")
