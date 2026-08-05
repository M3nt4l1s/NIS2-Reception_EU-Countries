document.addEventListener("DOMContentLoaded", () => {
    const dataRoot = document.getElementById("country-grid");
    const mapSvg = document.getElementById("eu-map");
    if (!dataRoot || !mapSvg) return;



    const cards = Array.from(dataRoot.querySelectorAll(".country-card"));
    const cardByIso = new Map(cards.map(c => [c.dataset.iso, c]));

    mapSvg.querySelectorAll(".eu-country").forEach(path => {
        const card = cardByIso.get(path.dataset.iso);
        if (!card) return;
        path.classList.add("status-" + card.dataset.status);
    });
   
    const hitsLayer = document.getElementById("eu-map-hits");
    mapSvg.querySelectorAll(".eu-country").forEach(path => {
        const card = cardByIso.get(path.dataset.iso);
        if (!card) return;

        path.setAttribute("tabindex", "0");
        path.setAttribute("role", "button");
        const name = card.querySelector(".country-name");
        if (name) path.setAttribute("aria-label", name.textContent.trim());

        const b = path.getBBox();
        if (Math.max(b.width, b.height) < 8 && hitsLayer) {
            const hit = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            hit.setAttribute("class", "eu-hit-target");
            hit.setAttribute("data-iso", path.dataset.iso);
            hit.setAttribute("cx", b.x + b.width / 2);
            hit.setAttribute("cy", b.y + b.height / 2);
            hit.setAttribute("r", 2.6);
            hit.setAttribute("tabindex", "0");
            hit.setAttribute("role", "button");
            if (name) hit.setAttribute("aria-label", name.textContent.trim());
            hitsLayer.appendChild(hit);
        }
    });

   
    const backdrop = document.getElementById("country-modal-backdrop");
    const content = document.getElementById("country-modal-content");
    const closeBtn = document.getElementById("country-modal-close");
    let lastFocused = null;
    let openedByKeyboard = false;

    function openModal(iso) {
        const card = cardByIso.get(iso);
        if (!card) return;
        content.innerHTML = "";
        ["\.card-header", ".card-meta", ".details-content"].forEach(sel => {
            const el = card.querySelector(sel);
            if (el) content.appendChild(el.cloneNode(true));
        });
        lastFocused = document.activeElement;
        backdrop.hidden = false;
        closeBtn.focus();
    }

    function closeModal() {
        backdrop.hidden = true;
        content.innerHTML = "";
        if (openedByKeyboard && lastFocused && lastFocused.focus) lastFocused.focus();
    }

    mapSvg.addEventListener("click", e => {
        const t = e.target.closest("[data-iso]");
  if (t) { openedByKeyboard = false; openModal(t.dataset.iso); }
    });
    mapSvg.addEventListener("keydown", e => {
        if (e.key !== "Enter" && e.key !== " ") return;
        const t = e.target.closest("[data-iso]");
        if (!t) return;
        e.preventDefault();
        openedByKeyboard = true;
        openModal(t.dataset.iso);
    });
    document.addEventListener("keydown", e => {
        if (e.key === "Escape" && !backdrop.hidden) closeModal();
    });
    closeBtn.addEventListener("click", closeModal);
    backdrop.addEventListener("click", e => { if (e.target === backdrop) closeModal(); });

  const popup = document.getElementById("country-popup");

  function fillPopup(iso) {
    const card = cardByIso.get(iso);
    if (!card) return false;
    popup.innerHTML = "";
    [".card-header", ".card-meta"].forEach(sel => {
      const el = card.querySelector(sel);
      if (el) popup.appendChild(el.cloneNode(true));
    });
    return true;
  }

  function placePopup(x, y) {
    const m = 16, r = popup.getBoundingClientRect();
    let left = x + m, top = y + m;
    if (left + r.width  > window.innerWidth  - m) left = x - r.width  - m;
    if (top  + r.height > window.innerHeight - m) top  = y - r.height - m;
    popup.style.left = Math.max(m, left) + "px";
    popup.style.top  = Math.max(m, top)  + "px";
  }

  mapSvg.addEventListener("mousemove", e => {
    const t = e.target.closest("[data-iso]");
    if (!t) { popup.hidden = true; return; }
    if (popup.dataset.iso !== t.dataset.iso) {
      if (!fillPopup(t.dataset.iso)) { popup.hidden = true; return; }
      popup.dataset.iso = t.dataset.iso;
    }
    popup.hidden = false;
    placePopup(e.clientX, e.clientY);
  });

  mapSvg.addEventListener("mouseleave", () => { popup.hidden = true; });

});