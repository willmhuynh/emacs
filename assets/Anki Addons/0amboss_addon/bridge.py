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


import json

from aqt.utils import openLink

from .debug import ErrorPromptFactory
from .reviewer import ReviewerTooltipUpdater
from .login import LoginHandler, LoginDialog

AMBOSS_LINK_PREFIX = "amboss"


class ReviewerLinkHandler:
    """Handles hijacked AMBOSS specific Anki reviewer bridge links."""

    def __init__(self, reviewerTooltipUpdater: ReviewerTooltipUpdater):
        self._reviewerTooltipUpdater = reviewerTooltipUpdater

    def __call__(self, cmd, payload):
        if cmd == "tooltip":
            payload = json.loads(payload)
            self._reviewerTooltipUpdater.updateTooltip(payload)


class LoginLinkHandler:
    """Handles all login bridge links."""

    def __init__(self, loginHandler: LoginHandler, loginDialog: LoginDialog, onDomDone):
        self._loginHandler = loginHandler
        self._loginDialog = loginDialog
        self._onDomDone = onDomDone

    def __call__(self, url, *args):
        if url.lower().startswith("http"):
            return openLink(url)
        elif url == "domDone":
            self._onDomDone()
            return False
        elif not url.startswith(AMBOSS_LINK_PREFIX):
            return True
        _, cmd, *data = url.split(":")
        if cmd == "login" and len(data) >= 2:
            userId, token = data[0], data[1]
            self._loginHandler.login(userId, token)
        elif cmd == "close":
            self._loginDialog.accept()
        return False


class AboutLinkHandler:
    def __init__(self, errorPromptFactory: ErrorPromptFactory):
        self._errorPromptFactory = errorPromptFactory

    def __call__(self, url, *args):
        if url.lower().startswith("http"):
            return openLink(url)
        elif not url.startswith(AMBOSS_LINK_PREFIX):
            return True
        _, cmd, *args = url.split(":")
        if cmd == "debug":
            self._errorPromptFactory.create(
                None,
                "Something isn't working like you expected?",
                "AMBOSS - Debug"
            )
