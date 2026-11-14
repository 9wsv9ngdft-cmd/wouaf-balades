// Wouaf Balades : rappels (notifications) envoyés aux iPhones des promeneurs.
// À coller tel quel dans un Worker Cloudflare, avec :
//   - une base KV liée sous le nom WOUAF
//   - un déclencheur Cron « */15 * * * * » (toutes les 15 minutes)
// Aucune position n'est jamais reçue ni gardée ici : seulement le prénom, les horaires choisis
// et quelques compteurs du jeu (série, coffre, défi, résumé de la semaine).

const APP_URL = "https://9wsv9ngdft-cmd.github.io/wouaf-balades/";
const TZ = "Europe/Paris";
const DOG = "Roxy";
const MAX_USERS = 30;
// Code du superviseur (pause de l'app) : variable secrète SUPERVISOR_CODE dans les réglages du Worker,
// pour qu'il ne soit pas visible dans ce fichier public.
const PUSH_HOSTS = ["push.apple.com", "googleapis.com", "push.services.mozilla.com", "notify.windows.com"];

// ---------- petites aides ----------
const enc = new TextEncoder();
const b64u = buf => { let s = ""; for (const b of new Uint8Array(buf)) s += String.fromCharCode(b); return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); };
const unb64u = s => { s = s.replace(/-/g, "+").replace(/_/g, "/"); while (s.length % 4) s += "="; return Uint8Array.from(atob(s), c => c.charCodeAt(0)); };
const concat = (...a) => { const out = new Uint8Array(a.reduce((n, x) => n + x.length, 0)); let o = 0; for (const x of a){ out.set(x, o); o += x.length; } return out; };
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type" };
const json = (o, status) => new Response(JSON.stringify(o), { status: status || 200, headers: Object.assign({ "Content-Type": "application/json" }, CORS) });

// heure locale (Paris) d'un instant
function local(ts){
  const p = {};
  for (const x of new Intl.DateTimeFormat("en-GB", { timeZone: TZ, year:"numeric", month:"numeric", day:"numeric", hour:"2-digit", minute:"2-digit", hourCycle:"h23", weekday:"short" }).formatToParts(new Date(ts))) p[x.type] = x.value;
  return { y:+p.year, m:+p.month, d:+p.day, h:+p.hour, min:+p.minute, dow:["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].indexOf(p.weekday) };
}
// même « jour » que l'app : la journée commence à 4 h
const dayKey = ts => { const l = local(ts - 4*3600000); return `${l.y}-${l.m}-${l.d}`; };
// lundi de la semaine (même clé que l'app)
const weekKey = ts => { const l = local(ts - 4*3600000); return dayKey(ts - ((l.dow + 6) % 7) * 86400000); };
const fmtMin = m => { m = Math.round(m); return m < 60 ? `${m} min` : `${Math.floor(m/60)} h${m % 60 ? " " + String(m % 60).padStart(2, "0") : ""}`; };
const isoDay = ts => { const l = local(ts - 4*3600000); return `${l.y}-${String(l.m).padStart(2, "0")}-${String(l.d).padStart(2, "0")}`; };
// même calcul que l'app : la durée ne paie qu'au-delà des 20 min obligatoires
const walkEuros = min => min <= 20 ? 0 : Math.round((0.35 * Math.pow(min / 25, 1.5) - 0.35 * Math.pow(20 / 25, 1.5)) * 100) / 100;
// 🪙 Clebsous : la monnaie de l'app (100 clebsous = 1 €)
const fmtEur = v => { const n = Math.round((v || 0) * 100); return n.toLocaleString("fr-FR") + (n > 1 ? " clebsous" : " clebsou"); };

// ---------- clés VAPID (créées une seule fois, gardées dans KV) ----------
async function vapid(env, create){
  let v = await env.WOUAF.get("vapid", "json");
  if (!v && create){
    const k = await crypto.subtle.generateKey({ name:"ECDSA", namedCurve:"P-256" }, true, ["sign", "verify"]);
    v = { pub: b64u(await crypto.subtle.exportKey("raw", k.publicKey)), jwk: await crypto.subtle.exportKey("jwk", k.privateKey) };
    await env.WOUAF.put("vapid", JSON.stringify(v));
  }
  return v;
}
async function vapidHeader(v, endpoint){
  const aud = new URL(endpoint).origin;
  const head = b64u(enc.encode(JSON.stringify({ typ:"JWT", alg:"ES256" })));
  const body = b64u(enc.encode(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + 12*3600, sub: APP_URL })));
  const key = await crypto.subtle.importKey("jwk", v.jwk, { name:"ECDSA", namedCurve:"P-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign({ name:"ECDSA", hash:"SHA-256" }, key, enc.encode(head + "." + body));
  return `vapid t=${head}.${body}.${b64u(sig)}, k=${v.pub}`;
}

// ---------- chiffrement du message (RFC 8291, aes128gcm) ----------
async function hkdf(salt, ikm, info, bytes){
  const k = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({ name:"HKDF", hash:"SHA-256", salt, info }, k, bytes * 8));
}
async function encrypt(sub, text){
  const uaPub = unb64u(sub.keys.p256dh), auth = unb64u(sub.keys.auth);
  const as = await crypto.subtle.generateKey({ name:"ECDH", namedCurve:"P-256" }, true, ["deriveBits"]);
  const asPub = new Uint8Array(await crypto.subtle.exportKey("raw", as.publicKey));
  const uaKey = await crypto.subtle.importKey("raw", uaPub, { name:"ECDH", namedCurve:"P-256" }, false, []);
  const secret = new Uint8Array(await crypto.subtle.deriveBits({ name:"ECDH", public: uaKey }, as.privateKey, 256));
  const ikm = await hkdf(auth, secret, concat(enc.encode("WebPush: info\0"), uaPub, asPub), 32);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, enc.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, enc.encode("Content-Encoding: nonce\0"), 12);
  const key = await crypto.subtle.importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name:"AES-GCM", iv: nonce }, key, concat(enc.encode(text), new Uint8Array([2]))));
  const head = new Uint8Array(21); head.set(salt); new DataView(head.buffer).setUint32(16, 4096); head[20] = 65;
  return concat(head, asPub, ct);
}
async function push(env, v, sub, msg){
  const body = await encrypt(sub, JSON.stringify(msg));
  const r = await fetch(sub.endpoint, { method:"POST", body, headers:{
    "Authorization": await vapidHeader(v, sub.endpoint), "Content-Encoding":"aes128gcm",
    "Content-Type":"application/octet-stream", "TTL":"3600", "Urgency":"normal" } });
  return r.status;
}

// ---------- quel message envoyer ----------
const GENERIC = [
  n => `${DOG} t'attend${n ? ", " + n : ""} ! Une petite balade ? 🐾`,
  () => `Des 🦴 et des 🎾 à ramasser aujourd'hui. Tu pars à la chasse avec ${DOG} ?`,
  () => `Et si tu changeais de trajet ? Les rues pas faites depuis 15 jours rapportent double 🗺️`,
  () => `Au-delà des 20 min, ça rapporte : 1 h = ${Math.round(walkEuros(60) * 100)} clebsous 🪙 + les bonus. Plus c'est long, plus ça rapporte.`,
  () => `${DOG} a besoin de se dégourdir les pattes. C'est le moment ? 🐕`
];
function pickMessage(u, slot, now){
  const s = u.state || {}, n = u.walker || "", today = dayKey(now), l = local(now);
  const walked = s.sd === today;
  const danger = (s.sn || 0) >= 2 && s.sd === dayKey(now - 86400000);
  const hot = s.hot && now >= s.hot;
  const defi = s.defis && s.defis[today];
  const dayNo = Math.floor(now / 86400000);
  // dimanche soir : le résumé de la semaine
  if (slot === 1 && l.dow === 0){
    const w = s.wk && s.wk.k === weekKey(now) ? s.wk : { n:0, min:0, eur:0 };
    if (walked) return { title:`🏅 Ta semaine avec ${DOG}`, body:`${w.n} balade${w.n > 1 ? "s" : ""} · ${fmtMin(w.min)} · 🪙 ${fmtEur(w.eur)}. Bravo ${n} !` };
    return { title:`🏅 Ta semaine avec ${DOG}`, body: w.n
      ? `${w.n} balade${w.n > 1 ? "s" : ""} · ${fmtMin(w.min)} · 🪙 ${fmtEur(w.eur)}. Une dernière ce soir pour finir en beauté ?`
      : `Pas encore de balade cette semaine. ${DOG} compte sur toi ce soir 🐾` };
  }
  if (walked) return null;   // déjà sortie aujourd'hui : on ne dérange pas
  if (slot === 1 && danger) return { title:`🔥 Série de ${s.sn} jours en danger !`, body:`Sors ${DOG} au moins 20 min ce soir pour la garder.` };
  const boosted = (s.boost || []).some(p => isoDay(now) >= p.from && isoDay(now) <= p.to);
  if (boosted) return { title:"🎉 Bonus ×2 aujourd'hui !", body:`Tous les bonus comptent double. Pars à la chasse avec ${DOG} !` };
  const gain = { title:"⏳ Pas encore de balade aujourd'hui", body:`Au moins 20 min avec ${DOG}, c'est obligatoire. Et au-delà : 45 min ${fmtEur(walkEuros(45))} · 1 h ${fmtEur(walkEuros(60))} + les bonus. Ne passe pas à côté !` };
  if (slot === 1) return gain;
  const ideas = [gain];
  if (defi) ideas.push({ title:"🎯 Défi du jour", body:`${defi} (+10 clebsous)` });
  if (hot) ideas.push({ title:"🔥 Le coffre est chaud !", body:`💰 500 clebsous peuvent se cacher sur une rue que tu n'as pas prise depuis longtemps. Pars à la chasse avec ${DOG} ?` });
  const g = GENERIC[(dayNo + slot) % GENERIC.length];
  ideas.push({ title:"Wouaf Balades 🐾", body: g(n) });
  return ideas[(dayNo * 2 + slot) % ideas.length];
}

// ---------- envoi programmé ----------
async function run(env, now){
  const v = await vapid(env, false); if (!v) return;
  const l = local(now), nowMin = l.h * 60 + l.min, date = `${l.y}-${l.m}-${l.d}`;
  const pauses = (await env.WOUAF.get("pauses", "json")) || [];
  const boosts = (await env.WOUAF.get("boosts", "json")) || [];
  const today = isoDay(now);
  if (pauses.some(p => today >= p.from && today <= p.to)) return;   // pause du superviseur : aucun rappel
  const admin = await env.WOUAF.get("admin");
  const list = await env.WOUAF.list({ prefix:"u:" });
  for (const k of list.keys){
    const id = k.name.slice(2);
    const u = await env.WOUAF.get(k.name, "json"); if (!u) continue;
    if (admin && normName(u.walker) === SUP_NAME) continue;   // Éric = testeur : pas de rappels
    const day = (u.sched || [])[l.dow] || [];
    const sent = (await env.WOUAF.get("s:" + id, "json")) || {};
    let changed = false;
    for (const slot of [0, 1]){
      const t = day[slot]; if (!t || !/^\d\d:\d\d$/.test(t)) continue;
      const tm = +t.slice(0, 2) * 60 + +t.slice(3);
      if (nowMin < tm || nowMin - tm >= 30 || sent[slot] === date) continue;
      sent[slot] = date; changed = true;
      const msg = pickMessage(Object.assign({}, u, { state: Object.assign({}, u.state, { boost: boosts }) }), slot, now);
      if (!msg) continue;
      msg.url = APP_URL; msg.tag = "wouaf";
      try{
        const st = await push(env, v, u.sub, msg);
        if (st === 404 || st === 410){ await env.WOUAF.delete(k.name); await env.WOUAF.delete("s:" + id); changed = false; break; }
      }catch(e){}
    }
    if (changed) await env.WOUAF.put("s:" + id, JSON.stringify(sent));
  }
}

// ---------- adresses appelées par l'app ----------
function okSub(sub){
  try{
    const h = new URL(sub.endpoint).hostname;
    return sub.endpoint.startsWith("https://") && PUSH_HOSTS.some(x => h === x || h.endsWith("." + x)) && sub.keys && sub.keys.p256dh && sub.keys.auth;
  }catch(e){ return false; }
}
const slug = w => String(w || "").toLowerCase().trim().replace(/[^a-z0-9àâäéèêëîïôöùûüç-]/g, "_").slice(0, 30);
const okId = id => typeof id === "string" && /^[A-Za-z0-9-]{8,64}$/.test(id);
// 🔑 Superviseur « Éric » : le premier téléphone qui prend ce prénom (sans accents ni majuscules) le réclame (POST /claim) et reçoit un jeton
// aléatoire gardé dans KV « admin ». Les routes superviseur acceptent ce jeton OU le code SUPERVISOR_CODE.
const normName = w => String(w || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
const SUP_NAME = "eric";
const safeEq = (a, b) => { a = String(a); b = String(b); if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; };
const newToken = () => b64u(crypto.getRandomValues(new Uint8Array(24)));
async function supOk(env, b){
  if (!b) return false;
  if (env.SUPERVISOR_CODE && b.code != null && safeEq(b.code, env.SUPERVISOR_CODE)) return true;
  if (typeof b.token === "string" && b.token.length >= 16){
    const a = await env.WOUAF.get("admin", "json");
    if (a && a.token && safeEq(a.token, b.token)) return true;
  }
  return false;
}
async function isTester(env, walker){ return normName(walker) === SUP_NAME && !!(await env.WOUAF.get("admin")); }
// efface toutes les clés d'un préfixe : on relit la liste depuis le début tant qu'il en reste (pas de curseur à garder entre deux suppressions)
async function wipe(env, prefix){
  const done = new Set();
  for (let i = 0; i < 200; i++){
    const l = await env.WOUAF.list({ prefix });
    const todo = l.keys.filter(k => !done.has(k.name));
    if (!todo.length) break;
    for (const k of todo){ await env.WOUAF.delete(k.name); done.add(k.name); }
  }
  return done.size;
}
// trésors de la semaine déjà trouvés : [{ wk, by }]
async function treasures(env){
  const l = await env.WOUAF.list({ prefix:"t:" }), out = [];
  for (const k of l.keys.slice(0, 20)){ const by = await env.WOUAF.get(k.name); if (by) out.push({ wk: k.name.slice(2), by }); }
  return out;
}
// dernière vraie sortie de Roxy (balades annulées exclues), recalculée à partir des chiffres de chaque promeneur
async function recomputeLast(env){
  const l = await env.WOUAF.list({ prefix:"d:" });
  let best = null;
  for (const k of l.keys){
    const d = await env.WOUAF.get(k.name, "json"); if (!d) continue;
    for (const w of d.walks || []) if (!w.v && (!best || w.e > best.t)) best = { walker: d.walker, t: w.e, min: w.min };
  }
  if (best) await env.WOUAF.put("last", JSON.stringify(best)); else await env.WOUAF.delete("last");
}
const cleanSched = s => Array.from({ length:7 }, (_, i) => [0, 1].map(j => { const t = s && s[i] && s[i][j]; return typeof t === "string" && /^\d\d:\d\d$/.test(t) ? t : ""; }));
const cleanState = s => (s && typeof s === "object" && JSON.stringify(s).length < 3000) ? s : {};

export default {
  async fetch(req, env, ctx){
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
    const path = new URL(req.url).pathname;
    if (req.method === "GET" && path === "/key"){
      const v = await vapid(env, true);
      return json({ key: v.pub });
    }
    if (req.method === "GET" && path === "/") return json({ ok:true, app:"Wouaf Balades : rappels" });
    // infos communes lues par l'app à l'ouverture : pauses, jours boostés, dernière balade de Roxy (tous promeneurs)
    // ✏️ corrections du superviseur à appliquer sur le téléphone d'un promeneur
    if (req.method === "GET" && path === "/adjust"){
      const w = new URL(req.url).searchParams.get("w");
      return json({ list: (w && await env.WOUAF.get("a:" + slug(w), "json")) || [] });
    }
    // 🐾 dernières sorties de Roxy, tous promeneurs : qui, quand, durée, km, pipi/caca (ni trajet, ni position, ni argent)
    if (req.method === "GET" && path === "/recent"){
      const l = await env.WOUAF.list({ prefix:"d:" }), all = [];
      for (const k of l.keys){ const d = await env.WOUAF.get(k.name, "json"); if (d) for (const x of (d.walks || []).slice(0, 20)) all.push({ w: d.walker, s: x.s, e: x.e, min: x.min, m: x.m, pp: x.pp, cc: x.cc, v: x.v ? 1 : 0 }); }
      all.sort((a, b) => b.e - a.e);
      return json({ walks: all.slice(0, 25) });
    }
    if (req.method === "GET" && path === "/pause") return json({ pauses: (await env.WOUAF.get("pauses", "json")) || [], boosts: (await env.WOUAF.get("boosts", "json")) || [], last: await env.WOUAF.get("last", "json"), reset: (await env.WOUAF.get("reset", "json")) || 0, treasure: await treasures(env) });
    if (req.method !== "POST") return json({ error:"not found" }, 404);
    let b; try{ b = JSON.parse(await req.text()); }catch(e){ return json({ error:"bad json" }, 400); }
    if (path === "/claim"){   // 🔑 le 1er téléphone qui prend le prénom Éric devient superviseur ; les autres sont refusés
      if (!b || normName(b.walker) !== SUP_NAME) return json({ error:"not supervisor name" }, 400);
      const a = await env.WOUAF.get("admin", "json");
      if (!a){
        const token = newToken();
        await env.WOUAF.put("admin", JSON.stringify({ token, walker: String(b.walker).slice(0, 30), at: Date.now() }));
        return json({ ok:true, token, created:true });
      }
      if (typeof b.token === "string" && safeEq(a.token, b.token)) return json({ ok:true, token: a.token });
      return json({ error:"taken" }, 403);
    }
    if (path === "/check" || path === "/pause" || path === "/boost" || path === "/dash" || path === "/restore" || path === "/adjust" || path === "/reset" || path === "/void"){
      // routes superviseur : jeton d'Éric OU code superviseur (20 essais ratés par jour au plus)
      const fk = "fails:" + isoDay(Date.now()), fails = +((await env.WOUAF.get(fk)) || 0);
      if (fails >= 20) return json({ error:"too many" }, 429);
      if (!(await supOk(env, b))){ await env.WOUAF.put(fk, String(fails + 1), { expirationTtl: 172800 }); return json({ error:"bad code" }, 403); }
      if (path === "/check") return json({ ok:true });   // vérifie seulement le code (ex. « payé ✓ » dans l'app)
      if (path === "/dash"){   // 📊 tableau de bord : chiffres de chaque promeneur (jamais de position)
        const l = await env.WOUAF.list({ prefix:"d:" });
        const all = [];
        for (const k of l.keys){ const d = await env.WOUAF.get(k.name, "json"); if (d) all.push(d); }
        return json({ ok:true, walkers: all, last: await env.WOUAF.get("last", "json") });
      }
      if (path === "/restore"){   // ♻️ sauvegarde d'un promeneur, pour un nouveau téléphone
        const d = await env.WOUAF.get("b:" + slug(b.walker), "json");
        if (!b.walker) { const l = await env.WOUAF.list({ prefix:"b:" }); return json({ ok:true, names: l.keys.map(k => k.name.slice(2)) }); }
        return d ? json({ ok:true, backup: d }) : json({ error:"none" }, 404);
      }
      if (path === "/reset"){   // 🧹 remise à zéro de tout le monde : chiffres, sauvegardes, corrections, trésor. On garde rappels, pauses, jours bonus
        const n = (await wipe(env, "d:")) + (await wipe(env, "b:")) + (await wipe(env, "a:")) + (await wipe(env, "t:")) + (await wipe(env, "duo:"));
        await env.WOUAF.delete("last");
        const reset = Date.now();
        await env.WOUAF.put("reset", JSON.stringify(reset));
        return json({ ok:true, reset, deleted: n });
      }
      if (path === "/void"){   // ❌ annuler une balade (id = fin de la balade, en secondes) avec un motif : le téléphone retire les gains
        const w = String(b.walker || "").slice(0, 30), e = Math.round(+b.e || 0);
        if (!w || !e) return json({ error:"bad" }, 400);
        const dk = "d:" + slug(w), d = await env.WOUAF.get(dk, "json");
        const walk = d && (d.walks || []).find(x => x.e === e);
        if (!walk) return json({ error:"walk not found" }, 404);
        const why = String(b.why || "").slice(0, 120);
        walk.v = why || "annulée";
        await env.WOUAF.put(dk, JSON.stringify(d));
        const k = "a:" + slug(w), l = ((await env.WOUAF.get(k, "json")) || []).filter(x => x.id !== "v" + e);
        l.push({ id: "v" + e, type:"void", e, why, t: Date.now() });
        await env.WOUAF.put(k, JSON.stringify(l.slice(-50)));
        await recomputeLast(env);
        return json({ ok:true });
      }
      if (path === "/adjust"){   // ✏️ ajouter / retirer des clebsous avec un motif
        const w = String(b.walker || "").slice(0, 30), cs = Math.round(+b.cs || 0);
        if (!w || !cs || Math.abs(cs) > 100000) return json({ error:"bad" }, 400);
        const k = "a:" + slug(w), l = (await env.WOUAF.get(k, "json")) || [];
        l.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), cs, why: String(b.why || "").slice(0, 120), t: Date.now() });
        await env.WOUAF.put(k, JSON.stringify(l.slice(-50)));
        return json({ ok:true });
      }
      const ok = d => typeof d === "string" && /^\d{4}-\d\d-\d\d$/.test(d);
      if (path === "/boost"){   // 🎉 jours à bonus ×2
        const boosts = (Array.isArray(b.boosts) ? b.boosts : []).filter(p => p && ok(p.from) && ok(p.to) && p.from <= p.to).slice(-20).map(p => ({ from: p.from, to: p.to }));
        await env.WOUAF.put("boosts", JSON.stringify(boosts));
        return json({ ok:true, boosts });
      }
      const pauses = (Array.isArray(b.pauses) ? b.pauses : []).filter(p => p && ok(p.from) && ok(p.to) && p.from <= p.to).slice(-20).map(p => ({ from: p.from, to: p.to }));
      await env.WOUAF.put("pauses", JSON.stringify(pauses));
      return json({ ok:true, pauses });
    }
    if (path === "/backup"){   // 💾 sauvegarde automatique du jeu et de la tirelire d'un promeneur (pas de trajets)
      const w = String(b.walker || "").slice(0, 30), txt = JSON.stringify(b.data || null);
      if (!w || !b.data || txt.length > 2000000) return json({ error:"bad" }, 400);
      await env.WOUAF.put("b:" + slug(w), JSON.stringify({ walker: w, at: Date.now(), data: b.data }));
      return json({ ok:true });
    }
    if (path === "/duo"){   // 👯 balade à deux : les deux promeneurs touchent « On est à deux » pendant la même balade
      const w = String(b.walker || "").slice(0, 30), st = +b.s || 0, now = Date.now();
      if (!w || !st) return json({ error:"bad" }, 400);
      if (b.press) await env.WOUAF.put("duo:" + slug(w), JSON.stringify({ walker: w, s: st, t: now }), { expirationTtl: 6 * 3600 });
      const l = await env.WOUAF.list({ prefix:"duo:" });
      for (const k of l.keys){
        if (k.name === "duo:" + slug(w)) continue;
        const o = await env.WOUAF.get(k.name, "json");
        if (o && Math.abs(o.s - st) < 45 * 60000 && now - o.t < 4 * 3600000) return json({ partner: o.walker });
      }
      return json({ partner: null });
    }
    if (path === "/treasure"){   // 🏴‍☠️ premier à trouver le trésor de la semaine (aucune position reçue)
      const wk = String(b.week || "").slice(0, 12), w = String(b.walker || "").slice(0, 30);
      if (!wk || !w) return json({ error:"bad" }, 400);
      if (await isTester(env, w)) return json({ first:false, test:true });   // le téléphone d'Éric (testeur) ne prend jamais le trésor
      // un seul gagnant : le premier. Les autres reçoivent « déjà trouvé » et le trésor disparaît pour tout le monde
      const by = await env.WOUAF.get("t:" + wk);
      if (!by){ await env.WOUAF.put("t:" + wk, w, { expirationTtl: 60*86400 }); return json({ first:true, by:w }); }
      return json({ first: by === w, found:true, by });
    }
    if (path === "/walk"){   // une balade terminée : chiffres seulement (durée, distance, clebsous…), jamais le trajet
      const w = String(b.walker || "").slice(0, 30), x = b.walk || {};
      if (!w || !x.e) return json({ error:"bad" }, 400);
      const num = v => Math.max(0, Math.min(1e7, Math.round(+v || 0))), ts = v => Math.max(0, Math.min(4e9, Math.round(+v || 0)));
      const walk = { s: ts(x.s), e: ts(x.e), min: num(x.min), m: num(x.m), cs: num(x.cs), pp: num(x.pp), cc: num(x.cc), cb: num(x.cb), df: x.df ? 1 : 0, ms: num(x.ms), tr: x.tr ? 1 : 0 };
      const rs = (await env.WOUAF.get("reset", "json")) || 0;
      if (rs && walk.e * 1000 < rs) return json({ ok:true, ignored:true });   // balade d'avant la remise à zéro (envoi en retard)
      const dk = "d:" + slug(w);
      const d = (await env.WOUAF.get(dk, "json")) || { walker: w, walks: [] };
      if (!d.walks.some(y => y.e === walk.e)) d.walks.unshift(walk);
      d.walks = d.walks.slice(0, 60); d.walker = w; d.sum = cleanState(b.sum); d.at = Date.now();
      await env.WOUAF.put(dk, JSON.stringify(d));
      const last = await env.WOUAF.get("last", "json");
      // dernière sortie de Roxy (tous promeneurs) : sert à l'humeur de Roxy dans l'app. Pas de notification (le récap arrive déjà sur WhatsApp)
      if (!last || walk.e > last.t) await env.WOUAF.put("last", JSON.stringify({ walker: w, t: walk.e, min: walk.min }));
      return json({ ok:true });
    }
    if (!b || !okId(b.id)) return json({ error:"bad id" }, 400);
    const key = "u:" + b.id;
    if (path === "/register"){
      if (!okSub(b.sub)) return json({ error:"bad subscription" }, 400);
      if (await isTester(env, b.walker)) return json({ ok:true, skipped:true });   // Éric = testeur : pas de rappels
      const old = await env.WOUAF.get(key, "json");
      if (!old && (await env.WOUAF.list({ prefix:"u:" })).keys.length >= MAX_USERS) return json({ error:"full" }, 403);
      await env.WOUAF.put(key, JSON.stringify({ sub: b.sub, sched: cleanSched(b.sched), walker: String(b.walker || "").slice(0, 30), state: cleanState(b.state), at: Date.now() }));
      return json({ ok:true });
    }
    const u = await env.WOUAF.get(key, "json");
    if (path === "/unregister"){ await env.WOUAF.delete(key); await env.WOUAF.delete("s:" + b.id); return json({ ok:true }); }
    if (!u) return json({ error:"unknown" }, 404);
    if (path === "/state"){
      u.state = cleanState(b.state);
      if (b.walker) u.walker = String(b.walker).slice(0, 30);
      await env.WOUAF.put(key, JSON.stringify(u));
      return json({ ok:true });
    }
    if (path === "/test"){
      const v = await vapid(env, false);
      const st = await push(env, v, u.sub, { title:"Wouaf Balades 🐾", body:`Ça marche ! Tu recevras tes rappels aux heures choisies.`, url: APP_URL, tag:"wouaf-test" });
      return json({ ok: st >= 200 && st < 300, status: st });
    }
    return json({ error:"not found" }, 404);
  },
  async scheduled(event, env, ctx){
    ctx.waitUntil(run(env, event.scheduledTime || Date.now()));
  }
};
