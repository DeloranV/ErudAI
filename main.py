import asyncio
import os
import sys

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from view import ChatDialog
import qasync

async def main(app):
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    chat_dialog = ChatDialog()
    chat_dialog.show()

    stylesheet_path = os.path.join('view', 'static', 'style.qss')
    with open(stylesheet_path, 'r') as stylesheet_file:
        _style = stylesheet_file.read()
        chat_dialog.setStyleSheet(_style)

    await app_close_event.wait()

if __name__ == "__main__":
    directory = "logs"

    os.makedirs(directory, exist_ok=True)
    app = QApplication(sys.argv)

    asyncio.run(main(app), loop_factory=QEventLoop)