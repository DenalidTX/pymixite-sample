from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPainter, QPolygonF
from PyQt5.QtWidgets import QGraphicsScene, QLineEdit
from mixite import HexagonImpl, Point
from mixite.calculator import HexagonGridCalculator
from mixite.coord import CubeCoordinate
from mixite.builder import GridControlBuilder, GridControl


class UIInitializer:
    """
    This class is tailored for the sample UI form. As such, it will fail with
    unknown consequences if elements are removed or renamed. You have been
    warned.
    """

    def __init__(self, root_widget):
        self.builder: GridControlBuilder = GridControlBuilder()
        self.grid_control: GridControl = self.builder.build_rectangle(CubeCoordinate.POINTY_TOP, 20, 10, 10)
        self.root_widget = root_widget

        self.root_widget.orientationComboBox.addItem("Pointy Top")
        self.root_widget.orientationComboBox.addItem("Flat Top")

        self.root_widget.layoutComboBox.addItem("Rectangle")
        self.root_widget.layoutComboBox.addItem("Triangle")
        self.root_widget.layoutComboBox.addItem("Hexagon")
        self.root_widget.layoutComboBox.addItem("Trapezoid")

        self.root_widget.canvas.mouseMoveEvent = self.mouse_move_event

        hexagon: HexagonImpl
        scene: QGraphicsScene = QGraphicsScene()
        for hexagon in self.grid_control.hex_grid.hexagons:
            points: list[Point] = hexagon.calculate_points(hexagon.calculate_center())
            poly = QPolygonF()
            for point in points:
                poly.append(QPointF(point.coordX, point.coordY))
            scene.addPolygon(poly)
        self.root_widget.canvas.setScene(scene)

    def mouse_move_event(self, event):
        self.root_widget.canvasXBox.setText(str(event.x()))
        self.root_widget.canvasYBox.setText(str(event.y()))
        pass
