import os, sys, traceback, copy
import pandas as pd
from PySide2.QtWidgets import *
from PySide2.QtGui import QPixmap, QIcon
from PySide2.QtCore import Qt, QSize
from PySide2.QtCore import Qt, QObject, Signal, Slot, QRunnable, QThreadPool

from .fileBrowser import FileBrowser
from .Gdriver import Gdriver
from .Modules import InfoSheetGenerator
from BespokeAutoSystem.WarningRaiser import WarningRaiser

class InfoTab(QWidget):
    def __init__(self, config):
        QWidget.__init__(self)
        self.threadpool = QThreadPool()

        self.config=config
        self.gdriveAPI = Gdriver()
        self.warn = WarningRaiser()

        # self.layout = QVBoxLayout()
        # init_layout = self.load_init_layout(config)
        # self.layout.addLayout(init_layout)

        # # Init. load
        # self.loadSheetLocal()
        # self.setLayout(self.layout)
        self.reload_all()

    def reload_all(self):
        self.layout = QVBoxLayout()
        init_layout = self.load_init_layout(self.config)
        self.layout.addLayout(init_layout)
        self.loadSheetLocal()
        self.setLayout(self.layout)


    def load_init_layout(self, config):
        # Sheets + edit box layout
        sheets_layout = QGridLayout()
        self.infosheet_browser = FileBrowser("csv", "Information Sheet Paragraphs", config)
        self.infosheet_browser.button.clicked.connect(self.loadSheetLocal)
        self.infosheet_browser.button.clicked.connect(self.reload_all)
        sheets_layout.addWidget(self.infosheet_browser, 0, 0)

        self.instruction_browser = FileBrowser("dir", "Product Instructions Directory", config)
        sheets_layout.addWidget(self.instruction_browser,0, 1)

        return sheets_layout

    def loadSheetLocal(self):
        try:
            # If failed then use local vers
            self.infoSheet_df = pd.read_excel(self.infosheet_browser.display.text())
            self.loadUi(self.infoSheet_df)
        except Exception as e:
            print(e)
            print("Local load failed")

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

        self.layout.addLayout(button_layout, 2)

        # Scroll area for paragraphs
        self.scroll = QScrollArea()
        self.widget = QWidget()
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        self.para_layout = QVBoxLayout()
        self.sections = []
        self.txt_boxes = []
        # Editable paragraphs for info sheet
        for i in range(df.shape[1]):
            heading = list(df)[i]
            body = df.iloc[0,i]
            section_layout = self.create_paragraph_section(heading, body)
            self.para_layout.addLayout(section_layout)

        self.widget.setLayout(self.para_layout)
        self.layout.addWidget(self.scroll)

    def save(self):
        # Update self dataframe
        new_dict = {}

        for label, txt_box in self.txt_boxes:
            #print(label.text())
            try:
                new_dict[label.text()] = [txt_box.toPlainText()]
            except Exception as e:
                print(e)

        self.infoSheet_df = pd.DataFrame.from_dict(new_dict)

        # Local save
        self.infoSheet_df.to_excel(self.infosheet_browser.display.text(), index=False)

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

        section_layout = self.create_paragraph_section(n_heading, n_body)
        self.para_layout.addLayout(section_layout)
        dialog.close()

    def create_paragraph_section(self, n_heading, n_body):
        banner_layout = QGridLayout()

        # Create label
        l = QLabel(n_heading)
        l.setMinimumSize(50, 50)
        banner_layout.addWidget(l, 0, 0)

        # Create text boxes
        if type(n_body) == str and n_body != "AutoFilled by system":
            t = QTextEdit(n_body)
        else:
            t = QTextEdit("AutoFilled by system")
            t.setReadOnly(True)

        t.setMinimumHeight(100)
        self.txt_boxes.append((l, t))

        # Up button
        upButton = self.create_button_icon("/Assets/caret-up.svg")
        banner_layout.addWidget(upButton, 0, 1)
        # Down button
        downButton = self.create_button_icon("/Assets/caret-down.svg")
        banner_layout.addWidget(downButton, 0, 2)
        # Delete button
        del_button = self.create_button_icon("/Assets/trash.svg")
        banner_layout.addWidget(del_button, 0, 3)

        # Package banner label and textbox into one layout
        section_layout = QVBoxLayout()
        section_layout.addLayout(banner_layout)
        section_layout.addWidget(t)

        #self.del_buttons.append(ButtonWrapper(button, l, t, self.layout))
        self.sections.append(SectionWrapper(upButton, downButton, del_button, l, t, section_layout, self.para_layout, self.txt_boxes))
        return section_layout

    def create_button_icon(self, pic_path):
        button = QPushButton()
        # Set icon
        if getattr(sys, 'frozen', False):
            app_path = sys._MEIPASS
        else:
            app_path = os.getcwd()
        icon = QPixmap(app_path + pic_path)
        button.setIcon(QIcon(icon))
        button.setMaximumWidth(30)
        return button

    def save_misc_entry(self, key, text):
        self.config.setMisc(key, text)


    def run(self):
        self.reporter = InfoSheetGenerator.InfoSheetGenerator(self.infoSheet_df, self.gdriveAPI, self.config)
        self.reporter.launched.connect(self.launchProgress)
        self.reporter.stateChanged.connect(self.progStateChanged)
        self.reporter.error.connect(self.showError)
        
        worker = Worker(self.reporter.process_all)
        worker.signals.result.connect(self.processResults)
        self.threadpool.start(worker)

    @Slot()
    def closeProg(self):
        self.prog.cancel()

    @Slot(str)
    def showError(self, errors):
        self.warn.displayWarningDialog("Error", errors)

    @Slot(int)
    def launchProgress(self, end):
        primaryMsg = "Generating PDFs...\n"
        self.prog = QProgressDialog(primaryMsg, "Cancel", 0, end)
        self.prog.canceled.connect(self.reporter.stop_)
        self.prog.setMinimumDuration(3000)
        self.prog.setFixedSize(400, 150)
        self.prog.exec_()

    @Slot(int)
    def progStateChanged(self, i):
        # Set the new value of the progress bar
        self.prog.setValue(i)

    @Slot(object)
    def processResults(self):
        # Start formulation calculations for all orders
        self.closeProg()


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        # fn = function to be run in the thread
        # *args = list of arguments the function uses
        # **kwargs = any signals the function will use. e.g.
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        #self.kwargs['cancel_signal'] = self.signals.cancel

    @Slot()
    def run(self):
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    cancel = Signal()


class SectionWrapper:
    def __init__(self, upButton, downButton, button, l, t, section_layout, para_layout, txt_boxes):
        self.upButton = upButton
        self.downButton = downButton
        self.button = button
        self.l = l
        self.t = t
        self.section_layout = section_layout
        self.para_layout = para_layout

        self.upButton.clicked.connect(lambda: self.move("up"))
        self.downButton.clicked.connect(lambda: self.move("down"))
        self.button.clicked.connect(self.del_section)

        self.txt_boxes = txt_boxes

    def move(self, direction):
        # make a copy of layout
        copy_banner = QGridLayout()
        copy_banner.addWidget(self.l, 0, 0)
        copy_banner.addWidget(self.upButton, 0, 1)
        copy_banner.addWidget(self.downButton, 0, 2)
        copy_banner.addWidget(self.button, 0, 3)

        copy_sec = QVBoxLayout()
        copy_sec.addLayout(copy_banner)
        copy_sec.addWidget(self.t)

        ix = self.para_layout.indexOf(self.section_layout)
        if direction == "down":
            self.para_layout.insertLayout(ix+2, copy_sec)
            loc = self.txt_boxes.index((self.l, self.t))
            self.txt_boxes.insert(loc+1, self.txt_boxes.pop(loc))
        else:
            self.para_layout.insertLayout(ix-1, copy_sec)
            loc = self.txt_boxes.index((self.l, self.t))
            self.txt_boxes.insert(loc-1, self.txt_boxes.pop(loc))

        self.section_layout.deleteLater()
        self.section_layout = copy_sec

    def del_section(self):
        self.upButton.deleteLater()
        self.downButton.deleteLater()
        self.button.deleteLater()
        self.l.deleteLater()
        self.t.deleteLater()
        self.section_layout.deleteLater()