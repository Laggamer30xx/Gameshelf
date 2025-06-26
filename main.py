import sys
from PyQt5.QtWidgets import QApplication
from gameshelf_ui import GameshelfUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameshelfUI()
    window.show()
    sys.exit(app.exec_())
