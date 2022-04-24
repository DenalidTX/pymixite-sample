class UIInitializer:
    """
    This class is tailored for the sample UI form. As such, it will fail with
    unknown consequences if elements are removed or renamed. You have been
    warned.
    """

    @staticmethod
    def setup(root_widget):
        root_widget.orientationComboBox.addItem("Pointy Top")
        root_widget.orientationComboBox.addItem("Flat Top")

        root_widget.layoutComboBox.addItem("Rectangle")
        root_widget.layoutComboBox.addItem("Triangle")
        root_widget.layoutComboBox.addItem("Hexagon")
        root_widget.layoutComboBox.addItem("Trapezoid")
