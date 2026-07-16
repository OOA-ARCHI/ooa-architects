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
        var target = document.getElementById(hash.slice(1));
        if (!target) return;

        event.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        history.pushState(null, "", hash);
      });
    });
  }

  /* ---------- Scroll to hash target on initial load ----------
     Uses getElementById rather than querySelector(hash) because project
     slugs start with a digit (e.g. "07-byeolbit-..."), which is an invalid
     CSS ID selector and throws — silently skipping every init call queued
     after this one, including initSlideshows(). */
  function scrollToInitialHash() {
    if (!window.location.hash) return;
    var target = document.getElementById(window.location.hash.slice(1));
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

  /* ---------- Home hero auto-slideshow (index.html only) ----------
     Cross-fades through images/main/01.jpg..06.jpg in order, one at a
     time, looping back to the first after the last. */
  function initHeroSlideshow() {
    var hero = document.querySelector("[data-hero-slideshow]");
    if (!hero) return;

    var images = hero.querySelectorAll(".hero-visual-img");
    if (images.length < 2) return;

    var active = 0;

    window.setInterval(function () {
      images[active].classList.remove("is-active");
      active = (active + 1) % images.length;
      images[active].classList.add("is-active");
    }, 3200);
  }

  /* ---------- Intro splash (index.html only) ----------
     Black "OOA" is visible immediately; 1s later the expansion text
     ("ptimum" / "pus" / "rchitecture") fades in as outline letters.
     Shortly after, each outline letter fills with a color from a
     Sasaki-logo-inspired palette and keeps shifting to new colors at
     staggered moments (mosaic feel). The dot appears last, as a closing
     punctuation mark, before the whole splash fades out to reveal the
     homepage. Plays once per browser tab session and is skippable by
     click; respects prefers-reduced-motion. */
  function initIntroSplash() {
    var splash = document.getElementById("introSplash");
    if (!splash) return;

    if (sessionStorage.getItem("ooaIntroPlayed")) {
      splash.remove();
      return;
    }
    sessionStorage.setItem("ooaIntroPlayed", "1");

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      splash.remove();
      return;
    }

    document.body.style.overflow = "hidden";

    /* 노란 배경(#e8c65a) 위에서 잘 보이도록 고른 Sasaki풍 팔레트 */
    var INTRO_PALETTE = [
      "#d7263d", /* crimson */
      "#1f6f43", /* forest green */
      "#7b3f8c", /* plum */
      "#2f4b9e", /* cobalt */
      "#e2711d", /* burnt orange */
      "#c98a8f", /* dusty rose */
      "#7f95c9", /* periwinkle */
      "#74a12e", /* moss lime */
      "#3e8f7c", /* teal */
      "#8e2f3c", /* maroon */
      "#8a5a2b", /* umber */
      "#9a7fc2"  /* lavender */
    ];

    /* 아웃라인 텍스트를 글자 단위 span으로 분리 (색을 글자별로 바꾸기 위함) */
    var letters = [];
    var lights = splash.querySelectorAll(".intro-light");
    for (var i = 0; i < lights.length; i++) {
      var text = lights[i].textContent;
      lights[i].textContent = "";
      for (var j = 0; j < text.length; j++) {
        var ch = document.createElement("span");
        ch.className = "intro-ch";
        ch.textContent = text.charAt(j);
        /* 글자마다 다른 지연 시간 → 색이 모자이크처럼 시차를 두고 변한다 */
        ch.style.transitionDelay = (Math.random() * 0.35).toFixed(2) + "s";
        lights[i].appendChild(ch);
        letters.push(ch);
      }
    }

    function pickColor(current) {
      var next = current;
      while (next === current) {
        next = INTRO_PALETTE[Math.floor(Math.random() * INTRO_PALETTE.length)];
      }
      return next;
    }

    var colorTicker = null;

    var revealTimer = window.setTimeout(function () {
      splash.classList.add("is-revealed");
    }, 1000);

    /* 텍스트가 자리잡은 뒤: 전 글자에 첫 색을 입히고, 이후 일부 글자씩 계속 전환 */
    var colorTimer = window.setTimeout(function () {
      for (var k = 0; k < letters.length; k++) {
        letters[k].dataset.introColor = pickColor("");
        letters[k].style.color = letters[k].dataset.introColor;
      }
      colorTicker = window.setInterval(function () {
        for (var k = 0; k < letters.length; k++) {
          if (Math.random() < 0.35) {
            letters[k].dataset.introColor = pickColor(letters[k].dataset.introColor);
            letters[k].style.color = letters[k].dataset.introColor;
          }
        }
      }, 650);
    }, 1600);

    var dotTimer = window.setTimeout(function () {
      splash.classList.add("is-dot-revealed");
    }, 3000);

    var hideTimer = window.setTimeout(finish, 4200);

    function finish() {
      window.clearTimeout(revealTimer);
      window.clearTimeout(colorTimer);
      window.clearTimeout(dotTimer);
      window.clearTimeout(hideTimer);
      window.clearInterval(colorTicker);
      splash.classList.add("is-revealed", "is-dot-revealed", "is-hidden");
      document.body.style.overflow = "";

      splash.addEventListener("transitionend", function handleEnd(event) {
        if (event.propertyName !== "opacity") return;
        splash.removeEventListener("transitionend", handleEnd);
        splash.remove();
      });
    }

    splash.addEventListener("click", finish);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSidebarToggle();
    initSmoothScroll();
    scrollToInitialHash();
    initSlideshows();
    initHeroSlideshow();
    initIntroSplash();
  });
})();
