import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QGraphicsScene, QGraphicsPixmapItem, QGraphicsView
from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PIL import Image, ImageDraw
from PyQt5.QtCore import QFileInfo, QFile, Qt, QPoint
from reportlab.pdfgen import canvas
from functools import partial

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        uic.loadUi("MainWindow.ui", self)
        self.temp = "temp.jpg"
        self.tojpg = "tojpg.jpg"
        self.current_image = None
        self.undo_stack = []
        self.redo_stack = []
        self.roi_stack = []
        self.shape = "no-roi"
        self.crop_flag = 0
        self.before_crop = None
        self.undo_count = 3

        self.buttonOpenImage.clicked.connect(self.open_file_dialog)
        self.actionOPne.triggered.connect(self.open_file_dialog)
        self.spinRotation.valueChanged.connect(self.rotate_image)
        self.sliderDisplayZoom_2.valueChanged.connect(self.rotate_image)
        self.sliderDisplayZoom.valueChanged.connect(self.zoom_image)
        self.buttonRotationAccept.clicked.connect(self.accept_rotation)
        self.buttonRotationDiscard.clicked.connect(self.discard_rotation)
        self.buttonFitWindow.clicked.connect(self.fit_window)
        self.buttonOpenImage_2.clicked.connect(self.undo)
        self.buttonOpenImage_3.clicked.connect(self.redo)
        self.actionSave.triggered.connect(self.show_save_dialog)
        self.actionSave_As.triggered.connect(self.save_as_pdf)
        self.radioROInone.toggled.connect(partial(self.select_shape, "no-roi"))
        self.radioROIcircle.toggled.connect(partial(self.select_shape, "circle"))
        self.radioROIrectangle.toggled.connect(partial(self.select_shape, "rectangle"))
        self.radioROIfreehand.toggled.connect(partial(self.select_shape, "freehand"))
        # self.buttonROIAdd.clicked.connect(self.add_roi)
        # self.buttonROIExclude.clicked.connect(self.undo)
        self.buttonROIDiscard.clicked.connect(self.discard_roi)
        self.buttonCrop.clicked.connect(self.crop_image_on)
        self.buttonCropDiscard.clicked.connect(self.discard_crop)

        # self.graphicsView = self.findChild(QGraphicsView, "graphicsView")
    

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousepress = True
            self.start_pos = event.pos()

    def mouseMoveEvent(self, event):
            if self.mousepress:
                self.end_pos = event.pos()
                self.x1, self.y1 = self.start_pos.x(), self.start_pos.y()
                self.x2, self.y2 = self.end_pos.x(), self.end_pos.y()
                self.crop_image_rect()
                self.draw_on_image()
                self.prev_x, self.prev_y = self.end_pos.x(), self.end_pos.y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousepress = False
            self.prev_x = None
            self.prev_y = None
            self.end_pos = event.pos()
            self.x1, self.y1 = self.start_pos.x(), self.start_pos.y()
            self.x2, self.y2 = self.end_pos.x(), self.end_pos.y()
            self.crop_image()
            self.accept_roi()

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        file_info = QFileInfo(file_path)
        file_extension = file_info.suffix()
        extension = ["jpg", "JPG", "jpeg", "JPEG", "png", "PNG", "tiff", "TIFF", "bmp", "BMP"]

        if file_path != "" and (file_extension in extension):
            self.undo_stack = []
            self.redo_stack = []
            self.shape = "no-roi"
            self.roi_stack = []
            self.before_crop = None
            self.crop_flag = 0
            self.radioROInone.setChecked(True)
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            
            self.current_image = Image.open(file_path)
            self.current_image.convert("RGB").save(self.tojpg, "JPEG")
            self.current_image = Image.open(self.tojpg)
            self.current_image = self.fit_in_window(self.current_image)
            self.save_undo_stack(self.current_image)
            self.freehand_image = self.current_image.copy()
            self.show_image(self.current_image)
            file = QFile(self.tojpg)
            file.remove()
            


        # if file_path != "" and (file_extension in extension):            
        #     self.undo_stack = []
        #     self.redo_stack = []
        #     self.shape = "no-roi"
        #     self.radioROInone.setChecked(True)
        #     QApplication.setOverrideCursor(Qt.ArrowCursor)
        #     self.current_image = Image.open(file_path)
        #     self.temp = "temp."+file_extension
        #     image = self.fit_in_window(self.current_image)
        #     self.current_image = image
        #     self.save_undo_stack(self.current_image)
        #     self.freehand_image = self.current_image.copy()
        #     self.show_image(image)
        else:
            self.imageview.setText("This format is not supported!")

    def show_save_dialog(self):
        if self.current_image != None:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, extension = QFileDialog.getSaveFileName(self, "Save File", "", "JPG file (*.jpg) ;; TIFF file (*.tiff) ;; BMP file (*.bmp)",  options=options)

            if file_name != "": 
                if extension == "JPG file (*.jpg)":
                    file_name = file_name+".jpg"
                    self.current_image.convert("RGB").save(file_name, "JPEG")
                    file = QFile(self.temp)
                    file.remove()
                elif extension == "TIFF file (*.tiff)":
                    file_name = file_name+".tiff"
                    self.current_image.convert("RGB").save(file_name, "TIFF")
                    file = QFile(self.temp)
                    file.remove()
                elif extension == "BMP file (*.bmp)":
                    file_name = file_name+".bmp"
                    self.current_image.convert("RGB").save(file_name, "BMP")
                    file = QFile(self.temp)
                    file.remove()
                else:
                    print(extension, "Does not suppoert!")

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
        if len(self.redo_stack) < self.undo_count:
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
            self.freehand_image = self.current_image.copy()

        elif len(self.undo_stack) > 1:
            self.save_redo_stack(self.undo_stack[-1])
            self.undo_stack.pop()
            self.current_image = self.undo_stack[-1]
            self.show_image(self.current_image)
            self.freehand_image = self.current_image.copy()

        print("undo_stack = ",self.undo_stack)

    def redo(self):
        if len(self.redo_stack) > 0:
            self.save_undo_stack(self.redo_stack[-1])
            self.current_image = self.redo_stack[-1]
            self.show_image(self.current_image)
            self.redo_stack.pop()
            self.freehand_image = self.current_image.copy()

        print("redo_stack = ",self.redo_stack)

    def show_image(self, image):
        image.save(self.temp)
        pixmap = QPixmap(self.temp)
        self.imageview.setPixmap(pixmap)

    
    def fit_in_window(self, image):
        if self.current_image != None:
            x = 20
            image_width, image_height = image.size
            if image_width > image_height and image_width > self.scrollAreaImage.width():
                new_height = round(self.scrollAreaImage.width() * image_height/image_width)
                image = image.resize((self.scrollAreaImage.width()-x, new_height-x))
                print("width")
            
            elif image_height > image_width and image_height > self.scrollAreaImage.height():
                new_width = round(self.scrollAreaImage.height() * image_width/image_height)
                image = image.resize((new_width-x, self.scrollAreaImage.height()-x))
                print("height")  

            elif image_height == image_width and (image_height > self.scrollAreaImage.height() or image_width > self.scrollAreaImage.width()):
                height_gap = self.scrollAreaImage.height()-image_height
                width_gap = self.scrollAreaImage.width()-image_width
                    
                if height_gap > width_gap:
                    new_height = round(self.scrollAreaImage.width() * image_height/image_width)
                    image = image.resize((self.scrollAreaImage.width()-x, new_height-x))
                    print("width")

                if width_gap > height_gap:
                    new_width = round(self.scrollAreaImage.height() * image_width/image_height)
                    image = image.resize((new_width-x, self.scrollAreaImage.height()-x))
                    print("height") 

            return image 

# ==================================== Basic Editing ===========================================

    def rotate_image(self, value):
        if self.current_image != None:
            self.rotate_angle = value
            image = self.current_image.copy()
            self.rotated_image = image.rotate(value, expand=True)
            self.rotated_image = self.fit_in_window(self.rotated_image)
            self.show_image(self.rotated_image)
            self.shape = "no-roi"
            self.radioROInone.setChecked(True)
            QApplication.setOverrideCursor(Qt.ArrowCursor)

    def accept_rotation(self):  
        if self.current_image != None:
            self.current_image = self.rotated_image
            self.save_undo_stack(self.current_image)
            self.roi_stack = []

    def discard_rotation(self):
        if self.current_image != None:
            image = self.fit_in_window(self.current_image)
            self.show_image(image)

    def crop_image_on(self):
        self.crop_flag = 1
        self.shape = "no-roi"
        self.radioROInone.setChecked(True)
        QApplication.setOverrideCursor(Qt.CrossCursor)

    def crop_image(self):
        if self.crop_flag == 1 and self.current_image != None:

            if self.x1 > self.x2:
                tmp = self.x1
                self.x1 = self.x2
                self.x2 = tmp

            if self.y1 > self.y2:
                tmp = self.y1
                self.y1 = self.y2
                self.y2 = tmp

            self.before_crop = self.current_image.copy()
            image_width, image_height = self.current_image.size
            gap_x = self.imageview.width() - self.imageview.width()/2 - image_width/2 + 9
            gap_y = self.height() - self.height()/2 - image_height/2

            self.x1 = self.x1 - gap_x
            self.y1 = self.y1 - gap_y
            self.x2 = self.x2 - gap_x
            self.y2 = self.y2 - gap_y
            
            self.current_image = self.current_image.crop((self.x1, self.y1, self.x2, self.y2))
            self.show_image(self.current_image)
            self.crop_flag = 0
            self.save_undo_stack(self.current_image)
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            self.roi_stack = []

    def crop_image_rect(self):
        if self.crop_flag == 1 and self.current_image != None:

            if self.x1 > self.x2:
                tmp = self.x1
                self.x1 = self.x2
                self.x2 = tmp

            if self.y1 > self.y2:
                tmp = self.y1
                self.y1 = self.y2
                self.y2 = tmp

            image_width, image_height = self.current_image.size
            gap_x = self.imageview.width() - self.imageview.width()/2 - image_width/2 + 9
            gap_y = self.height() - self.height()/2 - image_height/2

            self.x1 = self.x1 - gap_x
            self.y1 = self.y1 - gap_y
            self.x2 = self.x2 - gap_x
            self.y2 = self.y2 - gap_y

            crop_rect = self.current_image.copy()
            draw = ImageDraw.Draw(crop_rect)
            draw.rectangle([(self.x1, self.y1), (self.x2, self.y2)], outline='blue', width=2)
            self.show_image(crop_rect)

    def discard_crop(self):
        if self.before_crop != None:
            self.current_image = self.before_crop
            self.show_image(self.current_image)
        
        QApplication.setOverrideCursor(Qt.ArrowCursor)
        self.crop_flag = 0
        # self.undo()


# ==================================== Display Editing ===========================================

    def zoom_image(self, value):
        if self.current_image != None:
            zoom_image = self.current_image.copy()
            width, height = zoom_image.size
            new_width = int(width * value/100)
            new_height = int(height * value/100)
            zoomed_image = zoom_image.resize((new_width, new_height))
            self.show_image(zoomed_image)


    def fit_window(self):
        if self.current_image != None:
            x = 20
            image_width, image_height = self.current_image.size
            self.shape = "no-roi"
            self.radioROInone.setChecked(True)
            QApplication.setOverrideCursor(Qt.ArrowCursor)

            if image_width > image_height:
                new_height = round(self.scrollAreaImage.width() * image_height/image_width)
                self.current_image = self.current_image.resize((self.scrollAreaImage.width()-x, new_height-x))
                self.show_image(self.current_image)
                self.save_undo_stack(self.current_image)
                self.roi_stack = []
            
            elif image_height > image_width:
                new_width = round(self.scrollAreaImage.height() * image_width/image_height)
                self.current_image = self.current_image.resize((new_width-x, self.scrollAreaImage.height()-x))
                self.show_image(self.current_image)
                self.save_undo_stack(self.current_image)
                self.roi_stack = []

            elif image_height == image_width:
                height_gap = self.scrollAreaImage.height()-image_height
                width_gap = self.scrollAreaImage.width()-image_width
                if height_gap > width_gap:
                    new_height = round(self.scrollAreaImage.width() * image_height/image_width)
                    self.current_image = self.current_image.resize((self.scrollAreaImage.width()-x, new_height-x))
                    self.show_image(self.current_image)
                    self.save_undo_stack(self.current_image)
                    self.roi_stack = []

                if width_gap > height_gap:
                    new_width = round(self.scrollAreaImage.height() * image_width/image_height)
                    self.current_image = self.current_image.resize((new_width-x, self.scrollAreaImage.height()-x))
                    self.show_image(self.current_image)
                    self.save_undo_stack(self.current_image)
                    self.roi_stack = []



# ==================================== Basic Editing ===========================================

    def select_shape(self, shape):
        if self.current_image != None:
            self.shape = shape
            self.prev_x = None
            self.prev_y = None
            self.freehand_image = self.current_image.copy()
            if shape == "no-roi":
                QApplication.setOverrideCursor(Qt.ArrowCursor)
            else:
                QApplication.setOverrideCursor(Qt.PointingHandCursor)

    def draw_on_image(self):
        if self.current_image != None:
            image_width, image_height = self.current_image.size
            gap_x = self.imageview.width() - self.imageview.width()/2 - image_width/2 + 9
            gap_y = self.height() - self.height()/2 - image_height/2

            self.x1 = self.x1 - gap_x
            self.y1 = self.y1 - gap_y
            self.x2 = self.x2 - gap_x
            self.y2 = self.y2 - gap_y

            if self.shape == "freehand":
                draw = ImageDraw.Draw(self.freehand_image)
                if self.prev_x is not None and self.prev_y is not None:
                    draw.line([(self.prev_x - gap_x, self.prev_y - gap_y), (self.x2, self.y2)], fill="red", width=3)
                self.show_image(self.freehand_image)

            if self.x1 > self.x2:
                tmp = self.x1
                self.x1 = self.x2
                self.x2 = tmp

            if self.y1 > self.y2:
                tmp = self.y1
                self.y1 = self.y2
                self.y2 = tmp

            if self.shape == "circle":
                self.circle_image = self.current_image.copy()
                draw = ImageDraw.Draw(self.circle_image)
                draw.ellipse([(self.x1, self.y1), (self.x2, self.y2)], outline='red', width=2)
                self.show_image(self.circle_image)

            if self.shape == "rectangle":
                self.rect_image = self.current_image.copy()
                draw = ImageDraw.Draw(self.rect_image)
                draw.rectangle([(self.x1, self.y1), (self.x2, self.y2)], outline='red', width=2)
                self.show_image(self.rect_image)              

    def accept_roi(self):
        try:
            self.roi_stack.append(self.current_image)

            if self.shape == "circle":
                self.current_image = self.circle_image
                self.save_undo_stack(self.current_image)

            elif self.shape == "rectangle":
                self.current_image = self.rect_image
                self.save_undo_stack(self.current_image)
            elif self.shape == "freehand":
                self.current_image = self.freehand_image
                self.save_undo_stack(self.current_image)
                self.freehand_image = self.current_image.copy()
        except:
            print("Error")

    def discard_roi(self):
        if len(self.roi_stack) > 0:
            self.current_image = self.roi_stack[-1]
            self.roi_stack.pop()
            self.save_undo_stack(self.current_image)
            self.freehand_image = self.current_image.copy()
            self.show_image(self.current_image)
            # self.undo()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    