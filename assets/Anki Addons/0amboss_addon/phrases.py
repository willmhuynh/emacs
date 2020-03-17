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


from collections import namedtuple
from functools import lru_cache
from typing import Dict, Optional

import requests
import json

from .shared import TokenAuth
from .graphql import (
    GraphQLClient,
    GraphQLAuthorizationException,
    GraphQLClientException,
    GraphQLNetworkException,
)

Phrase = namedtuple(
    "Phrase",
    ["title", "groupId", "anchorId", "articleId", "articleTitle", "sectionTitle"],
)

PhraseGroup = namedtuple(
    "PhraseGroup",
    [
        "title",
        "id",
        "synonyms",
        "abstract",
        "translation",
        "destinations",
        "accessLimitation",
    ],
)

Destination = namedtuple("Destination", ["label", "articleId", "anchor"])


class PhraseMapper:
    """Maps result dict of phrase metadata to namedtuple Phrase object."""

    @staticmethod
    def map(d: dict) -> Phrase:
        return Phrase(
            title=d.get("phrase_title"),
            groupId=d.get("pg_id"),
            anchorId=d.get("ankerlink_id"),
            articleId=d.get("lc_id"),
            articleTitle=d.get("lc_title"),
            sectionTitle=d.get("ls_title"),
        )


class DestinationMapper:
    """Maps GraphQL SememeDestination JSON to namedtuple Destination object."""

    @staticmethod
    def map(d: dict) -> Destination:
        return Destination(
            label=d.get("label"), articleId=d.get("articleEid"), anchor=d.get("anchor")
        )


class PhraseGroupMapper:
    """Maps GraphQL PhraseGroup JSON to namedtuple PhraseGroup object."""

    def __init__(self, destMapper: DestinationMapper):
        self._destMapper = destMapper

    def map(self, d: dict) -> Optional[PhraseGroup]:
        phraseGroupData = d.get("data", {}).get("phraseGroup")
        if not phraseGroupData:
            return None
        return PhraseGroup(
            title=phraseGroupData.get("title"),
            id=phraseGroupData.get("eid"),
            synonyms=phraseGroupData.get("synonyms", []),
            abstract=phraseGroupData.get("abstract"),
            translation=phraseGroupData.get("translation"),
            destinations=[
                self._destMapper.map(dest)
                for dest in phraseGroupData.get("destinations", [])
            ],
            accessLimitation=self._isAccessLimited(d),
        )

    def _isAccessLimited(self, d: dict) -> bool:
        errors = d.get("errors", [{}])
        for error in errors:
            if error.get("message") == "permission.user_is_not_authorized":
                return True
            path = error.get("path", [None])
            if isinstance(path, list) and path[-1] == "abstract":
                return True
        return False


class PhraseFinderClient:
    """Client for fetching phrase metadata of list of Anki notes from REST endpoint."""

    _userAgent = "anki-addon"

    def __init__(self, uri: str, tokenAuth: TokenAuth, timeout: int):
        self._uri = uri
        self._tokenAuth = tokenAuth
        self._timeout = timeout

    # TODO: cache individual phrases as well as tuples
    @lru_cache(maxsize=128)
    def getPhraseDict(self, strings: tuple, guid: str) -> dict:
        response = requests.request(
            "POST",
            self._uri,
            data=json.dumps({"card_text_list": list(strings), "guid": guid}),
            timeout=self._timeout,
            headers={
                **{"Content-Type": "application/json", "User-Agent": self._userAgent},
                **self._tokenAuth.header,
            },
        )
        # TODO: inform client about failed request
        if response.status_code != 200:
            return {}
        try:
            response = json.loads(response.content)
        except ValueError:
            return {}
        return response


class PhraseRepository:
    """Holds cache of found Phrase metadata objects based on phrase group ID."""

    # TODO: phrase group ID might not be a valid key, as multiple phrases can belong to the same group
    # TODO: REST API returns synonym, not main phrase, use that normalized + encoded as key instead
    _phrasesById = {}

    def getPhraseById(self, phraseGroupId: str):
        return self._phrasesById.get(phraseGroupId, None)

    def store(self, phrase: Phrase):
        self._phrasesById[phrase.groupId] = phrase


class PhraseFinder:
    """
    Finds matching phrases and their phrase group IDs in Anki note fields.
    Stores the found phrases in PhraseRepository.
    """

    def __init__(
        self,
        client: PhraseFinderClient,
        repository: PhraseRepository,
        mapper: PhraseMapper,
    ):
        self._client = client
        self._repository = repository
        self._mapper = mapper

    @lru_cache(maxsize=128)
    def getPhrases(self, strings: tuple, guid: str) -> Dict[str, Phrase]:
        response = self._client.getPhraseDict(strings, guid)
        if "results" not in response or len(response) == 0:
            return {}
        phrases = {}
        for result in response["results"]:
            phrase = self._mapper.map(result)
            phrases[result["term"]] = phrase
            self._repository.store(phrase)
        return phrases


class PhraseGroupResolver:
    """Resolves phrase group ID to PhraseGroup objects with metadata such as abstract, synonyms and destinations."""

    def __init__(self, client: GraphQLClient, phraseGroupMapper: PhraseGroupMapper):
        self._client = client
        self._phraseGroupMapper = phraseGroupMapper

    def getPhraseGroup(self, phrase: Phrase) -> Optional[PhraseGroup]:
        try:
            return self._phraseGroupMapper.map(
                self._client.getPhraseGroupDict(phrase.groupId)
            )
        except (
            GraphQLNetworkException,
            GraphQLAuthorizationException,
            GraphQLClientException,
        ) as e:
            raise e
