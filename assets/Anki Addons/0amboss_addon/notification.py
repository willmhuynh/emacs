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
import time
from functools import lru_cache
from typing import Optional

import requests

from .shared import TokenAuth


class ServerNotificationService:
    # TODO: refactor + reuse

    _userAgent = "anki-addon"

    def __init__(
        self,
        uri: str,
        tokenAuth: TokenAuth,
        pollingInterval: int,
        requestTimeout: int,
        addonVersion: str,
        ankiVersion: str,
    ):
        self._uri = uri
        self._tokenAuth = tokenAuth
        self._pollingInterval = pollingInterval
        self._requestTimeout = requestTimeout
        self._addonVersion = addonVersion
        self._ankiVersion = ankiVersion

    def getServerNotification(self) -> Optional[str]:
        return self._getServerNotificationCached(self._getTtlHash())

    @lru_cache(maxsize=1)
    def _getServerNotificationCached(self, _hash=None):
        response = requests.request(
            "POST",
            self._uri,
            data=json.dumps(
                {"addon_version": self._addonVersion, "ankiVersion": self._ankiVersion}
            ),
            timeout=self._requestTimeout,
            headers={
                **{"Content-Type": "application/json", "User-Agent": self._userAgent},
                **self._tokenAuth.header,
            },
        )
        # TODO: inform client about failed request... with a notification?
        if response.status_code != 200:
            return None
        try:
            response = json.loads(response.content)
        except ValueError:
            return None
        return response.get("notification")

    def _getTtlHash(self):
        return round(time.time() / self._pollingInterval)
