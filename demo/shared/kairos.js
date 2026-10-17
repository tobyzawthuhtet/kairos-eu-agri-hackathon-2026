"use strict";
const K = (() => {
  const I = {
    leaf:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M5 19c0-8 5-13 15-14-1 9-6 14-15 14z"/><path d="M5 19l8-8"/></svg>',
    bell:'<svg viewBox="0 0 24 24"><path d="M6 17V11a6 6 0 1 1 12 0v6l1.5 2h-15z"/><path d="M10 21h4"/></svg>',
    plus:'<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
    chat:'<svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z"/></svg>',
    user:'<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-5 15-5 16 0"/></svg>',
    users:'<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-5 11-5 12 0"/><circle cx="17" cy="9" r="2.8"/><path d="M16.5 14c3.5-.3 5 1.8 5 4"/></svg>',
    drop:'<svg viewBox="0 0 24 24"><path d="M12 3C8 8 6 11 6 14a6 6 0 0 0 12 0c0-3-2-6-6-11z"/></svg>',
    cloud:'<svg viewBox="0 0 24 24"><path d="M7 15a4 4 0 1 1 1-7.9A5 5 0 0 1 18 9a3.5 3.5 0 0 1-.5 7"/><path d="M9 18v2M13 18v2M17 18v2"/></svg>',
    sun:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/></svg>',
    snow:'<svg viewBox="0 0 24 24"><path d="M12 2v20M4 7l16 10M20 7L4 17"/></svg>',
    wind:'<svg viewBox="0 0 24 24"><path d="M3 9h11a3 3 0 1 0-3-3M3 14h15a3 3 0 1 1-3 3M3 19h7"/></svg>',
    bug:'<svg viewBox="0 0 24 24"><ellipse cx="12" cy="14" rx="5" ry="6"/><path d="M12 8V4M7 12H3M17 12h4M8 18l-3 3M16 18l3 3"/></svg>',
    camera:'<svg viewBox="0 0 24 24"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>',
    send:'<svg viewBox="0 0 24 24"><path d="M21 3L3 11l7 3 3 7z"/><path d="M10 14l11-11"/></svg>',
    check:'<svg viewBox="0 0 24 24"><path d="M5 12l5 5 9-10"/></svg>',
    spark:'<svg viewBox="0 0 24 24"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg>',
    back:'<svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg>',
    x:'<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    chev:'<svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg>',
    pin:'<svg viewBox="0 0 24 24"><path d="M12 21s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    flag:'<svg viewBox="0 0 24 24"><path d="M5 21V4M5 5h12l-2 4 2 4H5"/></svg>',
  };
  const ICON_FOR = {irrigation:"drop", weather:"cloud", heat:"sun", frost:"snow", frost_inflorescence:"snow", cold_warning:"snow", wind:"wind", wind_hot_dry:"wind",
    heavy_rain:"cloud", rain_ahead:"cloud", soil_drying:"drop", water_use:"drop", community:"pin"};
  const sevClass = s => ({High:"high", Medium:"med", Low:"low", Info:"info"}[s] || "info");
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  async function api(path, body, method) {
    const r = await fetch("/demo" + path, body === undefined ? {} : {method: method || "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
    if (!r.ok) throw new Error(path + " " + r.status);
    return r.json();
  }
  const fmtDay = d => new Date(d + "T12:00:00").toLocaleDateString("en-GB", {weekday: "long", day: "numeric", month: "long"});
  const fmtLong = d => new Date(d + "T12:00:00").toLocaleDateString("en-GB", {weekday: "short", day: "numeric", month: "short", year: "numeric"});
  function toast(msg) {
    let t = document.querySelector(".toast");
    if (!t) { t = document.createElement("div"); t.className = "toast"; document.querySelector(".phone, body").appendChild(t); }
    t.textContent = msg; t.classList.add("on"); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("on"), 2600);
  }
  function photoPicker(max, onChange) { // returns {add(), list}, resizes to small JPEG thumbnails
    const list = [];
    const input = document.createElement("input"); input.type = "file"; input.accept = "image/*"; input.multiple = true; input.style.display = "none";
    document.body.appendChild(input);
    input.onchange = async () => {
      for (const f of input.files) {
        if (list.length >= max) break;
        const url = URL.createObjectURL(f), img = new Image();
        await new Promise(r => { img.onload = r; img.src = url; });
        const c = document.createElement("canvas"), s = 220 / Math.max(img.width, img.height);
        c.width = img.width * s; c.height = img.height * s; c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        list.push({label: "Photo " + (list.length + 1), thumb: c.toDataURL("image/jpeg", .6)}); URL.revokeObjectURL(url);
      }
      input.value = ""; onChange();
    };
    return {list, add: () => input.click(), remove: i => { list.splice(i, 1); onChange(); }};
  }
  const photosHtml = (list, max, prefix) => `<div class="photos">${list.slice(0, 2).map((p, i) => photoTile(p, i, prefix)).join("")}${list.length < max ? `<div class="photo add" data-add="${prefix}">${I.camera}Add photo</div>` : ""}${list.slice(2).map((p, i) => photoTile(p, i + 2, prefix)).join("")}</div>`;
  const photoTile = (p, i, prefix) => `<div class="photo">${p.thumb ? `<img src="${p.thumb}" alt="">` : ""}<i>${esc(p.label)}</i><button data-rm="${prefix}:${i}">×</button></div>`;
  return {I, ICON_FOR, sevClass, esc, api, fmtDay, fmtLong, toast, photoPicker, photosHtml};
})();
