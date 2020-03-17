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


from typing import Callable

from aqt.utils import openLink
from aqt.webview import AnkiWebPage, AnkiWebView


class Page(AnkiWebPage):
    def acceptNavigationRequest(self, url, navType, isMainFrame) -> bool:
        if url.host() == "localhost":
            return True
        openLink(url)
        return False

    def setBridgeCommand(self, bridgeCommand: Callable) -> None:
        self._onBridgeCmd = bridgeCommand


class WebView(AnkiWebView):
    def __init__(self, loginPage: Page, parent=None):
        super().__init__(parent)
        self.setPage(loginPage)
