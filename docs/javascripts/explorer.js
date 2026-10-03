/* ==========================================================================
   CIRQUA interactive system explorer
   --------------------------------------------------------------------------
   Progressive enhancement only. The chain is fully readable and every node is
   already a link without JavaScript: the buttons are real <a> elements, and
   the detail panel ships with Node 1 pre-rendered. JavaScript only upgrades the
   behaviour to in-place panel updates.

   No framework, no build step, no external dependency.
   Accessibility:
     - the chain is a list of links, so keyboard and screen-reader order match
       the visual order
     - aria-pressed communicates the selected node
     - aria-live announces the updated panel
     - the detail panel has an id so it is programmatically associated
   ========================================================================== */

(function () {
  "use strict";

  function initExplorer(root) {
    if (root.dataset.cirqaReady === "1") return;
    root.dataset.cirqaReady = "1";

    var buttons = Array.prototype.slice.call(
      root.querySelectorAll("[data-explorer-node]")
    );
    var panel = root.querySelector("[data-explorer-panel]");
    if (!buttons.length || !panel) return;

    function select(key, announce) {
      buttons.forEach(function (button) {
        var active = button.getAttribute("data-explorer-node") === key;
        button.setAttribute("aria-pressed", active ? "true" : "false");

        // Swap only the heading of the link so navigation still works.
        var num = button.querySelector("[data-part='num']");
        if (num) num.textContent = button.getAttribute("data-num") || "";

        if (active && announce) {
          // Nothing to do for aria-pressed; state is already announced by
          // the panel's aria-live region when its content changes.
        }
      });

      var template = root.querySelector('[data-explorer-template="' + key + '"]');
      if (!template) return;

      panel.innerHTML = template.innerHTML;
      // Move keyboard focus to the updated panel heading for screen readers
      // and keyboard users who activated the control.
      var heading = panel.querySelector("h3");
      if (heading) {
        heading.setAttribute("tabindex", "-1");
        heading.focus({ preventScroll: true });
      }
      if (announce) {
        panel.setAttribute("aria-live", "polite");
      }
    }

    buttons.forEach(function (button) {
      button.addEventListener("click", function (event) {
        // Let modified clicks behave like normal links.
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) {
          return;
        }
        event.preventDefault();
        history.replaceState(null, "", button.getAttribute("href"));
        select(button.getAttribute("data-explorer-node"), true);
      });
    });

    // Open whichever node the URL fragment names, otherwise keep the
    // server-rendered default.
    var hash = (window.location.hash || "").replace("#", "");
    if (hash) {
      var match = buttons.filter(function (b) {
        return b.getAttribute("href") === "#" + hash;
      })[0];
      if (match) select(match.getAttribute("data-explorer-node"), false);
    }
  }

  function init() {
    var explorers = document.querySelectorAll("[data-cirqua-explorer]");
    Array.prototype.forEach.call(explorers, initExplorer);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(init);
  }
})();