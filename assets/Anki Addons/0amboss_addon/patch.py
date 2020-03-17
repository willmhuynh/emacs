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


from aqt.reviewer import Reviewer
from anki.hooks import addHook
from .bridge import ReviewerLinkHandler
from .reviewer import wrap, AMBOSS_LINK_PREFIX


class ReviewerLinkPatcher:
    """Monkey-patches Anki reviewer by hijacking link handler bridge."""

    def __init__(self, linkHandler: ReviewerLinkHandler):
        self._linkHandler = linkHandler

    def patchOnHook(self, hook: str):
        """Monkey-patch as soon as provided Anki hook is run"""
        addHook(hook, self.patch)

    def patch(self):
        """Monkey-patch original Reviewer._linkHandler method to do our own link handling."""
        Reviewer._linkHandler = wrap(
            Reviewer._linkHandler, ReviewerLinkPatcher._onReviewerLinkHandler, self
        )

    def _onReviewerLinkHandler(self, reviewer: Reviewer, link: str, _old):
        """
        :param reviewer: original Reviewer instance to be monkey-patched
        :type reviewer: aqt.reviewer.Reviewer
        :param link: Anki link
        :type link: str
        :param _old: original Reviewer._linkHandler
        :type: function
        :return:
        """
        # TODO: delegate to ReviewerLinkHandler completely, ideally
        if not link.startswith(AMBOSS_LINK_PREFIX):
            return _old(reviewer, link)
        _, cmd, payload = link.split(":", 2)
        return self._linkHandler(cmd, payload)


class ReviewerHTMLPatcher:
    """Monkey-patches Anki reviewer by injecting JS and CSS into HTML."""

    def __init__(self, baseFolder, js=(), css=(), jsCalls=()):
        self._baseFolder = baseFolder
        self._js = js
        self._css = css
        self._jsCalls = jsCalls

    def patch(self):
        """Monkey-patch original Reviewer.revHtml method to add our own web elements."""
        Reviewer.revHtml = wrap(Reviewer.revHtml, ReviewerHTMLPatcher._onRevHtml, self)

    def _injection(self):
        inject = "\n"
        for f in self._js:
            inject += f"""<script src="{self._baseFolder}/{f}"></script>\n"""
        for f in self._css:
            inject += f"""<link rel="stylesheet" href="{self._baseFolder}/{f}">\n"""
        for c in self._jsCalls:
            inject += f"<script>{c()}</script>\n"
        return inject

    def _onRevHtml(self, reviewer, _old):
        """
        :param reviewer: original Reviewer instance to be monkey-patched
        :type reviewer: aqt.reviewer.Reviewer
        :param _old: original Reviewer.revHtml
        :type _old: function
        :return: reviewer HTML code
        :rtype: str
        """
        return _old(reviewer) + self._injection()
