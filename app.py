import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsScene, QGraphicsPixmapItem
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PIL import Image

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("MainWindow.ui", self)
        self.temp = "temp.jpg"
        self.image_path = ""
        self.current_image = ""
        self.buttonOpenImage.clicked.connect(self.open_file_dialog)
        self.spinRotation.valueChanged.connect(self.rotate_image)
        self.sliderDisplayZoom_2.valueChanged.connect(self.rotate_image)
        self.sliderDisplayZoom.valueChanged.connect(self.zoom_image)
        self.buttonRotationAccept.clicked.connect(self.accept_rotation)
        self.buttonRotationDiscard.clicked.connect(self.discard_rotation)
        
    def show_image(self, image_path):
        scene = QGraphicsScene()
        pixmap = QPixmap(image_path)
        pixmap_item = QGraphicsPixmapItem(pixmap)
        scene.addItem(pixmap_item)
        self.graphicsView.setScene(scene)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")

        if file_path:
            self.image_path = file_path
            self.image = Image.open(self.image_path)
            self.image.save(self.temp)
            self.show_image(self.temp)

    def rotate_image(self, value):
        if self.image_path != "":
            self.rotated_image = self.image.rotate(value, expand=True)
            self.rotated_image.save(self.temp)
            self.show_image(self.temp)

    def accept_rotation(self):
        self.current_image = self.rotated_image

    def discard_rotation(self):
        self.rotated_image = self.image.rotate(0, expand=True)
        self.rotated_image.save(self.temp)
        self.current_image = self.rotated_image
        self.show_image(self.temp)

    def zoom_image(self, value):
        image = None
        if self.image_path != "":
            if self.current_image != "":
                image = self.current_image
            else:
                image = Image.open(self.image_path)

        if image != None:
            width, height = image.size
            new_width = int(width * value/50)
            new_height = int(height * value/50)

            zoomed_image = image.resize((new_width, new_height))
            zoomed_image.save(self.temp)
            self.show_image(self.temp)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())