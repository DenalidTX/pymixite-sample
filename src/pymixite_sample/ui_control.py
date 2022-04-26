from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPainter, QPolygonF
from PyQt5.QtWidgets import QGraphicsScene, QLineEdit
from mixite import HexagonImpl, Point
from mixite.coord import CubeCoordinate
from mixite.builder import GridControlBuilder, GridControl
from mixite.layout import GridLayoutException


class UIInitializer:
    """
    This class is tailored for the sample UI form. As such, it will fail with
    unknown consequences if elements are removed or renamed. You have been
    warned.
    """

    orientations: dict[str, str] = {
        "Pointy Top": CubeCoordinate.POINTY_TOP,
        "Flat Top": CubeCoordinate.FLAT_TOP
    }

    hexagon_str = "Hexagon"
    trapezoid_str = "Trapezoid"
    rectangle_str = "Rectangle"
    triangle_str = "Triangle"

    def __init__(self, root_widget):
        self.root_widget = root_widget

        for orientation in self.orientations.keys():
            self.root_widget.orientationComboBox.addItem(orientation)

        self.root_widget.layoutComboBox.addItem(self.rectangle_str)
        self.root_widget.layoutComboBox.addItem(self.triangle_str)
        self.root_widget.layoutComboBox.addItem(self.hexagon_str)
        self.root_widget.layoutComboBox.addItem(self.trapezoid_str)

        self.root_widget.canvas.mouseMoveEvent = self.mouse_move_event
        self.builder: GridControlBuilder = GridControlBuilder()
        self.grid_control: GridControl = None
        self.redraw_grid()

        self.root_widget.layoutComboBox.currentIndexChanged.connect(self.redraw_grid)
        self.root_widget.orientationComboBox.currentIndexChanged.connect(self.redraw_grid)
        self.root_widget.gridWidthBox.valueChanged.connect(self.redraw_grid)
        self.root_widget.gridHeightBox.valueChanged.connect(self.redraw_grid)
        self.root_widget.cellRadiusBox.valueChanged.connect(self.redraw_grid)

    def mouse_move_event(self, event):
        self.root_widget.canvasXBox.setText(str(event.x()))
        self.root_widget.canvasYBox.setText(str(event.y()))
        pass

    def redraw_grid(self):

        selected_shape: str = self.root_widget.layoutComboBox.currentText()
        selected_orientation: str = self.root_widget.orientationComboBox.currentText()
        orientation_value = self.orientations.get(selected_orientation)
        width_value = int(self.root_widget.gridWidthBox.value())
        height_value = int(self.root_widget.gridHeightBox.value())
        cell_radius = int(self.root_widget.cellRadiusBox.value())

        try:
            if self.hexagon_str == selected_shape:
                self.grid_control = self.builder\
                    .build_hexagon(orientation_value, cell_radius, width_value, height_value)
            elif self.triangle_str == selected_shape:
                self.grid_control = self.builder\
                    .build_triangle(orientation_value, cell_radius, width_value, height_value)
            elif self.trapezoid_str == selected_shape:
                self.grid_control = self.builder\
                    .build_trapezoid(orientation_value, cell_radius, width_value, height_value)
            else:
                self.grid_control = self.builder\
                    .build_rectangle(orientation_value, cell_radius, width_value, height_value)

            hexagon: HexagonImpl
            scene: QGraphicsScene = QGraphicsScene()
            for hexagon in self.grid_control.hex_grid.hexagons:
                points: list[Point] = hexagon.calculate_points(hexagon.calculate_center())
                poly = QPolygonF()
                for point in points:
                    poly.append(QPointF(point.coordX, point.coordY))
                scene.addPolygon(poly)
            self.root_widget.canvas.setScene(scene)
            self.root_widget.statusBar().clearMessage()
        except GridLayoutException as ex:
            print("Exception: ", ex.message)
            self.root_widget.statusBar().showMessage(ex.message, 10000)
