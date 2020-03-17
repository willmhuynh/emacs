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
Handles user authentication.
"""

import json

from aqt.qt import *
from aqt.utils import askUser
from anki.hooks import addHook, runHook
from .graphql import GraphQLClient
from .compat import VersionCheckResult
from .web import WebView

from .profile import ProfileAdapter
from .shared import (
    AMBOSS_LOGIN_HOOK,
    AMBOSS_LOGOUT_HOOK,
    AMBOSS_FIRSTRUN_HOOK,
    ANKI_PROFILE_LOADED_HOOK,
)


class LoginHandler:
    def __init__(self, graphQlClient: GraphQLClient, profile: ProfileAdapter, reviewer):
        self._graphQlClient = graphQlClient
        self._profile = profile
        self._reviewer = reviewer
        addHook(AMBOSS_LOGIN_HOOK, self._onUpdateHook)
        addHook(AMBOSS_LOGOUT_HOOK, self._onUpdateHook)
        addHook(ANKI_PROFILE_LOADED_HOOK, self._profile.onProfileLoadedHook)

    def login(self, id: str, token: str) -> None:
        self._profile.token = token
        self._profile.id = id
        runHook(AMBOSS_LOGIN_HOOK)

    def logout(self) -> None:
        self._profile.token = None
        self._profile.id = None
        runHook(AMBOSS_LOGOUT_HOOK)

    def identifyScript(self) -> str:
        return f"""
        if (
          window.analytics &&
          (!window.analytics.user ||
            (!window.analytics.user().id() || window.analytics.user().id() != '{self._profile.id}'))
        ) {{
          window.analytics.identify('{self._profile.id}');
        }}"""

    def _onUpdateHook(self) -> None:
        self._graphQlClient.setToken(self._profile.token)
        self._reviewer.web.eval(self.identifyScript())


class LoginDialog(QDialog):
    def __init__(
        self,
        mainWindow,
        title: str,
        webServer,
        loginFilePath: str,
        webView: WebView,
        graphQlUri: str,
        profileAdapter: ProfileAdapter,
        versionCheckResult: VersionCheckResult,
        addonVersion: str,
        *args,
        **kwargs,
    ):
        super().__init__(parent=mainWindow, *args, **kwargs)
        self._webServer = webServer
        self._title = title
        self._loginFilePath = loginFilePath
        self._layout = QVBoxLayout(self)
        self._webView = webView
        self._graphQlUri = graphQlUri
        self._profileAdapter = profileAdapter
        self._versionCheckResult = versionCheckResult
        self._addonVersion = addonVersion
        self._setup()
        addHook(AMBOSS_FIRSTRUN_HOOK, self.showLogin)

    def showLogin(self) -> None:
        self._webView.load(
            QUrl(
                f"http://localhost:{self._webServer.getPort()}/{self._loginFilePath}?"
                f"ankiVersion={self._versionCheckResult.current}&addonVersion={self._addonVersion}"
            )
        )
        self.exec_()

    def onDomDone(self) -> None:
        """
        Fired by LoginLinkHandler instance once domDone reached.
        """
        self._analytics()
        self._webView.eval(f"setupLoginHandler({json.dumps(self._graphQlUri)});")
        if not self._versionCheckResult.satisfied:
            self._webView.eval(
                f"showVersionWarning({json.dumps(self._versionCheckResult._asdict())});"
            )

    def _setup(self) -> None:
        self._layout.addWidget(self._webView)  # signature broken?
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.resize(500, 600)
        self.setWindowTitle(self._title)

    def _analytics(self):
        anonId = self._profileAdapter.anonId
        anonStr = f"""window.analytics.setAnonymousId("{anonId}");""" if anonId else ""
        viewStr = f"""window.analytics.track("anki-addon.login.view");"""
        analyticsStr = f"""if (window.analytics) {{{anonStr} {viewStr}}};"""
        self._webView.eval(analyticsStr)


class LogoutDialog:
    def __init__(self, mainWindow, title: str, text: str):
        self._mainWindow = mainWindow
        self._title = title
        self.text = text

    def confirmed(self) -> bool:
        # TODO: don't use global function that assumes Anki context
        return askUser(
            self.text, title=self._title, parent=self._mainWindow, defaultno=True
        )
