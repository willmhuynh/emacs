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
Modifies Reviewer by injecting HTML and hijacking handlers.
"""
import json
import decorator
import time
from collections import OrderedDict
from typing import List, Callable, Optional

from PyQt5.QtCore import QThreadPool
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    SSLError,
    ProxyError,
    Timeout,
    ReadTimeout,
)
from urllib3.exceptions import ReadTimeoutError

from anki.hooks import addHook
from aqt.reviewer import Reviewer
from aqt.utils import tooltip as ankiTooltip

from .profile import ProfileAdapter
from .phrases import PhraseFinder
from .tooltip import TooltipRenderService
from .qthreading import Worker
from .debug import ErrorPromptFactory


AMBOSS_LINK_PREFIX = "amboss"


def wrap(old, new, self):
    # TODO: maybe put into a class, maybe as callable, at least don't assume argument name _old?
    """Override an existing method."""

    def decorator_wrapper(f, *args, **kwargs):
        return new(self, _old=old, *args, **kwargs)

    return decorator.decorator(decorator_wrapper)(old)


class ReviewerErrorHandler:
    def __init__(
        self,
        mainWindow,
        errorPromptFactory: ErrorPromptFactory,
        errorLifetime: int,
        connectionErrorInterval: int,
        timeoutErrorInterval: int,
    ):
        self._mainWindow = mainWindow
        self._errorPromptFactory = errorPromptFactory
        self._errorLifetime = errorLifetime
        self._connectionErrorInterval = connectionErrorInterval
        self._timeoutErrorInterval = timeoutErrorInterval
        self._lastConnectionErrorTime = 0
        self._lastTimeoutError = 0

    def __call__(self, exception: Exception):
        try:
            raise exception
        except (HTTPError, SSLError, ProxyError) as e:
            # TODO: handle HTTPError and Exception catch-all differently, e.g.
            # TODO: use HTTPError status code (e.response.status_code) to show different copy
            self._errorPromptFactory.create(
                e,
                "Encountered an error while trying to connect to AMBOSS",
                "Connection Error",
            )
        except ConnectionError:
            if (
                time.time() - self._lastConnectionErrorTime
            ) > self._connectionErrorInterval:
                ankiTooltip(
                    "Can't connect to AMBOSS.<br>Please check your internet connection.",
                    self._errorLifetime,
                )
                self._lastConnectionErrorTime = time.time()
        # TODO: improve handling of being offline vs. timing out because of bad connection
        # TODO: also ssl.py re-raises SSLError sometimes that is really a timeout
        except (Timeout, TimeoutError, ReadTimeout, ReadTimeoutError):
            if (time.time() - self._lastTimeoutError) > self._timeoutErrorInterval:
                ankiTooltip(
                    "Connection to AMBOSS timed out.<br>Please check your internet connection.",
                    self._errorLifetime,
                )
                self._lastTimeoutError = time.time()
        except (HTTPError, Exception) as e:
            self._errorPromptFactory.create(e)


class ReviewerScheduleService:
    def __init__(self, reviewer: Reviewer):
        self._reviewer = reviewer

    def getUpcomingCardIds(self) -> List[int]:
        sched = self._reviewer.mw.col.sched
        cids = []
        if not sched._haveQueues:
            return cids

        # There is no clear-cut queue of upcoming cards because the scheduler
        # draws up the next card on demand. So instead we iterate through
        # all individual queues and pick one candidate each

        lrnQueue = getattr(sched, "_lrnQueue", None)
        if lrnQueue:
            cids.append(lrnQueue[0][1])  # heap of tuples (due, cid)

        for queueName in ("_lrnDayQueue", "_revQueue", "_newQueue"):
            # misnomer: these are actually stacks of cids
            queue = getattr(sched, queueName, None)
            if not queue:
                continue
            try:
                cids.append(queue[-1])
            except IndexError:
                continue

        return cids


class ReviewerCardPhraseUpdater:
    """Updates card DOM with new phrase markers on reviewer changes."""

    def __init__(
        self,
        reviewer: Reviewer,
        phraseFinder: PhraseFinder,
        scheduleService: ReviewerScheduleService,
        threadPool: QThreadPool,
        errorHandler: ReviewerErrorHandler,
        profile: ProfileAdapter,
    ):
        self._reviewer = reviewer
        self._phraseFinder = phraseFinder
        self._scheduleService = scheduleService
        self._threadPool = threadPool
        self._errorHandler = errorHandler
        self._profile = profile

    def registerHooks(self):
        """Adds user hooks triggered when question or answer is shown."""
        addHook("showQuestion", self._onCardUpdated)
        addHook("showAnswer", self._onCardUpdated)

    def _onCardUpdated(self):
        """Fires when card content is updated and marks found phrases."""
        if not self._profile.highlights or (
            self._reviewer.state == "question" and not self._profile.questionHighlights
        ):
            return

        self._dispatchWorker(
            self._reviewer.card.note(), self._findPhrasePairs, self._markPhrases
        )
        # cache upcoming notes, one out of each queue
        for cardId in self._scheduleService.getUpcomingCardIds():
            self._dispatchWorker(
                self._reviewer.mw.col.getCard(cardId).note(), self._cachePhrasePairs
            )

    def _dispatchWorker(
        self, note, workerCallback: Callable, resultCallback: Optional[Callable] = None
    ):
        worker = Worker(
            workerCallback,
            tuple(field.strip() for field in note.fields if field.strip()),
            note.guid,
        )
        if resultCallback:
            worker.signals.result.connect(resultCallback)
        worker.signals.error.connect(self._errorHandler)
        self._threadPool.start(worker)

    def _cachePhrasePairs(self, fields: tuple, guid: str):
        # relies on getPhrases lru_cache
        self._phraseFinder.getPhrases(fields, guid)

    def _findPhrasePairs(self, fields: tuple, guid: str) -> dict:
        phrases = self._phraseFinder.getPhrases(fields, guid)
        phrasePairs = {
            term: phrase.groupId
            for term, phrase in phrases.items()
            if phrase is not None
        }
        return phrasePairs

    def _markPhrases(self, phrasePairs: dict, cancelled: bool):
        if cancelled:
            return
        elif not self._reviewer or self._reviewer.mw.state != "review":
            return
        self._reviewer.web.eval(
            f"ambossMarker.mark({json.dumps(self._sort(phrasePairs))})"
        )
    
    def toggleHighlights(self, state: bool):
        if self._reviewer.state not in ("question", "answer"):
            # abort if triggered outside of review session
            return
        if not state:
            self._reviewer.web.eval("""
                ambossMarker.hideAll();
                ambossTooltips.hideAll();
            """)
        else:
            self._onCardUpdated()

    def _sort(self, phrasePairs: dict) -> OrderedDict:
        """Order phrase pairs by descending phrase key length."""
        return OrderedDict(sorted(phrasePairs.items(), key=lambda k: -len(k[0])))


class ReviewerTooltipUpdater:
    """Updates tippy tooltips with new tooltip content"""

    def __init__(
        self,
        reviewer: Reviewer,
        tooltipRenderService: TooltipRenderService,
        threadPool: QThreadPool,
        errorHandler: ReviewerErrorHandler,
    ):
        self._reviewer = reviewer
        self._tooltipService = tooltipRenderService
        self._threadPool = threadPool
        self._errorHandler = errorHandler
        self._worker = None

    def updateTooltip(self, tippyData: dict):
        phraseGroupId = tippyData["phraseId"]
        foundTerm = tippyData["term"]
        markId = tippyData["markId"]
        self._worker = Worker(self._renderTooltip, phraseGroupId, foundTerm)
        self._worker.signals.result.connect(
            lambda t, c: self._updateTooltip(markId, t, c)
        )
        self._worker.signals.error.connect(self._errorHandler)
        self._threadPool.start(self._worker)

    def _renderTooltip(self, phraseGroupId, foundTerm):
        return self._tooltipService.renderTooltip(phraseGroupId, foundTerm)

    def _updateTooltip(self, markId, tooltip, cancelled):
        if not self._reviewer or self._reviewer.mw.state != "review":
            return
        self._reviewer.web.eval(
            f"ambossTooltips.setContentFor({json.dumps(markId)}, {json.dumps(tooltip)})"
        )
        # TODO: really dumb, if time fix MutationObserver implementation
        if "amboss-card-client-notification-access-expired" in tooltip:
            self._reviewer.web.eval(
                "try { accessExpired() } catch(error) { console.error(error) }"
            )
