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


import os
import sys
import re
import atexit

from aqt import mw
from anki import version as ankiVersion

MODULE = __name__.split(".")[0]
ADDON_PATH = os.path.join(mw.pm.addonFolder(), MODULE)

sys.path.insert(0, os.path.join(ADDON_PATH, "_vendor"))

from ._vendor.dotenv import load_dotenv

from .compat import VersionChecker

from .tooltip import (
    TooltipDestinationLabelFactory,
    PhraseTooltipMapper,
    PhraseGroupTooltipMapper,
    TooltipFactory,
    TooltipRenderer,
    TooltipService,
    TooltipRenderService,
    TooltipUTMFactory,
)
from .phrases import (
    PhraseMapper,
    DestinationMapper,
    PhraseGroupMapper,
    PhraseFinderClient,
    PhraseRepository,
    PhraseFinder,
    PhraseGroupResolver,
)
from .graphql import GraphQLClient
from .shared import BasicAuth, TokenAuth
from .profile import ProfileAdapter
from .login import LoginHandler, LoginDialog, LogoutDialog
from .menu import Menu, MenuHandler
from .reviewer import (
    ReviewerCardPhraseUpdater,
    ReviewerTooltipUpdater,
    ReviewerErrorHandler,
    ReviewerScheduleService,
)
from .bridge import ReviewerLinkHandler, LoginLinkHandler, AboutLinkHandler
from .patch import ReviewerLinkPatcher, ReviewerHTMLPatcher
from .debug import ErrorSubmitter, ErrorPromptFactory, DebugService
from .about import AboutDialog
from .web import Page, WebView
from .notification import ServerNotificationService

import sentry_sdk
from PyQt5.QtCore import QThreadPool

from ._version import __version__

# Make vendorized packages available to importer
# Prepares and registers web elements with Anki.
# Bypasses Anki's security policy to enable loading of our web elements.
sep = re.escape(os.path.sep)  # TODO?: Drop the subpath limitation?
mw.addonManager.setWebExports(__name__, f"web{sep}.*")

# Environment

if os.path.isfile(os.path.join(ADDON_PATH, ".env")):
    load_dotenv(dotenv_path=os.path.join(ADDON_PATH, ".env"))
else:
    load_dotenv(dotenv_path=os.path.join(ADDON_PATH, ".env.dist"))

# Properties

recommendedAnkiVersion = "2.1.15"
menuLabel = "AMBOSS"
menuLoginText = "Log in..."
menuLogoutText = "Log out..."
menuAboutText = "A​bout"  # CAVE: contains invisible space - for some reason, string cannot contain 'about'
menuToggleActiveText = "Enable pop-up definitions"
menuToggleQuestionText = "Show pop-up definitions on questions"
loginDialogTitle = "AMBOSS - Login"
logoutDialogTitle = "AMBOSS - Logout"
logoutDialogText = """Are you sure you want to log out?
By doing so, you'll lose access to all of AMBOSS' add-on features."""
aboutDialogTitle = "AMBOSS - About"
graphQlUri = os.environ.get("AMBOSS_GRAPHQL_URI") or "https://content-gateway.us.production.amboss.com"
restPhraseUri = (
    os.environ.get("AMBOSS_RESTPHRASE_URI")
    or "https://anki.production.amboss.com/anki_evaluate_flashcard/us/v1/"
)
serverNotificationUri = (
    os.environ.get("AMBOSS_NOTIFICATION_URI")
    or "https://anki.production.amboss.com/us/v1/notification/"
)
ambossLibraryUri = (
    os.environ.get("AMBOSS_LIBRARY_URI") or "https://www.amboss.com/us/library"
)
loginFilePath = f"_addons/{MODULE}/web/login.html"
aboutFilePath = f"_addons/{MODULE}/web/about.html"
basicAuthUser = os.environ.get("AMBOSS_BASIC_USER")
basicAuthPass = os.environ.get("AMBOSS_BASIC_PASS")
timeout = os.environ.get("AMBOSS_TIMEOUT") or 10
feedbackUri = (
    os.environ.get("AMBOSS_FEEDBACK_URI")
    or "https://docs.google.com/forms/d/e/1FAIpQLSe6CNC3XIvqs9nhZ93OevEEbAUR-XKQHcmk74BSN7gD5buKEg/viewform"
)
supportUri = (
    os.environ.get("AMBOSS_SUPPORT_URI") or "https://www.amboss.com/us/anki-amboss"
)
storeUri = os.environ.get("AMBOSS_STORE_URI") or "https://www.amboss.com/us/store"
sentryDsn = (
    os.environ.get("AMBOSS_SENTRY_DSN")
    or "https://39cc2d0c71fd43d3ae1c19607c7b6937:ab93eecf0e054b429d07c61f13307665@sentry.miamed.de/31"
)
serverNotificationPollingInterval = int(
    os.environ.get("AMBOSS_NOTIFICATION_POLLING_INTERVAL") or 300
)

# Sentry

# TODO: possibly enable always based on env vars or user-set config
# sentry_sdk.init(sentryDsn, release=__version__, attach_stacktrace=True, with_locals=True)
atexit.register(sentry_sdk.flush)

# Shared

basicAuth = BasicAuth(user=basicAuthUser, password=basicAuthPass)
tokenAuth = TokenAuth(basicAuth)

# ThreadPool

threadPool = QThreadPool.globalInstance()

# GraphQL

graphQlClient = GraphQLClient(graphQlUri, tokenAuth, timeout)

# Phrases

phraseMapper = PhraseMapper()
destinationMapper = DestinationMapper()
phraseGroupMapper = PhraseGroupMapper(destinationMapper)
phraseFinderClient = PhraseFinderClient(restPhraseUri, tokenAuth, timeout)
phraseRepository = PhraseRepository()
phraseFinder = PhraseFinder(phraseFinderClient, phraseRepository, phraseMapper)
phraseGroupResolver = PhraseGroupResolver(graphQlClient, phraseGroupMapper)

# Version

versionCheckResult = VersionChecker.getResult(ankiVersion, recommendedAnkiVersion)

# Login

profileAdapter = ProfileAdapter(mw.pm)
loginHandler = LoginHandler(graphQlClient, profileAdapter, mw.reviewer)
loginPage = Page(lambda *args, **kwargs: None)  # bridge command set in later step
loginWebView = WebView(loginPage)
loginDialog = LoginDialog(
    mw,
    loginDialogTitle,
    mw.mediaServer,
    loginFilePath,
    loginWebView,
    graphQlUri,
    profileAdapter,
    versionCheckResult,
    __version__,
)
logoutDialog = LogoutDialog(mw, logoutDialogTitle, logoutDialogText)

# About

aboutPage = Page(lambda *args, **kwargs: None)
aboutWebView = WebView(aboutPage)
aboutDialog = AboutDialog(
    mw, aboutDialogTitle, mw.mediaServer, aboutFilePath, aboutWebView, __version__
)

# Debug

debugService = DebugService(mw)
errorSubmitter = ErrorSubmitter(profileAdapter, sentryDsn, __version__)
errorPromptFactory = ErrorPromptFactory(mw, debugService, errorSubmitter)

# Notification

serverNotificationService = ServerNotificationService(
    serverNotificationUri,
    tokenAuth,
    serverNotificationPollingInterval,
    timeout,
    __version__,
    ankiVersion,
)

# Tooltip

phraseTooltipMapper = PhraseTooltipMapper()
tooltipUtmFactory = TooltipUTMFactory(profileAdapter)
phraseGroupTooltipMapper = PhraseGroupTooltipMapper(tooltipUtmFactory, storeUri)
tooltipFactory = TooltipFactory(phraseTooltipMapper, phraseGroupTooltipMapper)
tooltipDestinationLabelFactory = TooltipDestinationLabelFactory()
tooltipRenderer = TooltipRenderer(
    tooltipDestinationLabelFactory,
    debugService,
    ambossLibraryUri,
    supportUri,
    feedbackUri,
    tooltipUtmFactory,
)
tooltipService = TooltipService(
    phraseRepository, phraseGroupResolver, tooltipFactory, serverNotificationService
)
tooltipRenderService = TooltipRenderService(
    tooltipService, tooltipRenderer, mw.reviewer
)

# Reviewer

reviewerHtmlPatcher = ReviewerHTMLPatcher(
    f"/_addons/{MODULE}/web",
    (
        "js/analytics.js",
        "js/popper.js",
        "js/tippy.js",
        "js/mark.es6.min.js",
        "js/tooltip.js",
    ),
    (
        "css/global.css",
        "css/tippy.css",
        "css/highlight.css",
        "css/tooltip.css",
        "css/tooltip-beta.css",
    ),
    (
        loginHandler.identifyScript,
        lambda: f"""ankiVersion="{ankiVersion}";"""
        f"""addonVersion="{__version__}";""",
    ),
)
reviewerErrorHandler = ReviewerErrorHandler(mw, errorPromptFactory, 3000, 300, 60)
reviewerScheduleService = ReviewerScheduleService(mw.reviewer)
reviewerCardPhraseUpdater = ReviewerCardPhraseUpdater(
    mw.reviewer,
    phraseFinder,
    reviewerScheduleService,
    threadPool,
    reviewerErrorHandler,
    profileAdapter,
)
reviewerTooltipUpdater = ReviewerTooltipUpdater(
    mw.reviewer, tooltipRenderService, threadPool, reviewerErrorHandler
)
reviewerCardPhraseUpdater.registerHooks()

# Bridge

reviewerLinkHandler = ReviewerLinkHandler(reviewerTooltipUpdater)  # TODO: fix
reviewerLinkPatcher = ReviewerLinkPatcher(reviewerLinkHandler)
reviewerLinkPatcher.patchOnHook("profileLoaded")
loginLinkHandler = LoginLinkHandler(loginHandler, loginDialog, loginDialog.onDomDone)
aboutLinkHandler = AboutLinkHandler(errorPromptFactory)
loginPage.setBridgeCommand(loginLinkHandler)
aboutPage.setBridgeCommand(aboutLinkHandler)

# Menu

menu = Menu(
    menuLabel,
    menuLoginText,
    menuLogoutText,
    menuAboutText,
    menuToggleActiveText,
    menuToggleQuestionText,
)
menuHandler = MenuHandler(
    mw,
    menu,
    loginDialog,
    logoutDialog,
    aboutDialog,
    loginHandler,
    profileAdapter,
    reviewerCardPhraseUpdater,
)
menuHandler.setup()

# Reviewer

reviewerHtmlPatcher.patch()
reviewerLinkPatcher.patchOnHook("profileLoaded")
reviewerCardPhraseUpdater.registerHooks()
