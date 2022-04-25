from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPainter, QPolygonF
from PyQt5.QtWidgets import QGraphicsScene, QLineEdit
from mixite import HexagonImpl, Point
from mixite.coord import CubeCoordinate
from mixite.builder import GridControlBuilder, GridControl


class UIInitializer:
    """
    This class is tailored for the sample UI form. As such, it will fail with
    unknown consequences if elements are removed or renamed. You have been
    warned.
    """
    hexagon_str = "Hexagon"
    trapezoid_str = "Trapezoid"
    rectangle_str = "Rectangle"
    triangle_str = "Triangle"

    def __init__(self, root_widget):
        self.root_widget = root_widget

        self.root_widget.orientationComboBox.addItem("Pointy Top")
        self.root_widget.orientationComboBox.addItem("Flat Top")

        self.root_widget.layoutComboBox.addItem(self.rectangle_str)
        self.root_widget.layoutComboBox.addItem(self.triangle_str)
        self.root_widget.layoutComboBox.addItem(self.hexagon_str)
        self.root_widget.layoutComboBox.addItem(self.trapezoid_str)

        self.root_widget.canvas.mouseMoveEvent = self.mouse_move_event
        self.builder: GridControlBuilder = GridControlBuilder()
        self.grid_control: GridControl = self.builder.build_rectangle(CubeCoordinate.POINTY_TOP, 20, 10, 10)
        self.redraw_grid()

        self.root_widget.layoutComboBox.currentIndexChanged.connect(self.redraw_grid)

    def mouse_move_event(self, event):
        self.root_widget.canvasXBox.setText(str(event.x()))
        self.root_widget.canvasYBox.setText(str(event.y()))
        pass

    def redraw_grid(self):

        selected_shape: str = self.root_widget.layoutComboBox.currentText()

        if self.hexagon_str == selected_shape:
            self.grid_control = self.builder.build_hexagon(CubeCoordinate.POINTY_TOP, 20, 9, 9)
        elif self.triangle_str == selected_shape:
            self.grid_control = self.builder.build_triangle(CubeCoordinate.POINTY_TOP, 20, 10, 10)
        elif self.trapezoid_str == selected_shape:
            self.grid_control = self.builder.build_trapezoid(CubeCoordinate.POINTY_TOP, 20, 10, 10)
        else:
            self.grid_control = self.builder.build_rectangle(CubeCoordinate.POINTY_TOP, 20, 10, 10)

        hexagon: HexagonImpl
        scene: QGraphicsScene = QGraphicsScene()
        for hexagon in self.grid_control.hex_grid.hexagons:
            points: list[Point] = hexagon.calculate_points(hexagon.calculate_center())
            poly = QPolygonF()
            for point in points:
                poly.append(QPointF(point.coordX, point.coordY))
            scene.addPolygon(poly)
        self.root_widget.canvas.setScene(scene)
