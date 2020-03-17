# AMBOSS Anki Add-on
#
# Copyright (C) 2019 AMBOSS MD Inc. <https://www.amboss.com/us>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QDialog, QVBoxLayout

from .web import WebView


class AboutDialog(QDialog):
    def __init__(
        self,
        mainWindow,
        title: str,
        webServer,
        aboutFilePath: str,
        webView: WebView,
        version: str,
        *args,
        **kwargs,
    ):
        super().__init__(parent=mainWindow, *args, **kwargs)
        self._webServer = webServer
        self._title = title
        self._aboutFilePath = aboutFilePath
        self._layout = QVBoxLayout(self)
        self._webView = webView
        self._version = version
        self._setup()

    def show(self) -> None:
        self._webView.load(
            QUrl(
                f"http://localhost:{self._webServer.getPort()}/{self._aboutFilePath}?version={self._version}"
            )
        )
        self.exec_()

    def _setup(self) -> None:
        self._layout.addWidget(self._webView)  # signature broken
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.resize(480, 360)
        self.setWindowTitle(self._title)
