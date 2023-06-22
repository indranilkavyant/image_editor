import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QGraphicsScene, QGraphicsPixmapItem, QGraphicsView
from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PIL import Image, ImageDraw
from PyQt5.QtCore import QFileInfo, QFile, Qt, QPoint
from reportlab.pdfgen import canvas
from functools import partial

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        uic.loadUi("MainWindow.ui", self)
        self.temp = ""
        self.current_image = None
        self.undo_stack = []
        self.redo_stack = []
        self.shape = None
        self.freehand_temp = None
        self.crop_flag = None
        self.undo_count = 3

        self.buttonOpenImage.clicked.connect(self.open_file_dialog)
        self.actionOPne.triggered.connect(self.open_file_dialog)
        self.spinRotation.valueChanged.connect(self.rotate_image)
        self.sliderDisplayZoom_2.valueChanged.connect(self.rotate_image)
        self.sliderDisplayZoom.valueChanged.connect(self.zoom_image)
        self.buttonRotationAccept.clicked.connect(self.accept_rotation)
        self.buttonRotationDiscard.clicked.connect(self.undo)
        self.buttonFitWindow.clicked.connect(self.fit_in_window)
        self.buttonOpenImage_2.clicked.connect(self.undo)
        self.buttonOpenImage_3.clicked.connect(self.redo)
        self.actionSave.triggered.connect(self.show_save_dialog)
        self.actionSave_As.triggered.connect(self.save_as_pdf)
        self.radioROInone.toggled.connect(partial(self.select_shape, "no_roi"))
        self.radioROIrectangle.toggled.connect(partial(self.select_shape, "rectangle"))
        self.radioROIcircle.toggled.connect(partial(self.select_shape, "circle"))
        self.radioROIfreehand.toggled.connect(partial(self.select_shape, "freehand"))
        self.buttonROIAdd.clicked.connect(self.add_roi)
        self.buttonROIExclude.clicked.connect(self.undo)
        self.buttonROIDiscard.clicked.connect(self.discard_roi)
        self.buttonCrop.clicked.connect(self.crop_image_on)
        self.buttonCropDiscard.clicked.connect(self.discard_crop)

        # self.graphicsView = self.findChild(QGraphicsView, "graphicsView")

    def discard_crop(self):
        self.crop_flag = 0

    def discard_roi(self):
        self.freehand_temp = self.current_image.copy()
        self.undo()

    def crop_image_on(self):
        self.crop_flag = 1

    def crop_image(self, left, top, right, bottom):
        if self.crop_flag == 1 and self.current_image != None:
            try:
                self.cropped_image = self.current_image
                self.cropped_image = self.cropped_image.crop((left, top, right, bottom))
                self.current_image = self.cropped_image
                self.show_image(self.current_image)
                self.save_undo_stack(self.current_image)
                self.crop_flag = 0
            except:
                print("crop error!")

    def crop_image_rect(self):
        if self.crop_flag == 1 and self.current_image != None:
            try:
                temp = self.current_image.copy()
                draw = ImageDraw.Draw(temp)
                draw.rectangle([(self.x1, self.y1), (self.x2, self.y2)], outline='blue', width=2)
                self.show_image(temp)
            except:
                print("Something went wrong!")

    def add_roi(self):
        if self.freehand_temp != None:
            self.current_image = self.freehand_temp
            self.save_undo_stack(self.current_image)

    def select_shape(self, shape):
        if self.current_image != None:
            self.shape = shape
            self.drawing = False
            self.start_pos = QPoint()
            self.end_pos = QPoint()
            self.prev_x = None
            self.prev_y = None
            self.freehand_temp = self.current_image.copy()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_pos = event.pos()


    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_pos = event.pos()
            print(self.start_pos, self.end_pos)
            # self.update()
            self.x1, self.y1 = self.start_pos.x(), self.start_pos.y()
            self.x2, self.y2 = self.end_pos.x(), self.end_pos.y()
            self.crop_image_rect()
            self.draw_on_image()
            self.prev_x, self.prev_y = self.end_pos.x(), self.end_pos.y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.end_pos = event.pos()
            self.prev_x = None
            self.prev_y = None
            self.x1, self.y1 = self.start_pos.x(), self.start_pos.y()
            self.x2, self.y2 = self.end_pos.x(), self.end_pos.y()
            self.crop_image(self.x1, self.y1, self.x2, self.y2)
            # self.update()

    def draw_on_image(self):
        if self.current_image != None and self.x1 <= self.x2 and self.y1 <= self.y2:
            if self.shape == "rectangle":
                self.freehand_temp = self.current_image.copy()
                draw = ImageDraw.Draw(self.freehand_temp)
                draw.rectangle([(self.x1, self.y1), (self.x2, self.y2)], outline='red', width=2)
                self.show_image(self.freehand_temp)

            if self.shape == "circle":
                self.freehand_temp = self.current_image.copy()
                draw = ImageDraw.Draw(self.freehand_temp)
                draw.ellipse([(self.x1, self.y1), (self.x2, self.y2)], outline='red', width=2)
                self.show_image(self.freehand_temp)

        if self.shape == "freehand" and self.freehand_temp != None:
            draw = ImageDraw.Draw(self.freehand_temp)
            if self.prev_x is not None and self.prev_y is not None:
                draw.line([(self.prev_x, self.prev_y), (self.x2, self.y2)], fill="red", width=3)
            self.show_image(self.freehand_temp)


    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        file_info = QFileInfo(file_path)
        file_extension = file_info.suffix()

        if file_path != "" and (file_extension == "jpg" or file_extension == "png"):            
            self.undo_stack = []
            self.redo_stack = []
            self.freehand_temp = None
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
        if len(self.undo_stack) <= self.undo_count:
            self.undo_stack.append(image)
            print("undo_stack = ",self.undo_stack)
        else:
            self.undo_stack.pop(0)
            self.undo_stack.append(image)
            print("undo_stack = ",self.undo_stack)

    def save_redo_stack(self, image):
        if len(self.redo_stack) <= self.undo_count:
            self.redo_stack.append(image)
            print("redo_stack = ",self.redo_stack)
        else:
            self.redo_stack.pop(0)
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
        pixmap = QPixmap(self.temp)
        self.imageview.setPixmap(pixmap)
        # scene = QGraphicsScene()
        # pixmap = QPixmap(self.temp)
        # pixmap_item = QGraphicsPixmapItem(pixmap)
        # scene.addItem(pixmap_item)
        # self.graphicsView.setScene(scene)

    def rotate_image(self, value):
        if self.current_image != None:
            self.rotate_angle = value
            self.rotated_image = self.current_image.rotate(value, expand=True)
            self.show_image(self.rotated_image)

    def accept_rotation(self):  
        if self.current_image != None:    
            try:  
                self.current_image = self.rotated_image
                self.save_undo_stack(self.current_image)
            except:
                print("Image not rotated!")

    # def discard_rotation(self):
    #     if self.current_image != None:
    #         self.current_image = self.image
    #         self.save_undo_stack(self.current_image)
    #         self.show_image(self.current_image)

    def zoom_image(self, value):
        if self.current_image != None:
            width, height = self.current_image.size
            new_width = int(width * value/80)
            new_height = int(height * value/80)
            zoomed_image = self.current_image.resize((new_width, new_height))
            self.show_image(zoomed_image)

    def fit_in_window(self):
        if self.current_image != None:
            view_size = self.imageview.size()
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
    