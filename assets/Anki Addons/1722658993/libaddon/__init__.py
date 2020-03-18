# -*- coding: utf-8 -*-

# Libaddon for Anki
#
# Copyright (C) 2018-2019  Aristotelis P. <https//glutanimate.com/>
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
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

"""
Libaddon: A helper library for Anki add-on development

Provides access to a number of commonly used modules shared across
many of my add-ons.

Please note that this package is not fit for general use yet, as it is
still is too specific to my own add-ons and implementations.

This module is the package entry-point.
"""

from ._version import __version__  # noqa: F401

def registerLegacyVendorDir():
    """Some modules like "typing" cannot be properly vendorized, so fall back
    to hacky sys.path modifications if necessary
    NOTE: make sure not to use vendored legacy dependencies before running this
    """
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "_vendor_legacy"))
