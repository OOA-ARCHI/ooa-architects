/**
 * OOA Architects — main.js
 * Vanilla JS, no dependencies: mobile sidebar drawer toggle + smooth anchor scrolling.
 * The project navigation tree itself uses native <details>/<summary> and needs no JS.
 */

(function () {
  "use strict";

  /* ---------- Mobile sidebar drawer toggle ---------- */
  function initSidebarToggle() {
    var toggle = document.querySelector(".sidebar-toggle");
    var sidebar = document.getElementById("sidebar");

    if (!toggle || !sidebar) return;

    toggle.addEventListener("click", function () {
      var isOpen = sidebar.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
      document.body.style.overflow = isOpen ? "hidden" : "";
    });

    // Close the drawer when a link inside the sidebar is activated (mobile)
    sidebar.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.innerWidth >= 768) return;
        sidebar.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      });
    });

    // Close the drawer on outside click (mobile overlay behavior)
    document.addEventListener("click", function (event) {
      if (window.innerWidth >= 768) return;
      if (!sidebar.classList.contains("is-open")) return;
      if (sidebar.contains(event.target) || toggle.contains(event.target)) return;
      sidebar.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    });
  }

  /* ---------- Smooth-scroll for in-page anchors ---------- */
  function initSmoothScroll() {
    var links = document.querySelectorAll('a[href*="#"]');

    links.forEach(function (link) {
      var href = link.getAttribute("href");
      if (!href) return;

      var hashIndex = href.indexOf("#");
      var hash = href.slice(hashIndex);
      var pathPart = href.slice(0, hashIndex);

      // Only intercept links that point to an anchor on the current page
      var isSamePage =
        pathPart === "" ||
        pathPart === window.location.pathname.split("/").pop();

      if (!isSamePage || hash.length < 2) return;

      link.addEventListener("click", function (event) {
        var target = document.querySelector(hash);
        if (!target) return;

        event.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        history.pushState(null, "", hash);
      });
    });
  }

  /* ---------- Scroll to hash target on initial load ---------- */
  function scrollToInitialHash() {
    if (!window.location.hash) return;
    var target = document.querySelector(window.location.hash);
    if (!target) return;

    window.requestAnimationFrame(function () {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSidebarToggle();
    initSmoothScroll();
    scrollToInitialHash();
  });
})();
