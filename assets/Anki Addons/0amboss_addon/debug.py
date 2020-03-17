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


"""
Based in parts on anki.utils (Copyright: Ankitects Pty Ltd and contributors)
"""

import os
import json
import ssl
import traceback
import html
from typing import Tuple, Optional

import certifi
import sentry_sdk

from .profile import ProfileAdapter
from .shared import safePrint

from sentry_sdk import capture_exception, capture_message, configure_scope
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTextBrowser,
    QDialogButtonBox,
    QApplication,
    QTextEdit,
    QLabel,
)

from aqt.utils import tooltip, showWarning


from ._version import __version__

ADDON_NAME = "AMBOSS"  # TODO: put this somewhere else


class ErrorSubmitter:
    def __init__(self, profile: ProfileAdapter, sentryDsn: str, version: str):
        self._profile = profile
        self._sentryDsn = sentryDsn
        self._version = version

    def submit(self, data: dict, exception: Optional[Exception]) -> bool:
        """
        Temporarily enables sentry integration to send error and then disables it again.
        """
        try:
            sentry_sdk.init(
                self._sentryDsn,
                release=self._version,
                attach_stacktrace=True,
                with_locals=True,
            )
            with configure_scope() as scope:
                scope.level = "error"
                scope.user = {"id": self._profile.id}
                if "debug" in data and type(data["debug"]) is dict:
                    for k, v in data["debug"].items():
                        scope.set_extra(k, v)
                if "message" in data:
                    scope.set_extra("message", data["message"])
            if isinstance(exception, Exception):
                capture_exception(exception)
            elif "message" in data:
                capture_message(data["message"], "error")
            sentry_sdk.flush()
            return True
        except Exception as e:
            # something went wrong
            safePrint(e)
            return False
        finally:
            # Calling init with empty string disables sentry again
            # Otherwise we would log other Anki exceptions
            sentry_sdk.init("")


class DebugInfo:
    """
    Utility class for gathering debug info on various aspects of our add-on and Anki
    """

    _reviewer_attrs = {
        "card": ("id",),
        "note": ("guid", "tags", "fields"),
        "model": ("name", "css"),
        "template": ("qfmt", "afmt"),
    }

    # all environment variables used by Anki that could be relevant to us
    _anki_env = (
        "ANKI_NOVERIFYSSL",
        "ANKI_BASE",
        "ANKI_NOHIGHDPI",
        "ANKI_SOFTWAREOPENGL",
        "ANKI_WEBSCALE",
        "DEBUG",
        "QT_XCB_FORCE_SOFTWARE_OPENGL",
        "QT_OPENGL",
    )

    _amboss_env = ("AMBOSS_GRAPHQL_URI", "AMBOSS_RESTPHRASE_URI", "AMBOSS_LIBRARY_URI")

    def __init__(self, mainWindow):
        self._mainWindow = mainWindow

    def all(self) -> dict:
        return {
            "amboss": self.amboss(),
            "anki": self.anki(),
            "reviewer": self.reviewer(),
            "addons": self.addons(),
        }

    def amboss(self) -> dict:
        return {
            "version": __version__,
            "env": self._getEnvironment(self._amboss_env),
        }

    def anki(self) -> dict:
        import platform
        import sys
        import locale
        from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        from anki.utils import versionWithBuild
        from anki.utils import isWin, isMac

        if isWin:
            platname = "Windows " + platform.win32_ver()[0]
        elif isMac:
            platname = "Mac " + platform.mac_ver()[0]
        else:
            platname = "Linux"

        def schedVer() -> str:
            try:
                return self._mainWindow.col.schedVer()
            except:
                return "?"

        return {
            "version": versionWithBuild(),
            "python": platform.python_version(),
            "qt": QT_VERSION_STR,
            "pyqt": PYQT_VERSION_STR,
            "platform": platname,
            "frozen": getattr(sys, "frozen", False),  # source build or binary build?
            "addonsLoaded": self._mainWindow.addonManager.dirty,
            "scheduler": schedVer(),
            "env": self._getEnvironment(self._anki_env),
            "locale": locale.getlocale(),
            "cacert": certifi.where(),
            "sslVersion": ssl.OPENSSL_VERSION,
        }

    def reviewer(self) -> Optional[dict]:
        reviewer = getattr(self._mainWindow, "reviewer", None)
        if not reviewer or not reviewer.card:
            return None

        card = reviewer.card
        note = card.note()
        template = card.template()
        model = card.model()

        data = {"deck": {"name": self._mainWindow.col.decks.nameOrNone(card.did)}}

        for (obj, obj_name) in (
            (card, "card"),
            (note, "note"),
            (template, "template"),
            (model, "model"),
        ):
            attrs = self._reviewer_attrs[obj_name]

            obj_data = {}

            for attr in attrs:
                if obj_name in ("template", "model"):
                    obj_data[attr] = obj.get(attr, None)
                else:
                    obj_data[attr] = getattr(obj, attr, None)

            data[obj_name] = obj_data

        data["model"]["flds"] = self._mainWindow.col.models.fieldNames(model)

        return data

    def addons(self) -> Optional[Tuple[str, ...]]:
        addonManager = getattr(self._mainWindow, "addonManager", None)
        if not addonManager:
            return None
        # annotated name provides us with info on activation state:
        return tuple(addonManager.annotatedName(d) for d in addonManager.allAddons())

    def _getEnvironment(self, names: Tuple[str, ...]) -> dict:
        return {name: os.environ.get(name, None) for name in names}


class DebugService:
    def __init__(self, mainWindow):
        self._mainWindow = mainWindow

    def getForMachine(self) -> dict:
        return DebugInfo(self._mainWindow).all()


class ErrorPromptFactory:
    _default_message = f"Encountered an unexpected error in the {ADDON_NAME} add-on"
    _default_title = f"Unexpected {ADDON_NAME} add-on error"

    def __init__(
        self, mainWindow, debugService: DebugService, errorSubmitter: ErrorSubmitter
    ):
        self._mainWindow = mainWindow
        self._debugService = debugService
        self._errorSubmitter = errorSubmitter

    def create(
        self, exception: Optional[Exception], message: str = None, title: str = None
    ):
        return ErrorPrompt(
            self._mainWindow,
            self._debugService,
            self._errorSubmitter,
            exception,
            message or self._default_message,
            title or self._default_title,
        )


class ErrorPrompt(QDialog):
    _json_indent = 4

    def __init__(
        self,
        mainWindow,
        debugService: DebugService,
        errorSubmitter: ErrorSubmitter,
        exception: Optional[Exception],
        message: str,
        title: str,
        parent=None,
        *args,
        **kwargs,
    ):
        parent = parent or mainWindow
        super().__init__(*args, parent=parent, **kwargs)
        self._mainWindow = mainWindow
        self._debugData = debugService.getForMachine()
        self._errorSubmitter = errorSubmitter
        self._exception = exception
        self._message = message
        self._title = title

        self.textBrowser = QTextBrowser(self)
        self.textEdit = QTextEdit(self)
        self.buttonBox = QDialogButtonBox(self)

        self._setupUI()
        self.exec_()

    def _setupUI(self):
        self.setWindowTitle(self._title)
        self.textBrowser.setHtml(self._composeHtml())

        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(
            QLabel(
                f"<h2>{self._message}</h2>"
                "Please consider using the \"Submit\" button below to let us know about the issue you encountered. "
                "Thanks!"
            )
        )
        self.layout().addWidget(self.textBrowser)
        self.layout().addWidget(QLabel("Please describe the issue you encountered:"))
        self.layout().addWidget(self.textEdit)
        self.layout().addWidget(self.buttonBox)

        submitButton = self.buttonBox.addButton(
            "Submit bug report", QDialogButtonBox.AcceptRole
        )
        closeButton = self.buttonBox.addButton(QDialogButtonBox.Close)
        copyButton = self.buttonBox.addButton(
            "Copy to clipboard", QDialogButtonBox.ActionRole
        )

        submitButton.clicked.connect(self._onSubmitButton)
        closeButton.clicked.connect(self.reject)
        copyButton.clicked.connect(self._onCopyButton)

        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

    def _composeHtml(self) -> str:
        return f"""
        {self._errorMessage()}
        {self._debugMessage()}
        """

    def _errorMessage(self) -> str:
        return (
            f"""
        <h3>Error message:</h3>
        <div style='white-space: pre-wrap; font-family: monospace; font-size: 10pt;'>
        <div>{html.escape(self._stringifyException(self._exception))}</div>
        </div>"""
            if isinstance(self._exception, Exception)
            else ""
        )

    def _debugMessage(self) -> str:
        return f"""
        <h3>Debug info:</h3>
        <div style='white-space: pre-wrap; font-family: monospace; font-size: 10pt;'>
        <div>{html.escape(json.dumps(self._debugData, indent=self._json_indent))}</div>
        </div>"""

    def _stringifyException(self, exception: Optional[Exception]):
        if not isinstance(exception, Exception):
            return "Debug"
        stringified = (
            f"{type(exception).__name__}: {exception}\n\n{traceback.format_exc()}"
        )
        safePrint(stringified)
        return stringified

    def _onCopyButton(self):
        QApplication.clipboard().setText(
            json.dumps(self._getSubmissionData(), indent=self._json_indent)
        )
        tooltip("Copied to clipboard", parent=self)

    def _getSubmissionData(self):
        return {
            "traceback": self._stringifyException(self._exception),
            "debug": self._debugData,
            "message": self.textEdit.toPlainText(),
        }

    def _onSubmitButton(self):
        self._mainWindow.progress.start(label="Submitting bug report...")
        ret = self._errorSubmitter.submit(self._getSubmissionData(), self._exception)
        self._mainWindow.progress.finish()

        if ret:
            tooltip("Successfully submitted bug report", parent=self._mainWindow)
            self.accept()
        else:
            showWarning(
                "Was not able to submit debug info. "
                "Please check your network connection and try again.\n\n"
                "Should things still not work, then please use the 'Copy' button to send us "
                "the error message directly. Thanks!",
                title="Error while submitting debug info",
                parent=self,
            )
