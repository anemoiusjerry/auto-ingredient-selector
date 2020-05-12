import sys
from PySide2.QtWidgets import QApplication
from main_cosmetic_window import MainWindow
from browser import Browser

if __name__ == "__main__":

    app = QApplication(sys.argv)

    supportedFormats =    {'*.3fr','*.ari','*.arw','*.srf', '*.sr2','*.bay','*.cri','*.crw', '*.cr2',     '*.cr3', '*.cap','*.iiq','*.eip',\
                           '*.dcs','*.dcr','*.drf','*.k25', '*.kdc','*.dng','*.erf','*.fff', '*.mef',     '*.mdc', '*.mos','*.mrw','*.nef',\
                           '*.nrw','*.orf','*.pef','*.ptx', '*.pxn','*.r3d','*.raf','*.raw', '*.rw2',     '*.rwl', '*.rwz','*.srw','*.x3f',\
                           '*.3FR','*.ARI','*.ARW','*.SRF', '*.SR2','*.BAY','*.CRI','*.CRW', '*.CR2',     '*.CR3', '*.CAP','*.IIQ','*.EIP',\
                           '*.DCS','*.DCR','*.DRF','*.K25', '*.KDC','*.DNG','*.ERF','*.FFF', '*.MEF',     '*.MDC', '*.MOS','*.MRW','*.NEF',\
                           '*.NRW','*.ORF','*.PEF','*.PTX', '*.PXN','*.R3D','*.RAF','*.RAW', '*.RW2',     '*.RWL', '*.RWZ','*.SRW','*.X3F',\
                           '*.bmp','*.eps','*.gif','*.icns','*.ico','*.im', '*.jpg','*.jpeg','*.jpeg2000','*.msp', '*.pcx','*.png','*.ppm',\
                           '*.sgi','*.tiff','*.tif','*.xbm','*.BMP','*.EPS','*.GIF','*.ICNS','*.ICO',     '*.IM',  '*.JPG','*.JPEG','*.JPEG2000',\
                           '*.MSP','*.PCX','*.PNG','*.PPM','*.SGI','*.TIFF','*.TIF','*.XBM'}

    widget = Browser(supportedFormats)
    window = MainWindow(widget)
    window.show()


    sys.exit(app.exec_())
