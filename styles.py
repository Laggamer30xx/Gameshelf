class Style:
    def __init__(self):
        pass

    @staticmethod
    def get_dark_stylesheet():
        return """
            QWidget {
                background-color: #2e2e2e;
                color: #ffffff;
            }
            QMainWindow {
                background-color: #2e2e2e;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QMenuBar::item {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #5a5a5a;
            }
            QMenu {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #5a5a5a;
            }
            QMenu::item:selected {
                background-color: #5a5a5a;
            }
        """

    @staticmethod
    def get_light_stylesheet():
        return """
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
            }
            QMenuBar {
                background-color: #e0e0e0;
                color: #000000;
            }
            QMenuBar::item {
                background-color: #e0e0e0;
                color: #000000;
            }
            QMenuBar::item:selected {
                background-color: #c0c0c0;
            }
            QMenu {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #c0c0c0;
            }
            QMenu::item:selected {
                background-color: #c0c0c0;
            }
        """
