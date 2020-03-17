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
import logging
from typing import Optional
from urllib.request import urlopen
from ssl import create_default_context
from urllib.error import URLError
from functools import lru_cache

from sgqlc.endpoint.http import HTTPEndpoint
from sgqlc.types import Type, Field, list_of, ArgDict, ID
from sgqlc.operation import Operation
from requests.utils import certs

from .shared import TokenAuth


class SememeDestination(Type):
    """Subset of GraphQL type for sememe destination."""

    label = str
    articleEid = ID
    anchor = str


class PhraseGroup(Type):
    """Subset of GraphQL type for phrase group."""

    eid = str
    # the top-ranking synonym
    title = str
    # all other synonyms
    synonyms = list_of(str)
    abstract = str
    # etymology
    translation = str
    destinations = list_of(SememeDestination)


class Query(Type):
    """Subset of Graphql query type."""

    phraseGroup = Field(PhraseGroup, args=ArgDict(eid=str))


class GraphQLNetworkException(Exception):
    """Generic GraphQL client exception."""

    pass


class GraphQLClientException(Exception):
    """Generic GraphQL client exception."""

    pass


class GraphQLAuthorizationException(GraphQLClientException):
    """User is not authorized or not logged in."""

    pass


class GraphQLClient:
    """Client for communication with GraphQL endpoint."""

    _context = create_default_context(cafile=certs.where())

    def __init__(self, uri: str, tokenAuth: TokenAuth, timeout: int):
        assert type(uri) is str
        assert type(tokenAuth) is TokenAuth
        self._uri = uri
        self._tokenAuth = tokenAuth
        self._timeout = timeout

    @property
    def _endpoint(self) -> HTTPEndpoint:
        @lru_cache(maxsize=1)
        def _tokenEndpoint(authHeaderJson: Optional[str]):
            endpoint = HTTPEndpoint(self._uri, json.loads(authHeaderJson), urlopen=self._urlopen)
            endpoint.logger = logging.Logger(endpoint.__class__.__name__, logging.CRITICAL)
            return endpoint
        return _tokenEndpoint(json.dumps(self._tokenAuth.header))

    def getPhraseGroupDict(self, phraseId: str) -> dict:
        if not self._isLoggedIn():
            raise GraphQLAuthorizationException
        return self._getPhraseGroupDict(phraseId)

    def _urlopen(self, url, data=None, timeout=None) -> None:
        return urlopen(
            url,
            data=data,
            timeout=timeout or self._timeout,
            context=self._context,
            cafile=None,
            capath=None,
            cadefault=False,
        )

    @lru_cache(maxsize=128)
    def _getPhraseGroupDict(self, phraseId: str) -> dict:
        op = Operation(Query)
        op.phraseGroup(eid=phraseId)
        try:
            response = self._endpoint(op)
        except URLError:
            raise GraphQLNetworkException
        if "data" not in response:
            raise GraphQLClientException
        return response

    def setToken(self, token: str) -> None:
        self._tokenAuth.token = token

    def _isLoggedIn(self) -> bool:
        return self._tokenAuth.isSet()
