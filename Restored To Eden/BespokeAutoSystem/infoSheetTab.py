from PySide2.QtWidgets import *
import pandas as pd

from .fileBrowser import FileBrowser
from .Gdriver import Gdriver
from .Modules import InfoSheetGenerator

class InfoTab(QWidget):

    def __init__(self, config):
        QWidget.__init__(self)
        self.layout = QGridLayout()
        self.gdriveAPI = Gdriver()

        self.infosheet_browser = FileBrowser("csv", "Information Sheet Paragraphs", config)
        self.infosheet_browser.button.clicked.connect(self.loadSheetLocal)
        self.layout.addWidget(self.infosheet_browser)
        # Init. load
        self.loadSheetCloud()
        self.setLayout(self.layout)
    
    def run(self):
        reporter = InfoSheetGenerator.InfoSheetGenerator(self.infoSheet_df, self.gdriveAPI)
        reporter.process_all()

    def loadSheetLocal(self):
        # If failed then use local vers
        self.infoSheet_df = pd.read_excel(self.infosheet_browser.display.text())
        self.loadUi(self.infoSheet_df)
        # try:
            
        # except:
        #     print("Local load failed")
    def loadSheetCloud(self):
        try:
            # Query Gdrive for info sheet
            fh, file_id = self.gdriveAPI.fetch_file("InformationSheet")
            self.infoSheet_id = file_id
            self.infoSheet_df = pd.read_excel(fh)
            self.loadUi(self.infoSheet_df)
        except:
            print("Could Load from GDrive, trying load locally...")
            self.loadSheetLocal()


    def loadUi(self, df):

        button_layout = QGridLayout()
        # Run button
        run_button = QPushButton("Run")
        run_button.clicked.connect(self.run)
        button_layout.addWidget(run_button, 0, 0)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        button_layout.addWidget(save_button, 0, 1)

        # Add new section button
        add_button = QPushButton("Add section")
        add_button.clicked.connect(self.add_section)
        button_layout.addWidget(add_button, 0, 2)

        self.layout.addLayout(button_layout, 1, 0)

        self.del_buttons = []
        self.txt_boxes = []
        for i in range(df.shape[1]):
            # Create label
            #l = QLabel(list(df)[i])
            l = QLineEdit(list(df)[i])
            self.layout.addWidget(l, 2*i+2, 0)

            # Create text boxes
            t = QTextEdit(df.iloc[0,i])
            t.setMinimumSize(50, 50)
            self.layout.addWidget(t, 2*i+3, 0)
            self.txt_boxes.append((l, t))

            # Delete button
            button = QPushButton("Del")
            self.del_buttons.append(ButtonWrapper(button, l, t))
            self.layout.addWidget(button, 2*i+3, 1)

    def save(self):
        # Update self dataframe
        new_dict = {}
        for label, txt_box in self.txt_boxes:
            new_dict[label.text()] = [txt_box.toPlainText()]

        self.infoSheet_df = pd.DataFrame.from_dict(new_dict)

        # Local save
        self.infoSheet_df.to_excel(self.infosheet_browser.display.text(), index=False)
        
        # GDrive save
        if self.infoSheet_id != None:
            self.gdriveAPI.push_file("InformationSheet.xlsx", 
                                     self.infosheet_browser.display.text(),
                                     fileId=self.infoSheet_id)

    def add_section(self):
        dialog = QDialog()
        dialog.setWindowTitle("New Section")
        layout = QVBoxLayout()

        # New section heading
        l = QLabel("Section Title")
        layout.addWidget(l)
        e = QLineEdit()
        layout.addWidget(e)

        # New section content
        l_content = QLabel("Section Content")
        layout.addWidget(l_content)
        e_content = QTextEdit()
        layout.addWidget(e_content)

        # Button adds new info to SQLite
        button = QPushButton("Ok!")
        button.clicked.connect(lambda: self.add_N_close(dialog, e.text(), e_content.toPlainText()))
        layout.addWidget(button)

        dialog.setLayout(layout)
        dialog.exec_() 

    def add_N_close(self, dialog, n_heading, n_body):
        new_section_df = pd.DataFrame({n_heading: [n_body]})
        self.infoSheet_df = pd.concat([self.infoSheet_df, new_section_df], axis=1)
        
        l = QLineEdit(n_heading)
        t = QTextEdit(n_body)
        self.txt_boxes.append((l, t))
        
        # Insert at end of UI
        pos = self.layout.rowCount()
        self.layout.addWidget(l, pos, 0)
        self.layout.addWidget(t, pos+1, 0)

         # Delete button
        button = QPushButton("Del")
        self.del_buttons.append(ButtonWrapper(button, l, t))
        self.layout.addWidget(button, pos+1, 1)

        dialog.close()

class ButtonWrapper:
    def __init__(self, button, label, text_box):
        self.df = None
        self.button = button
        self.label = label
        self.text_box = text_box
        
        self.button.clicked.connect(self.del_section)
        
    def del_section(self):
        df = pd.DataFrame({self.label.text(): [self.text_box.toPlainText()]})
        self.label.deleteLater()
        self.text_box.deleteLater()
        self.button.deleteLater()
        
        self.df = df