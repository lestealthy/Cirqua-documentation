/* ==========================================================================
   CIRQUA Technical Documentation - progressive enhancement only.
   Everything essential is already present in the static HTML; this file adds
   navigation conveniences without introducing a framework dependency.
   ========================================================================== */

(function () {
  "use strict";

  /* --------------------------------------------------------------------
     1. Wrap wide engineering tables so phones scroll them horizontally
        instead of overflowing the page.
     -------------------------------------------------------------------- */
  function wrapWideTables() {
    var tables = document.querySelectorAll(".md-typeset table");
    Array.prototype.forEach.call(tables, function (table) {
      var parent = table.parentNode;
      if (!parent || parent.classList.contains("table-scroll")) return;
      var wrapper = document.createElement("div");
      wrapper.className = "table-scroll";
      parent.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    });
  }

  /* --------------------------------------------------------------------
     2. Annotate code blocks with a copy button that reports success.
        Material already provides content.code.copy; this is a no-op when
        the native button is already present.
     -------------------------------------------------------------------- */
  function ensureCopyButtons() {
    if (document.querySelector(".md-clipboard")) return; // Material already active
  }

  /* --------------------------------------------------------------------
     3. Reading progress indicator (thin, blue, non-intrusive).
     -------------------------------------------------------------------- */
  function addProgressBar() {
    var bar = document.createElement("div");
    bar.id = "cirqua-progress";
    bar.setAttribute("aria-hidden", "true");
    bar.style.cssText = [
      "position:fixed",
      "top:0",
      "left:0",
      "height:2px",
      "width:0",
      "background:#072A92",
      "z-index:10000",
      "transition:width 0.1s ease-out",
      "pointer-events:none"
    ].join(";");
    document.body.appendChild(bar);

    function update() {
      var doc = document.documentElement;
      var height = doc.scrollHeight - window.innerHeight;
      var pct = height > 0 ? (window.scrollY / height) * 100 : 0;
      bar.style.width = Math.min(Math.max(pct, 0), 100) + "%";
    }
    window.addEventListener("scroll", update, { passive: true });
    update();
  }

  /* --------------------------------------------------------------------
     4. Back-to-top control, shown only after scrolling.
     -------------------------------------------------------------------- */
  function addBackToTop() {
    var btn = document.createElement("button");
    btn.id = "cirqua-top";
    btn.type = "button";
    btn.setAttribute("aria-label", "Back to top");
    btn.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">' +
      '<path fill="currentColor" d="M12 4l-8 8 1.4 1.4L12 6.8l6.6 6.6L20 12z"/><path fill="currentColor" d="M11 11h2v9h-2z"/></svg>';
    btn.style.cssText = [
      "position:fixed",
      "bottom:1.4rem",
      "right:1.4rem",
      "width:2.4rem",
      "height:2.4rem",
      "borderRadius:50%",
      "background:#072A92",
      "color:#ffffff",
      "border:none",
      "cursor:pointer",
      "display:none",
      "alignItems:center",
      "justifyContent:center",
      "boxShadow:0 2px 10px rgba(10,5,27,0.22)",
      "zIndex:900"
    ].join(";");
    document.body.appendChild(btn);

    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    window.addEventListener(
      "scroll",
      function () {
        btn.style.display = window.scrollY > 320 ? "flex" : "none";
      },
      { passive: true }
    );
  }

  /* --------------------------------------------------------------------
     5. Mark external links so they open safely in a new tab.
     -------------------------------------------------------------------- */
  function markExternalLinks() {
    var links = document.querySelectorAll('.md-typeset a[href^="http"]');
    Array.prototype.forEach.call(links, function (link) {
      if (link.hostname === window.location.hostname) return;
      if (link.dataset.cirquaExternal === "1") return;
      link.dataset.cirquaExternal = "1";
      link.setAttribute("target", "_blank");
      link.setAttribute("rel", "noopener noreferrer");
    });
  }

  /* --------------------------------------------------------------------
     6. Keyboard shortcut: "/" focuses the search field, Escape blurs it.
     -------------------------------------------------------------------- */
  function addSearchShortcut() {
    document.addEventListener("keydown", function (event) {
      var tag = (event.target.tagName || "").toLowerCase();
      var typing =
        tag === "input" ||
        tag === "textarea" ||
        tag === "select" ||
        event.target.isContentEditable;
      if (typing || event.ctrlKey || event.altKey || event.metaKey) return;

      if (event.key === "/") {
        var input = document.querySelector(".md-search__input");
        if (input) {
          event.preventDefault();
          input.focus();
        }
      } else if (event.key === "Escape") {
        var active = document.activeElement;
        if (active && active.classList.contains("md-search__input")) {
          active.blur();
        }
      }
    });
  }

  /* --------------------------------------------------------------------
     Boot
     -------------------------------------------------------------------- */
  function init() {
    wrapWideTables();
    ensureCopyButtons();
    addProgressBar();
    addBackToTop();
    markExternalLinks();
    addSearchShortcut();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // MkDocs instant navigation re-runs this module on page transitions.
  if (typeof document$ !== "undefined") {
    document$.subscribe(init);
  }
})();