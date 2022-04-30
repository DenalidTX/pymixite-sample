import math

from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPainter, QPolygonF, QBrush, QColor, QFont, QPen
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPolygonItem, QGraphicsTextItem
from mixite import HexagonImpl, Point, SatelliteData
from mixite.coord import CubeCoordinate
from mixite.builder import GridControlBuilder, GridControl
from mixite.layout import GridLayoutException


class DrawableSatelliteData(SatelliteData):

    def __init__(self, hex_widget):
        super().__init__()
        self.hex_widget: QGraphicsPolygonItem = hex_widget
        self.path_widget: QGraphicsPolygonItem | None = None
        self.coord_widgets: list[QGraphicsTextItem] | None = None

        self.show_as_neighbor = False
        self.show_as_movable = False
        self.show_as_current = False
        self.show_as_visible = False
        self.show_as_not_visible = False

    def set_path_widget(self, widget):
        self.path_widget = widget
        if self.path_widget is not None:
            self.path_widget.setBrush(QBrush(QColor("purple")))

    def get_path_widget(self):
        return self.path_widget

    def get_coord_widgets(self):
        return self.coord_widgets

    def set_coord_widgets(self, x_widget, y_widget, z_widget):
        if x_widget is None:
            self.coord_widgets = None
        else:
            self.coord_widgets = [x_widget, y_widget, z_widget]

    def set_neighbor(self):
        self.show_as_neighbor = True
        self.determine_color()

    def unset_neighbor(self):
        self.show_as_neighbor = False
        self.determine_color()

    def set_selected(self):
        self.isSelected = True
        self.determine_color()

        # This defaults to False, but to get proper visibility
        # displays we need it to be True for selected hexes.
        self.isOpaque = True

    def unset_selected(self):
        self.isSelected = False
        self.determine_color()

        # This defaults to False, but to get proper visibility
        # displays we need it to be True for selected hexes.
        self.isOpaque = False

    def set_movable(self):
        self.show_as_movable = True
        self.determine_color()

    def unset_movable(self):
        self.show_as_movable = False
        self.determine_color()

    def set_current(self):
        self.show_as_current = True
        self.determine_color()

    def unset_current(self):
        self.show_as_current = False
        self.determine_color()

    def set_visible(self):
        self.show_as_visible = True
        self.show_as_not_visible = False
        self.determine_color()

    def set_not_visible(self):
        self.show_as_visible = False
        self.show_as_not_visible = True
        self.determine_color()

    def disable_visibility(self):
        self.show_as_visible = False
        self.show_as_not_visible = False
        self.determine_color()

    def determine_color(self):
        # Set fill color.
        brush_color = QColor("transparent")

        if self.isSelected:
            brush_color = QColor("blue")
        elif self.show_as_neighbor:
            brush_color = QColor("grey")
        elif self.show_as_movable:
            brush_color = QColor("yellow")

        self.hex_widget.setBrush(brush_color)

        # Set line color.
        # This is just a little jank because the highlight is on
        # the same z-level as the rest of the hexagons, and the
        # hexagons are drawn top-down and left-right. So the black
        # bottom and right hexagons will always overlay the purple
        # ones. It's a demo. If you don't like it, feel free to
        # fix it. :P
        line_pen = QPen()
        line_pen.setColor(QColor("black"))
        line_pen.setWidth(1)
        if self.show_as_current:
            line_pen.setColor(QColor("purple"))
            line_pen.setWidth(5)
        elif self.show_as_visible:
            line_pen.setColor(QColor("green"))
            line_pen.setWidth(5)
        elif self.show_as_not_visible:
            line_pen.setColor(QColor("red"))
            line_pen.setWidth(5)

        self.hex_widget.setPen(line_pen)


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

        self.last_selected: HexagonImpl = None

        self.root_widget.layoutComboBox.currentIndexChanged.connect(self.create_grid)
        self.root_widget.orientationComboBox.currentIndexChanged.connect(self.create_grid)
        self.root_widget.gridWidthBox.valueChanged.connect(self.create_grid)
        self.root_widget.gridHeightBox.valueChanged.connect(self.create_grid)
        self.root_widget.cellRadiusBox.valueChanged.connect(self.create_grid)

        self.root_widget.showNeighborsCheck.stateChanged.connect(self.redraw_all)
        self.root_widget.showPathCheck.stateChanged.connect(self.redraw_all)
        self.root_widget.showMoveRangeCheck.stateChanged.connect(self.redraw_all)
        self.root_widget.moveRangeBox.valueChanged.connect(self.redraw_all)
        self.root_widget.showCoordsCheck.stateChanged.connect(self.toggle_coords)

    def mouse_move_event(self, event):
        """
        This method updates the current canvas coordinates. It also updates the current
        grid distance to the last selected hexagon, if any is designated.
        :param event:
        :return:
        """
        mouse_x = event.x()
        mouse_y = event.y()
        self.root_widget.canvasXBox.setText(str(mouse_x))
        self.root_widget.canvasYBox.setText(str(mouse_y))

        self.update_path_and_visibility(mouse_x, mouse_y)

        current_hex = self.grid_control.hex_grid.get_hex_by_pixel_coord(mouse_x, mouse_y)
        if self.last_selected is None or current_hex is None:
            self.root_widget.distToLastBox.setText("")
        else:
            distance = self.grid_control.calculator.calc_distance_between(self.last_selected, current_hex)
            self.root_widget.distToLastBox.setText(str(distance))

    def create_grid(self):

        selected_shape: str = self.root_widget.layoutComboBox.currentText()
        selected_orientation: str = self.root_widget.orientationComboBox.currentText()
        orientation_value = self.orientations.get(selected_orientation)
        width_value = int(self.root_widget.gridWidthBox.value())
        height_value = int(self.root_widget.gridHeightBox.value())
        cell_radius = int(self.root_widget.cellRadiusBox.value())

        try:
            if self.hexagon_str == selected_shape:
                self.grid_control = self.builder \
                    .build_hexagon(orientation_value, cell_radius, width_value, height_value)
            elif self.triangle_str == selected_shape:
                self.grid_control = self.builder \
                    .build_triangle(orientation_value, cell_radius, width_value, height_value)
            elif self.trapezoid_str == selected_shape:
                self.grid_control = self.builder \
                    .build_trapezoid(orientation_value, cell_radius, width_value, height_value)
            else:
                self.grid_control = self.builder \
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

            # Handle things that were already checked.
            self.toggle_neighbors()
            self.toggle_move_range()
            self.toggle_coords()

            # If we had something selected, forget it.
            self.last_selected = None
        except GridLayoutException as ex:
            print("Exception: ", ex.message)
            self.root_widget.statusBar().showMessage(ex.message, 10000)

    def select_hex(self, event):

        mouse_x = event.scenePos().x()
        mouse_y = event.scenePos().y()

        hexagon = self.grid_control.hex_grid.get_hex_by_pixel_coord(mouse_x, mouse_y)

        if hexagon is not None:
            # Change the current (outlined) hex. This is the hex
            # from which distance and visibility are calculated.
            satellite: DrawableSatelliteData = hexagon.get_satellite()
            was_selected: bool = satellite.isSelected

            if was_selected:
                if self.last_selected == hexagon:
                    self.last_selected = None
                satellite.unset_current()
                satellite.unset_selected()
            else:
                if self.last_selected is not None:
                    self.last_selected.get_satellite().unset_current()
                self.last_selected = hexagon
                satellite.set_current()
                satellite.set_selected()

            self.redraw_partial(mouse_x, mouse_y)

    def toggle_neighbors(self):
        # Unset everything, then set the ones that ought to be set.
        # This is much easier than trying to get the intersection of
        # neighbors of multiple hexes. Since we are storing neighbor
        # status instead of determining it on the fly we could end
        # up deselecting and de-neighboring too many hexagons.
        for hexagon in self.grid_control.hex_grid.hexagons:
            hexagon.get_satellite().unset_neighbor()

        if self.root_widget.showNeighborsCheck.isChecked():
            for hexagon in self.grid_control.hex_grid.hexagons:
                if hexagon.get_satellite().isSelected:
                    for neighbor in self.grid_control.hex_grid.get_neighbors_of(hexagon):
                        neighbor.get_satellite().set_neighbor()

    def toggle_move_range(self):
        # Unset everything, then set the ones that ought to be set.
        # This is much easier than trying to get the intersection of
        # neighbors of multiple hexes. Since we are storing neighbor
        # status instead of determining it on the fly we could end
        # up deselecting and de-neighboring too many hexagons.
        for hexagon in self.grid_control.hex_grid.hexagons:
            hexagon.get_satellite().unset_movable()

        if self.root_widget.showMoveRangeCheck.isChecked():
            move_range = int(self.root_widget.moveRangeBox.value())
            for hexagon in self.grid_control.hex_grid.hexagons:
                if hexagon.get_satellite().isSelected:
                    for neighbor in self.grid_control.calculator.calc_move_range_from(hexagon, move_range):
                        neighbor.get_satellite().set_movable()

    def update_path_and_visibility(self, x, y):
        # Remove the old path and make a new one.
        for hexagon in self.grid_control.hex_grid.hexagons:
            widget = hexagon.get_satellite().get_path_widget()
            if widget is not None:
                self.scene.removeItem(widget)
                hexagon.get_satellite().set_path_widget(None)
            # While we're at it, reset visibility.
            hexagon.get_satellite().disable_visibility()

        try:
            if self.last_selected is not None:
                hovering = self.grid_control.hex_grid.get_hex_by_pixel_coord(x, y)
                if hovering is not None:
                    # Add the grid coordinates to the display.
                    self.root_widget.gridXBox.setText(str(hovering.get_coords().gridX))
                    self.root_widget.gridYBox.setText(str(hovering.get_coords().grid_y()))
                    self.root_widget.gridZBox.setText(str(hovering.get_coords().gridZ))

                    path_hexes = self.grid_control.calculator.draw_line(self.last_selected, hovering)
                    radius = self.grid_control.grid_data.innerRadius / 2
                    for hexagon in path_hexes:
                        # Display the path indicators if they are turned on.
                        if self.root_widget.showPathCheck.isChecked():
                            center_x = hexagon.center.coordX
                            center_y = hexagon.center.coordY

                            if hexagon.get_satellite().get_path_widget() is None:
                                center_offset = radius / 2
                                hexagon.get_satellite().set_path_widget(
                                    self.scene.addEllipse(center_x - center_offset, center_y - center_offset,
                                                          radius, radius))

                        # Also display visibility indicators if they are turned on.
                        if self.root_widget.showVisibilityCheck.isChecked():
                            if self.grid_control.calculator.is_visible(self.last_selected, hexagon):
                                hexagon.get_satellite().set_visible()
                            else:
                                hexagon.get_satellite().set_not_visible()
        except Exception as ex:
            print("Oh no!", ex)
        self.redraw_all()

    def toggle_coords(self):
        if self.root_widget.showCoordsCheck.isChecked():
            try:
                for hexagon in self.grid_control.hex_grid.hexagons:
                    # First create the text objects if needed.
                    if hexagon.get_satellite().get_coord_widgets() is None:
                        x_text = "X: " + str(hexagon.coords.gridX)
                        y_text = "X: " + str(hexagon.coords.grid_y())
                        z_text = "X: " + str(hexagon.coords.gridZ)
                        hexagon.get_satellite().set_coord_widgets(
                            self.scene.addText(x_text),
                            self.scene.addText(y_text),
                            self.scene.addText(z_text))

                        widgets: list[QGraphicsTextItem] = hexagon.get_satellite().get_coord_widgets()

                        # Once we have them, resize and reposition as necessary.
                        radius = self.grid_control.grid_data.innerRadius
                        text_size = radius / 3

                        center_x = hexagon.center.coordX
                        center_y = hexagon.center.coordY
                        # The exact position doesn't matter, as long as the text doesn't overlap.
                        widgets[0].setPos(center_x - radius, center_y - (text_size * 2.5))
                        widgets[1].setPos(center_x - radius, center_y - (text_size * 1.25))
                        widgets[2].setPos(center_x - radius, center_y)

                        font = QFont()
                        font.setPixelSize(math.ceil(text_size))
                        widgets[0].setFont(font)
                        widgets[1].setFont(font)
                        widgets[2].setFont(font)

                    # Remove and then add, to prevent duplicates in non-standard cases.
                    widgets: list[QGraphicsTextItem] = hexagon.get_satellite().get_coord_widgets()
                    self.scene.removeItem(widgets[0])
                    self.scene.removeItem(widgets[1])
                    self.scene.removeItem(widgets[2])
                    self.scene.addItem(widgets[0])
                    self.scene.addItem(widgets[1])
                    self.scene.addItem(widgets[2])

            except Exception as ex:
                print("Error!", ex)
                print(ex)

        else:
            for hexagon in self.grid_control.hex_grid.hexagons:
                if hexagon.get_satellite().get_coord_widgets() is not None:
                    widgets = hexagon.get_satellite().get_coord_widgets()
                    self.scene.removeItem(widgets[0])
                    self.scene.removeItem(widgets[1])
                    self.scene.removeItem(widgets[2])


    def redraw_partial(self, x, y):
        self.toggle_neighbors()
        self.toggle_move_range()
        # Rather than figure out exactly what to redraw, just do enough math
        # to make sure we get the whole hexagon, even when the click is on
        # the very edge.
        radius = self.grid_control.grid_data.radius
        self.scene.invalidate(QRectF(x-radius, y-radius, radius*2, radius*2))

    def redraw_all(self):
        self.toggle_neighbors()
        self.toggle_move_range()
        self.root_widget.canvas.invalidateScene()
