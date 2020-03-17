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


import base64
from collections import namedtuple

AMBOSS_LOGIN_HOOK = "ambossLogin"
AMBOSS_LOGOUT_HOOK = "ambossLogout"
AMBOSS_FIRSTRUN_HOOK = "ambossFirstrun"
ANKI_PROFILE_LOADED_HOOK = "profileLoaded"
ANKI_PROFILE_UNLOADED_HOOK = "unloadProfile"

# DTO for basic authentication.
BasicAuth = namedtuple("BasicAuth", ["user", "password"])


class TokenAuth:
    """DTO holding token and basic auth credentials with authorization header representation."""

    def __init__(self, basicAuth: BasicAuth = None, token: str = None):
        assert basicAuth is None or type(basicAuth) is BasicAuth
        assert token is None or type(token) is str
        self.token = token
        self._basicAuth = basicAuth

    @property
    def header(self) -> dict:
        return {
            "Authorization": (
                "Basic "
                + base64.b64encode(
                    f"{self._basicAuth.user}:{self._basicAuth.password}".encode()
                ).decode()
                + ", "
                if type(self._basicAuth) is BasicAuth
                and (self._basicAuth.user or self._basicAuth.password)
                else ""
            )
            + f"Bearer {self.token}"
        }

    def isSet(self):
        return self.token is not None


def _sanitizeText(text):
    return text.encode("ascii", errors="xmlcharrefreplace").decode("ascii")


def safePrint(*args, **kwargs):
    """Temporary workaround for locale issues forcing ascii stdout"""
    try:
        return print(*args, **kwargs)
    except UnicodeEncodeError as e:
        try:
            new_args = [_sanitizeText(str(a)) for a in args]
            if "sep" in kwargs:
                kwargs["sep"] = _sanitizeText(kwargs["sep"])
            if "end" in kwargs:
                kwargs["end"] = _sanitizeText(kwargs["end"])
            print(*new_args, **kwargs)
        except:  # noqa: E722
            print("Error while trying to print.")
