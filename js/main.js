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
     Like the sasaki.com landing screen, each outline letter starts as a
     hairline stroke and grows to full stroke weight at staggered moments
     (verified frame-by-frame from a screen recording of sasaki.com).
     While the splash stays up, random letters keep thinning back to a
     hairline and regrowing, so the type feels alive. The dot appears
     last, as a closing punctuation mark, before the whole splash fades
     out to reveal the homepage. Plays once per browser tab session and is skippable by
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

    /* 아웃라인 텍스트를 글자 단위 span으로 분리 (글자별 획 굵기 애니메이션용).
       완성 획 굵기는 CSS(-webkit-text-stroke, 데스크톱 1.5px/모바일 1px)에서 읽는다 */
    var letters = [];
    var lights = splash.querySelectorAll(".intro-light");
    for (var i = 0; i < lights.length; i++) {
      var baseStroke =
        parseFloat(getComputedStyle(lights[i]).webkitTextStrokeWidth) || 1.5;
      var text = lights[i].textContent;
      lights[i].textContent = "";
      for (var j = 0; j < text.length; j++) {
        var ch = document.createElement("span");
        ch.className = "intro-ch";
        ch.textContent = text.charAt(j);
        ch.dataset.base = baseStroke;
        /* 시작 상태: 거의 보이지 않는 헤어라인 획 */
        ch.style.webkitTextStrokeWidth = "0.05px";
        lights[i].appendChild(ch);
        letters.push(ch);
      }
      /* 글자가 전부 헤어라인 상태가 된 뒤에만 노출 (완성 굵기 플래시 방지) */
      lights[i].style.opacity = "1";
    }

    /* -webkit-text-stroke-width는 CSS transition이 안 되는(discrete) 속성이라
       requestAnimationFrame으로 직접 보간한다. sasaki.com 첫 화면과 동일하게
       가는 선 -> 완성 굵기로 "자라나는" 움직임 */
    var tweens = [];
    var rafId = null;

    function tickTweens(now) {
      for (var t = tweens.length - 1; t >= 0; t--) {
        var tw = tweens[t];
        var p = (now - tw.start) / tw.dur;
        if (p < 0) continue;
        if (p > 1) p = 1;
        var eased = 1 - Math.pow(1 - p, 3); /* ease-out cubic */
        tw.el.style.webkitTextStrokeWidth =
          (tw.from + (tw.to - tw.from) * eased).toFixed(2) + "px";
        if (p === 1) {
          tweens.splice(t, 1);
          if (tw.done) tw.done();
        }
      }
      rafId = window.requestAnimationFrame(tickTweens);
    }

    function tween(el, from, to, dur, delay, done) {
      tweens.push({
        el: el,
        from: from,
        to: to,
        dur: dur,
        start: performance.now() + (delay || 0),
        done: done
      });
    }

    var waveTicker = null;

    var revealTimer = window.setTimeout(function () {
      splash.classList.add("is-revealed");
      rafId = window.requestAnimationFrame(tickTweens);
      /* 등장: 글자마다 시차를 두고 헤어라인 -> 완성 굵기로 성장 */
      for (var k = 0; k < letters.length; k++) {
        tween(letters[k], 0.05, parseFloat(letters[k].dataset.base), 700, Math.random() * 600);
      }
    }, 1000);

    /* 등장 완료 후: 무작위 글자가 가늘어졌다가 다시 굵어지기를 반복 */
    function pulse(el) {
      el.dataset.busy = "1";
      var base = parseFloat(el.dataset.base);
      tween(el, base, 0.1, 350, 0, function () {
        tween(el, 0.1, base, 450, 80, function () {
          delete el.dataset.busy;
        });
      });
    }

    var waveTimer = window.setTimeout(function () {
      waveTicker = window.setInterval(function () {
        for (var k = 0; k < letters.length; k++) {
          if (!letters[k].dataset.busy && Math.random() < 0.15) {
            pulse(letters[k]);
          }
        }
      }, 500);
    }, 2500);

    var dotTimer = window.setTimeout(function () {
      splash.classList.add("is-dot-revealed");
    }, 3000);

    var hideTimer = window.setTimeout(finish, 4200);

    function finish() {
      window.clearTimeout(revealTimer);
      window.clearTimeout(waveTimer);
      window.clearTimeout(dotTimer);
      window.clearTimeout(hideTimer);
      window.clearInterval(waveTicker);
      if (rafId) window.cancelAnimationFrame(rafId);
      tweens.length = 0;
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
