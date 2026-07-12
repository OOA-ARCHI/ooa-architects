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

  /* ---------- Project gallery slideshows ----------
     Each [data-slideshow] instance (one per project entry) tracks its own
     active index independently — navigating one project's gallery never
     affects any other project on the page. */
  function initSlideshows() {
    var shows = document.querySelectorAll("[data-slideshow]");

    shows.forEach(function (show) {
      var track = show.querySelector(".slideshow-track");
      var slides = show.querySelectorAll("[data-slide]");
      var dots = show.querySelectorAll(".slide-dot");
      var prevBtn = show.querySelector(".slide-zone-prev");
      var nextBtn = show.querySelector(".slide-zone-next");
      var count = slides.length;
      var active = 0;

      if (!track || count === 0) return;

      function render() {
        track.style.setProperty("--active", active);

        slides.forEach(function (slide, i) {
          var isActive = i === active;
          slide.classList.toggle("is-active", isActive);
          slide.setAttribute("aria-hidden", String(!isActive));
        });

        dots.forEach(function (dot, i) {
          var isActive = i === active;
          dot.classList.toggle("is-active", isActive);
          dot.setAttribute("aria-selected", String(isActive));
        });
      }

      function goTo(index) {
        active = (index + count) % count;
        render();
      }

      if (prevBtn) {
        prevBtn.addEventListener("click", function () {
          goTo(active - 1);
        });
      }

      if (nextBtn) {
        nextBtn.addEventListener("click", function () {
          goTo(active + 1);
        });
      }

      dots.forEach(function (dot, i) {
        dot.addEventListener("click", function () {
          goTo(i);
        });
      });

      show.addEventListener("keydown", function (event) {
        if (event.key === "ArrowLeft") {
          event.preventDefault();
          goTo(active - 1);
        } else if (event.key === "ArrowRight") {
          event.preventDefault();
          goTo(active + 1);
        }
      });

      /* ---- Swipe / drag gesture (Pointer Events cover touch + mouse + pen) ----
         Tapping still falls through to the zone-button click handlers above;
         this only reacts once movement crosses SWIPE_THRESHOLD, and then
         suppresses the synthetic click that follows so a swipe ending over
         a zone button doesn't also fire that button's own goTo(). */
      var SWIPE_THRESHOLD = 40;
      var pointerStartX = 0;
      var pointerStartY = 0;
      var pointerActive = false;
      var didSwipe = false;

      show.addEventListener("pointerdown", function (event) {
        if (event.pointerType === "mouse" && event.button !== 0) return;
        pointerActive = true;
        didSwipe = false;
        pointerStartX = event.clientX;
        pointerStartY = event.clientY;
      });

      show.addEventListener("pointermove", function (event) {
        if (!pointerActive) return;
        var dx = event.clientX - pointerStartX;
        var dy = event.clientY - pointerStartY;
        if (Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy)) {
          // Horizontal drag dominant — stop vertical page scroll from fighting the gesture.
          event.preventDefault();
        }
      });

      function endPointer(event) {
        if (!pointerActive) return;
        pointerActive = false;
        var dx = event.clientX - pointerStartX;
        var dy = event.clientY - pointerStartY;
        if (Math.abs(dx) >= SWIPE_THRESHOLD && Math.abs(dx) > Math.abs(dy)) {
          didSwipe = true;
          goTo(active + (dx < 0 ? 1 : -1));
        }
      }

      show.addEventListener("pointerup", endPointer);
      show.addEventListener("pointercancel", function () {
        pointerActive = false;
      });

      show.addEventListener(
        "click",
        function (event) {
          if (didSwipe) {
            event.preventDefault();
            event.stopPropagation();
            didSwipe = false;
          }
        },
        true
      );

      render();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSidebarToggle();
    initSmoothScroll();
    scrollToInitialHash();
    initSlideshows();
  });
})();
