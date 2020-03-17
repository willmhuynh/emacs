/*
AMBOSS Anki Add-on

Copyright (C) 2019 AMBOSS MD Inc. <https://www.amboss.com/us>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version, with the additions
listed at the end of the license file that accompanied this program.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

let ankiVersion = "unknown";
let addonVersion = "unknown";

const context = () => ({
  context: {
    app: {
      name: "anki-addon",
      version: addonVersion || "unknown",
      hostVersion: ankiVersion || "unknown"
    }
  }
});

//  ### Hooks ###

// based on anki.hooks.wrap
function wrap(oldFct, newFct, pos = "after") {
  function repl(...args) {
    if (pos === "after") {
      oldFct(...args);
      return newFct(...args);
    } else if (pos === "before") {
      newFct(...args);
      return oldFct(...args);
    } else {
      // don't wrap at all
      return newFct(...args);
    }
  }
  return repl;
}

// ### Highlights ###

// Determine which text nodes should be marked and in what way
class TextNodeFilter {
  constructor() {
    this.initialize();
  }

  initialize() {
    this.textBuffer = "";
    this.markerType = "single";
  }

  filter(textNode, termFound, markCounter) {
    // Prevent multiple markers
    if (textNode.parentNode.hasAttribute("data-phrase-id")) {
      return false;
    }

    // Composite phrases: Identify fragment position and set CSS accordingly
    const text = textNode.textContent;
    const termIncluded = text.toLowerCase().includes(termFound.toLowerCase());

    if (!this.textBuffer && termIncluded) {
      this.markerType = "single";
    } else if (!this.textBuffer && !termIncluded) {
      this.textBuffer += text;
      this.markerType = "start";
    } else if (this.textBuffer && !termIncluded) {
      this.textBuffer += text;
      if (this.textBuffer.includes(termFound)) {
        this.textBuffer = "";
        this.markerType = "end";
      } else {
        this.markerType = "middle";
      }
    } else {
      this.markerType = "single";
      this.textBuffer = "";
    }
    return true;
  }
}

class PhraseMarker {
  constructor(cardSelector, markClass, textNodeFilter) {
    this.card = document.querySelector(cardSelector);
    this.markClass = markClass;
    this.textNodeFilter = textNodeFilter;
    this.marker = null;
  }

  hideAll() {
    if (!this.marker) {
      return false;
    }
    this.marker.unmark({ className: this.markClass });
  }

  mark(phrases) {
    // Workaround:
    // Anki might still be loading in new card content when mark() fires, so
    // we defer marking until the qa element is ready
    if (_updatingQA) {
      setTimeout(() => this.mark(phrases), 50);
      return;
    }

    this._spacifyParagraphs(this.card);

    if (!this.marker) {
      this.marker = new Mark(this.card);
    }

    let markId = 0;

    for (const term in phrases) {
      this.textNodeFilter.initialize();

      const termRegex = this._composeTermRegex(term);

      // FIXME:
      // We should switch back to mark() as soon as the hyphen workaround is
      // no longer needed (see _composeTermRegex)
      this.marker.markRegExp(termRegex, {
        element: "span",
        className: this.markClass,
        separateWordSearch: false,
        acrossElements: true,
        filter: (textNode, termFound, markCounter) =>
          this.textNodeFilter.filter(textNode, termFound, markCounter),
        each: node => {
          node.setAttribute("data-phrase-id", phrases[term]);
          node.setAttribute("data-phrase-term", term);
          node.id = `mark-${++markId}`;
          node.classList.add(`${this.markClass}-${textNodeFilter.markerType}`);
        }
      });
    }
  }

  // Workaround:
  // We match across elements to support partial formatting within phrases.
  // However, that configuration also prompts mark.js to ignore paragraph-like
  // boundaries (e.g. div, br or p) as word separators.
  // As a workaround we temporarily surround all pertinent tags with spaces.
  // This is ugly, but currently the only way to both match across elements and
  // delimit matches by paragraphs (cf. https://github.com/julmot/mark.js/issues/127)
  _spacifyParagraphs(parent) {
    for (const elm of parent.querySelectorAll("div, p, br")) {
      elm.insertAdjacentHTML("beforebegin", " ");
      elm.insertAdjacentHTML("afterend", " ");
    }
  }

  // Workaround:
  // API sometimes returns spaces for hyphens, so treat hyphens like whitespace.
  // Additionally escapes reserved regex characters in term.
  // Add word boundaries.
  _composeTermRegex(term) {
    return new RegExp(
      "\\b" +
        term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/ /g, "[ -‐‑−]") +
        "\\b",
      "gmi"
    );
  }
}

// ### Tooltips ###

class TooltipManager {
  constructor(selector, markClass) {
    this.placeholder = `<div id="amboss-card-placeholder" class="amboss-card-placeholder">
        <svg id="triangle" width="100" height="100" viewBox="-3 -4 39 39" class="container-2420473442">
          <polygon fill="transparent" stroke-width="1" points="16,0 32,32 0,32" class="amboss-load"></polygon>
        </svg>
      </div>`;
    this.selector = selector;
    this.markClass = markClass;
  }

  initialize() {
    tippy(this.selector, {
      target: `.${this.markClass}`,
      content: this.placeholder,
      animateFill: false,
      animation: "shift-away",
      theme: "light amboss",
      arrow: true,
      maxWidth: 400,
      interactive: true,
      interactiveDebounce: 100,
      flipOnUpdate: true,
      onShow: tippyInstance => {
        this.hideAll();
        this._getAbstractFor(tippyInstance.reference);
      },
      onHidden: tippyInstance => {
        tippyInstance.setContent(this.placeholder);
      }
    });
  }

  hideAll() {
    tippy.hideAll({ duration: 0 });
  }

  setContentFor(markId, html) {
    const markElm = document.getElementById(markId);
    if (!markElm) {
      return false;
    }
    markElm._tippy.popperChildren.tooltip.classList.add("tippy-tooltip-loaded");
    markElm._tippy.setContent(html);
    if (window.analytics) {
      document
        .querySelectorAll("a.amboss-destination-link")
        .forEach(element => {
          element.addEventListener("click", event => {
            // workaround for non-standard URLs path
            const params = new URL(
              element.getAttribute("href").replace(/#(xid=.+?&)/, "&$1")
            ).searchParams;

            window.analytics.track(
              "anki-addon.tooltip.destination.opened",
              {
                term: params.get("utm_term"),
                anchor: params.get("anker"),
                learningCardId: params.get("xid"),
                guid: params.get("guid")
              },
              context()
            );
          });
        });
    }
  }

  _getAbstractFor(referenceElm) {
    const payload = {
      phraseId: referenceElm.getAttribute("data-phrase-id"),
      term: referenceElm.getAttribute("data-phrase-term"),
      markId: referenceElm.id
    };
    if (window.analytics) {
      window.analytics.track(
        "anki-addon.tooltip.shown",
        {
          phraseId: payload.phraseId,
          term: payload.term
        },
        context()
      );
    }
    pycmd(`amboss:tooltip:${JSON.stringify(payload)}`);
  }
}

const accessExpired = () => {
  if (window.analytics) {
    window.analytics.track("anki_addon.tooltip.access_error");
  }
};

// ### Main ###

const cardSelector = "#qa";
const markClass = "amboss-mark";
const textNodeFilter = new TextNodeFilter();
const ambossMarker = new PhraseMarker(cardSelector, markClass, textNodeFilter);
const ambossTooltips = new TooltipManager(cardSelector, markClass);

window._showQuestion = wrap(
  window._showQuestion,
  ambossTooltips.hideAll,
  "before"
);
window._showAnswer = wrap(window._showAnswer, ambossTooltips.hideAll, "before");
window.setTimeout(function() {
  ambossTooltips.initialize();
}, 50);
