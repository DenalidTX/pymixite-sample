from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPainter, QPolygonF, QBrush, QColor
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPolygonItem
from mixite import HexagonImpl, Point, SatelliteData
from mixite.coord import CubeCoordinate
from mixite.builder import GridControlBuilder, GridControl
from mixite.layout import GridLayoutException


class DrawableSatelliteData(SatelliteData):

    def __init__(self, hex_widget):
        super().__init__()
        self.hex_widget: QGraphicsPolygonItem = hex_widget

    def toggle_selected(self):
        self.isSelected = not self.isSelected
        self.determine_color()

    def determine_color(self):
        if self.isSelected:
            self.hex_widget.setBrush(QBrush(QColor("blue")))
        else:
            self.hex_widget.setBrush(QBrush(QColor("transparent")))


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
        self.scene: QGraphicsScene = None
        self.create_grid()

        self.root_widget.layoutComboBox.currentIndexChanged.connect(self.create_grid)
        self.root_widget.orientationComboBox.currentIndexChanged.connect(self.create_grid)
        self.root_widget.gridWidthBox.valueChanged.connect(self.create_grid)
        self.root_widget.gridHeightBox.valueChanged.connect(self.create_grid)
        self.root_widget.cellRadiusBox.valueChanged.connect(self.create_grid)

    def mouse_move_event(self, event):
        self.root_widget.canvasXBox.setText(str(event.x()))
        self.root_widget.canvasYBox.setText(str(event.y()))
        pass

    def create_grid(self):

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
            self.scene = QGraphicsScene()
            self.scene.mousePressEvent = self.select_hex
            for hexagon in self.grid_control.hex_grid.hexagons:
                points: list[Point] = hexagon.calculate_points(hexagon.calculate_center())
                poly = QPolygonF()
                for point in points:
                    poly.append(QPointF(point.coordX, point.coordY))
                hexagon.set_satellite(DrawableSatelliteData(self.scene.addPolygon(poly)))
            self.root_widget.canvas.setScene(self.scene)
            self.root_widget.statusBar().clearMessage()
        except GridLayoutException as ex:
            print("Exception: ", ex.message)
            self.root_widget.statusBar().showMessage(ex.message, 10000)

    def select_hex(self, event):

        mouse_x = event.scenePos().x()
        mouse_y = event.scenePos().y()

        hexagon = self.grid_control.hex_grid.get_hex_by_pixel_coord(mouse_x, mouse_y)

        if hexagon is not None:
            satellite: DrawableSatelliteData = hexagon.get_satellite()
            if satellite is not None:
                satellite.toggle_selected()
                self.redraw_overlays(mouse_x, mouse_y)

    def redraw_overlays(self, x, y):
        radius = self.grid_control.grid_data.radius
        self.scene.invalidate(QRectF(x-radius, y-radius, radius*2, radius*2))
