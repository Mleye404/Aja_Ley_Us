// AJA LEY — front-end simple : menu mobile, frais de livraison au checkout, guide des tailles.
document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.getElementById("navToggle");
  var closeBtn = document.getElementById("mobileNavClose");
  var mobileNav = document.getElementById("mobileNav");
  var backdrop = document.getElementById("mobileNavBackdrop");

  if (!toggle || !mobileNav || !backdrop) return;

  function openMenu() {
    mobileNav.classList.add("open");
    backdrop.classList.add("open");
    toggle.classList.add("active");
    toggle.setAttribute("aria-expanded", "true");
    mobileNav.setAttribute("aria-hidden", "false");
    document.body.classList.add("nav-open");
  }

  function closeMenu() {
    mobileNav.classList.remove("open");
    backdrop.classList.remove("open");
    toggle.classList.remove("active");
    toggle.setAttribute("aria-expanded", "false");
    mobileNav.setAttribute("aria-hidden", "true");
    document.body.classList.remove("nav-open");
  }

  toggle.addEventListener("click", function () {
    if (mobileNav.classList.contains("open")) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  if (closeBtn) closeBtn.addEventListener("click", closeMenu);
  backdrop.addEventListener("click", closeMenu);

  mobileNav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", closeMenu);
  });

  // Ferme le menu si la fenêtre repasse en largeur desktop.
  window.addEventListener("resize", function () {
    if (window.innerWidth > 900) closeMenu();
  });
});


// Checkout Sénégal : région -> zone de livraison (Dakar, Thiès) -> ville / localité -> frais et total.
// (Les montants viennent du serveur — aucune saisie manuelle ; le serveur recalcule aussi à la validation.)
document.addEventListener("DOMContentLoaded", function () {
  var regionSelect = document.getElementById("id_region");
  var summary = document.getElementById("checkoutSummary");
  var cfgEl = document.getElementById("shipping-config");
  if (!regionSelect || !summary || !cfgEl) return;

  var config = JSON.parse(cfgEl.textContent);
  var subtotal = parseInt(summary.getAttribute("data-subtotal"), 10) || 0;
  var zoneGroup = document.getElementById("zoneGroup");
  var zoneSelect = document.getElementById("id_delivery_zone");
  var zoneHelp = document.getElementById("zoneHelp");
  var localityGroup = document.getElementById("localityGroup");
  var localitySelect = document.getElementById("id_locality");
  var otherGroup = document.getElementById("localityOtherGroup");
  var sumRegion = document.getElementById("sumRegion");
  var sumZoneRow = document.getElementById("sumZoneRow");
  var sumZone = document.getElementById("sumZone");
  var sumShipping = document.getElementById("sumShipping");
  var sumTotal = document.getElementById("sumTotal");
  var zonesBuiltFor = null, localitiesBuiltFor = null;

  function fmt(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0") + "\u00a0FCFA";
  }
  function show(el, visible) { if (el) el.hidden = !visible; }

  function fill(select, firstLabel, items, previous) {
    select.innerHTML = "";
    var first = document.createElement("option");
    first.value = ""; first.textContent = firstLabel;
    select.appendChild(first);
    items.forEach(function (it) {
      var opt = document.createElement("option");
      opt.value = it.value; opt.textContent = it.label;
      select.appendChild(opt);
    });
    select.value = items.some(function (it) { return it.value === previous; }) ? previous : "";
  }

  function buildZones(region, zones) {
    if (zonesBuiltFor === region) return;
    fill(zoneSelect, "Choisissez votre zone", zones.map(function (z) {
      return { value: z.name, label: z.name + " \u2014 " + fmt(z.fee) };
    }), zoneSelect.value);
    zonesBuiltFor = region;
  }

  function buildLocalities(key, localities) {
    if (localitiesBuiltFor === key) return;
    fill(localitySelect, "Choisissez votre ville / localité", localities.map(function (l) {
      return { value: l, label: l };
    }), localitySelect.value);
    localitiesBuiltFor = key;
  }

  function update() {
    var region = regionSelect.value;
    var cfg = Object.prototype.hasOwnProperty.call(config, region) ? config[region] : null;
    var fee = null, shippingText = "Sélectionnez votre région";

    if (cfg && cfg.zones) {
      buildZones(region, cfg.zones);
      var zone = null;
      cfg.zones.forEach(function (z) { if (z.name === zoneSelect.value) zone = z; });
      show(zoneGroup, true);
      if (zoneHelp) { zoneHelp.textContent = cfg.help || ""; show(zoneHelp, !!cfg.help); }
      if (zone && zone.locality) {
        buildLocalities(region + "|" + zone.name, zone.localities);
        show(localityGroup, true);
        show(otherGroup, localitySelect.value === "Autre");
      } else {
        localitiesBuiltFor = null;
        show(localityGroup, false); show(otherGroup, false);
      }
      sumRegion.textContent = region;
      show(sumZoneRow, !!zone);
      sumZone.textContent = zone ? zone.name : "";
      if (zone) { fee = zone.fee; } else { shippingText = "Choisissez votre zone de livraison"; }
    } else {
      zonesBuiltFor = null; localitiesBuiltFor = null;
      show(zoneGroup, false); show(localityGroup, false); show(otherGroup, false); show(sumZoneRow, false);
      if (cfg) {
        if (zoneSelect) zoneSelect.value = "";
        sumRegion.textContent = region;
        fee = cfg.fee;
      } else {
        sumRegion.textContent = "\u2014";
      }
    }

    sumShipping.textContent = fee === null ? shippingText : fmt(fee);
    sumTotal.textContent = fmt(subtotal + (fee || 0));
  }

  regionSelect.addEventListener("change", update);
  zoneSelect.addEventListener("change", update);
  localitySelect.addEventListener("change", update);
  update();
});

// Guide des tailles : fenêtre (modal) simple, texte + tableau.
document.addEventListener("DOMContentLoaded", function () {
  var lastFocus = null;
  function openModal(modal) {
    lastFocus = document.activeElement;
    modal.hidden = false;
    document.body.classList.add("modal-open");
    var close = modal.querySelector("[data-close-modal]");
    if (close) close.focus();
  }
  function closeModal(modal) {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  document.querySelectorAll("[data-open-modal]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var modal = document.getElementById(btn.getAttribute("data-open-modal"));
      if (modal) openModal(modal);
    });
  });
  document.querySelectorAll(".modal").forEach(function (modal) {
    modal.addEventListener("click", function (e) {
      if (e.target === modal || e.target.hasAttribute("data-close-modal")) closeModal(modal);
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    document.querySelectorAll(".modal").forEach(function (modal) { if (!modal.hidden) closeModal(modal); });
  });
});
