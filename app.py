import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsScene, QGraphicsPixmapItem, QGraphicsView
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PIL import Image
from PyQt5.QtCore import QFileInfo, QFile
from reportlab.pdfgen import canvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("MainWindow.ui", self)
        self.temp = ""
        self.current_image = None
        self.undo_stack = []
        self.redo_stack = []

        self.buttonOpenImage.clicked.connect(self.open_file_dialog)
        self.actionOPne.triggered.connect(self.open_file_dialog)
        self.spinRotation.valueChanged.connect(self.rotate_image)
        self.sliderDisplayZoom_2.valueChanged.connect(self.rotate_image)
        self.sliderDisplayZoom.valueChanged.connect(self.zoom_image)
        self.buttonRotationAccept.clicked.connect(self.accept_rotation)
        self.buttonRotationDiscard.clicked.connect(self.discard_rotation)
        self.buttonFitWindow.clicked.connect(self.fit_in_window)
        self.buttonOpenImage_2.clicked.connect(self.undo)
        self.buttonOpenImage_3.clicked.connect(self.redo)
        self.actionSave.triggered.connect(self.show_save_dialog)
        self.actionSave_As.triggered.connect(self.save_as_pdf)

        # self.graphicsView = self.findChild(QGraphicsView, "graphicsView")

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        file_info = QFileInfo(file_path)
        file_extension = file_info.suffix()

        if file_path != "" and (file_extension == "jpg" or file_extension == "png"):            
            self.undo_stack = []
            self.redo_stack = []
            self.image = Image.open(file_path)
            self.current_image = self.image  
            self.save_undo_stack(self.current_image)
            self.temp = "temp."+file_extension
            self.show_image(self.current_image)

    def show_save_dialog(self):
        if self.current_image != None:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "JPEG file (*.jpg)", options=options)
        
            if file_name != "":
                file_name = file_name+".jpg"
                self.current_image.convert("RGB").save(file_name, "JPEG")
                file = QFile(self.temp)
                file.remove()

    def save_as_pdf(self):
        if self.current_image != None:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "PDF file (*.pdf)", options=options)

            if file_name != "":
                pdf_file = file_name+".pdf"
                pdf_canvas = canvas.Canvas(pdf_file, pagesize=(self.current_image.size))
                self.current_image.convert("RGB").save("tmp.jpg", "JPEG")
                file = QFile("tmp.jpg")                
                pdf_canvas.drawImage("tmp.jpg", 0, 0)
                pdf_canvas.save()
                file.remove()
                file = QFile(self.temp)
                file.remove()

    def save_undo_stack(self, image):
        self.undo_stack.append(image)
        print("undo_stack = ",self.undo_stack)

    def save_redo_stack(self, image):
        self.redo_stack.append(image)
        print("redo_stack = ",self.redo_stack)

    def undo(self):
        if len(self.undo_stack) == 1:
            self.current_image = self.undo_stack[0]
            self.show_image(self.current_image)
        elif len(self.undo_stack) > 1:
            self.save_redo_stack(self.undo_stack[-1])
            self.undo_stack.pop()
            self.current_image = self.undo_stack[-1]
            self.show_image(self.current_image)
        else: pass
        print("undo_stack = ",self.undo_stack)

    def redo(self):
        if len(self.redo_stack) > 0:
            self.save_undo_stack(self.redo_stack[-1])
            self.current_image = self.redo_stack[-1]
            self.show_image(self.current_image)
            self.redo_stack.pop()
        else: pass
        print("redo_stack = ",self.redo_stack)

    def show_image(self, image):
        image.save(self.temp)
        scene = QGraphicsScene()
        pixmap = QPixmap(self.temp)
        pixmap_item = QGraphicsPixmapItem(pixmap)
        scene.addItem(pixmap_item)
        self.graphicsView.setScene(scene)

    def rotate_image(self, value):
        if self.current_image != None:
            self.rotate_angle = value
            self.rotated_image = self.current_image.rotate(value, expand=True)
            self.show_image(self.rotated_image)

    def accept_rotation(self):  
        if self.current_image != None:      
            self.current_image = self.rotated_image
            self.save_undo_stack(self.current_image)

    def discard_rotation(self):
        if self.current_image != None:
            self.current_image = self.image
            self.save_undo_stack(self.current_image)
            self.show_image(self.current_image)

    def zoom_image(self, value):
        if self.current_image != None:
            width, height = self.current_image.size
            new_width = int(width * value/80)
            new_height = int(height * value/80)
            zoomed_image = self.current_image.resize((new_width, new_height))
            self.show_image(zoomed_image)

    def fit_in_window(self):
        if self.current_image != None:
            view_size = self.graphicsView.size()
            new_width = int(view_size.width())
            new_height = int(view_size.height())
            fitted = self.current_image.resize((new_width, new_height))
            self.current_image = fitted
            self.save_undo_stack(self.current_image)
            self.show_image(self.current_image)    



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    