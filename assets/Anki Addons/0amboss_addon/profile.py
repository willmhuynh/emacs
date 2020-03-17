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

import uuid
from typing import Optional

from anki.hooks import runHook
from .shared import AMBOSS_FIRSTRUN_HOOK, AMBOSS_LOGIN_HOOK, AMBOSS_LOGOUT_HOOK

AMBOSS_ID = "ambossId"
ANON_ID = "anonId"
AMBOSS_TOKEN = "ambossToken"
AMBOSS_HIGHLIGHTS = "ambossHighlights"
AMBOSS_QUESTION_HIGHLIGHTS = "ambossQuestionHighlights"


class ProfileAdapter:
    def __init__(self, profileManager):
        self._profileManager = profileManager
        # Defer loading Anki profile as it's not available at program start
        self._profile = {}

    @property
    def token(self) -> Optional[str]:
        return self._profile.get(AMBOSS_TOKEN)

    @property
    def id(self) -> Optional[str]:
        return self._profile.get(AMBOSS_ID)

    @property
    def anonId(self) -> str:
        anonId = self._profile.get(ANON_ID)
        if not anonId:
            anonId = str(uuid.uuid4())
            self.anonId = anonId
        return anonId

    @property
    def highlights(self) -> bool:
        return self._profile.get(AMBOSS_HIGHLIGHTS, True)

    @property
    def questionHighlights(self) -> bool:
        return self._profile.get(AMBOSS_QUESTION_HIGHLIGHTS, True)

    @token.setter
    def token(self, token: Optional[str]) -> None:
        self._profile[AMBOSS_TOKEN] = token

    @id.setter
    def id(self, id: Optional[str]) -> None:
        self._profile[AMBOSS_ID] = id

    @anonId.setter
    def anonId(self, id: Optional[str]) -> None:
        self._profile[ANON_ID] = id

    @highlights.setter
    def highlights(self, state: bool) -> None:
        self._profile[AMBOSS_HIGHLIGHTS] = state

    @questionHighlights.setter
    def questionHighlights(self, state: bool) -> None:
        self._profile[AMBOSS_QUESTION_HIGHLIGHTS] = state

    def onProfileLoadedHook(self) -> None:
        self._profile = self._profileManager.profile
        if AMBOSS_TOKEN not in self._profileManager.profile:
            runHook(AMBOSS_FIRSTRUN_HOOK)
            return
        if self.token:
            runHook(AMBOSS_LOGIN_HOOK)
            return
        runHook(AMBOSS_LOGOUT_HOOK)
