document.documentElement.classList.add("js");

// Zoom: click a scan to see it large; click the image to toggle fit / actual size.
(function () {
  const dlg = document.querySelector("dialog.zoom");
  if (!dlg || !dlg.showModal) return;
  const stage = dlg.querySelector(".zoom__stage");
  const img = stage.querySelector("img");
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-zoom]");
    if (!a) return;
    e.preventDefault();
    img.src = a.getAttribute("href");
    img.alt = (a.querySelector("img") || {}).alt || "";
    stage.classList.add("fit");
    dlg.showModal();
  });
  stage.addEventListener("click", (e) => {
    if (e.target !== img) { dlg.close(); return; }
    const r = img.getBoundingClientRect();
    const fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
    stage.classList.toggle("fit");
    if (!stage.classList.contains("fit")) {
      stage.scrollLeft = fx * img.offsetWidth - stage.clientWidth / 2;
      stage.scrollTop = fy * img.offsetHeight - stage.clientHeight / 2;
    }
  });
  dlg.addEventListener("close", () => img.removeAttribute("src"));
})();

// Censors page: one source open at a time, chosen by the URL hash.
(function () {
  const sections = [...document.querySelectorAll("section.source")];
  if (!sections.length) return;
  const tl = document.querySelector(".tl");
  const rows = [...document.querySelectorAll(".tl__row")];
  const ids = sections.map((s) => s.id);

  function open(id, scroll) {
    if (!ids.includes(id)) id = ids[0];
    sections.forEach((s) => s.classList.toggle("is-open", s.id === id));
    rows.forEach((r) => {
      if (r.dataset.source === id) r.setAttribute("aria-current", "true");
      else r.removeAttribute("aria-current");
    });
    tl.classList.add("has-sel");
    if (scroll) {
      const sec = document.getElementById(id);
      if (sec.getBoundingClientRect().top > window.innerHeight * 0.75) sec.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  rows.forEach((r) => r.addEventListener("click", (e) => {
    e.preventDefault();
    const id = r.dataset.source;
    history.pushState(null, "", location.pathname + "#" + id);
    open(id, true);
  }));
  window.addEventListener("popstate", () => open(location.hash.slice(1), false));

  open(location.hash.slice(1), false);

  // Coming back from a cover page: outline the cover you were looking at.
  const seen = new URLSearchParams(location.search).get("seen");
  if (seen) {
    const card = document.getElementById("card-" + location.hash.slice(1) + "-" + seen);
    if (card) {
      card.classList.add("is-seen");
      card.scrollIntoView({ block: "center" });
    }
  }
})();

// Cover page: show the breadcrumb and previous/next for the source you came from.
(function () {
  const blocks = [...document.querySelectorAll(".ctx[data-source], .bottomnav[data-source]")];
  if (!blocks.length) return;
  const from = new URLSearchParams(location.search).get("from");
  const have = blocks.some((b) => b.dataset.source === from);
  if (!have) return;
  blocks.forEach((b) => { b.hidden = b.dataset.source !== from; });
})();

// Document pages: on small screens start the contents list closed; highlight the current section.
(function () {
  const toc = document.querySelector(".toc");
  if (!toc) return;
  const det = toc.querySelector("details");
  if (window.matchMedia("(max-width: 960px)").matches) det.removeAttribute("open");
  const links = [...toc.querySelectorAll("a")];
  const pairs = links.map((a) => [a, document.getElementById(a.getAttribute("href").slice(1))]).filter((p) => p[1]);
  let ticking = false;
  function update() {
    ticking = false;
    let cur = null;
    for (const [a, el] of pairs) {
      if (el.getBoundingClientRect().top <= 140) cur = a;
    }
    links.forEach((a) => a.classList.toggle("is-current", a === cur));
  }
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  update();
  if (window.matchMedia("(max-width: 960px)").matches) {
    links.forEach((a) => a.addEventListener("click", () => det.removeAttribute("open")));
  }
})();
