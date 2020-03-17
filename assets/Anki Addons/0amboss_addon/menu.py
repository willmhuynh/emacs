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


from PyQt5.QtWidgets import QMenu
from anki.hooks import addHook, remHook

from .shared import AMBOSS_LOGIN_HOOK, AMBOSS_LOGOUT_HOOK
from .login import LoginDialog, LogoutDialog, LoginHandler
from .shared import ANKI_PROFILE_LOADED_HOOK, ANKI_PROFILE_UNLOADED_HOOK
from .reviewer import ReviewerCardPhraseUpdater
from .profile import ProfileAdapter
from .about import AboutDialog


# TODO: don't consume global state/functions for hooks and message prompts


class Menu(QMenu):
    """Menu object in a menu bar. Note that aboutText cannot contain 'about', for some reason."""

    def __init__(
        self,
        label: str,
        loginText: str,
        logoutText: str,
        aboutText: str,
        toggleActiveText: str,
        toggleQuestionText: str,
        *args
    ):
        super().__init__(label, *args)
        self.toggleActiveAction = self.addAction(toggleActiveText)
        self.toggleActiveAction.setCheckable(True)
        self.toggleQuestionAction = self.addAction(toggleQuestionText)
        self.toggleQuestionAction.setCheckable(True)
        self.toggleSeparator = self.addSeparator()
        self.loginAction = self.addAction(loginText)
        self.logoutAction = self.addAction(logoutText)
        self.addSeparator()
        self.aboutAction = self.addAction(aboutText)


class MenuHandler:
    """Adds Menu to menu bar and handles its actions."""

    def __init__(
        self,
        mainWindow,
        menu: Menu,
        loginDialog: LoginDialog,
        logoutDialog: LogoutDialog,
        aboutDialog: AboutDialog,
        loginHandler: LoginHandler,
        profile: ProfileAdapter,
        reviewerCardPhraseUpdater: ReviewerCardPhraseUpdater,
    ):
        self._mainWindow = mainWindow
        self._menu = menu
        self._loginDialog = loginDialog
        self._logoutDialog = logoutDialog
        self._aboutDialog = aboutDialog
        self._loginHandler = loginHandler
        self._profile = profile
        self._reviewerCardPhraseUpdater = reviewerCardPhraseUpdater
        addHook(ANKI_PROFILE_LOADED_HOOK, self._updateMenuState)

    def setup(self):
        self._setupMenu()
        self._onLogoutHook()  # set default menu state to logged out
        self._addHooks()

    def _setupMenu(self):
        self._mainWindow.form.menubar.addMenu(self._menu)
        self._menu.loginAction.triggered.connect(self._loginClicked)
        self._menu.logoutAction.triggered.connect(self._logoutClicked)
        self._menu.aboutAction.triggered.connect(self._aboutClicked)
        self._menu.toggleActiveAction.triggered.connect(self._toggleActiveClicked)
        self._menu.toggleQuestionAction.triggered.connect(self._toggleQuestionClicked)

    def _updateMenuState(self):
        self._menu.toggleActiveAction.setChecked(self._profile.highlights)
        self._menu.toggleQuestionAction.setDisabled(not self._profile.highlights)
        self._menu.toggleQuestionAction.setChecked(self._profile.questionHighlights)

    def _addHooks(self):
        addHook(AMBOSS_LOGIN_HOOK, self._onLoginHook)
        addHook(AMBOSS_LOGOUT_HOOK, self._onLogoutHook)
        addHook(ANKI_PROFILE_UNLOADED_HOOK, self._destroyHooks)

    def _destroyHooks(self):
        remHook(AMBOSS_LOGIN_HOOK, self._onLoginHook)
        remHook(AMBOSS_LOGOUT_HOOK, self._onLogoutHook)

    def _onLoginHook(self):
        self._menu.toggleActiveAction.setVisible(True)
        self._menu.toggleQuestionAction.setVisible(True)
        self._menu.toggleSeparator.setVisible(True)
        self._menu.loginAction.setVisible(False)
        self._menu.logoutAction.setVisible(True)

    def _onLogoutHook(self):
        self._menu.toggleActiveAction.setVisible(False)
        self._menu.toggleQuestionAction.setVisible(False)
        self._menu.toggleSeparator.setVisible(False)
        self._menu.loginAction.setVisible(True)
        self._menu.logoutAction.setVisible(False)

    def _loginClicked(self):
        self._loginDialog.showLogin()

    def _logoutClicked(self):
        if self._logoutDialog.confirmed():
            self._loginHandler.logout()

    def _aboutClicked(self):
        self._aboutDialog.show()

    def _toggleActiveClicked(self, checked):
        self._profile.highlights = checked
        self._reviewerCardPhraseUpdater.toggleHighlights(checked)
        self._menu.toggleQuestionAction.setDisabled(not checked)

    def _toggleQuestionClicked(self, checked):
        self._profile.questionHighlights = checked
        self._reviewerCardPhraseUpdater.toggleHighlights(checked)
