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


from typing import NamedTuple
from packaging.version import parse as parseVersion


class VersionCheckResult(NamedTuple):
    current: str
    minimum: str
    maximum: str
    satisfied: bool


class VersionChecker:
    @classmethod
    def check(cls, current: str, minimum: str, maximum: str = None) -> bool:
        """Checks whether specified version is in specified range
        
        :param current: current version
        :type current: str
        :param minimum: minimum version (inclusive)
        :type minimum: str
        :param maximum: maximum version (exclusive), defaults to None
        :type maximum: str, optional
        :return: Whether current version is in specified range
        :rtype: bool
        """
        if maximum is not None:
            current_parsed = parseVersion(current)
            return current_parsed >= parseVersion(
                minimum
            ) and current_parsed < parseVersion(maximum)
        else:
            return parseVersion(current) >= parseVersion(minimum)

    @classmethod
    def getResult(
        cls, current: str, minimum: str, maximum: str = None
    ) -> VersionCheckResult:
        satisfied = cls.check(current, minimum, maximum=maximum)
        return VersionCheckResult(
            current=current, minimum=minimum, maximum=maximum, satisfied=satisfied
        )
