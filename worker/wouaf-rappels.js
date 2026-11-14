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

// ---------- ⚔️ Duels entre promeneurs (v2.1) ----------
// KV « duels » = liste de tous les duels (petite famille). Un duel : { id, from, to, days (3|7), type ("walks"|"streets"), stake (0|25|50|100),
// status (pending | active | done | declined | expired | cancelled), created, start / end (jours « AAAA-MM-JJ » inclus, la journée commence à 4 h comme l'app),
// cancel: [prénoms qui veulent annuler], cells: { case: prénom } (guerre des rues, effacées à la fin), lost: { prénom: rues perdues }, res: { a, b, winner, why } }
const DUEL_DAYS = [3, 7], DUEL_STAKES = [0, 25, 50, 100], DUEL_TYPES = ["walks", "streets"];
const addDays = (iso, n) => { const d = new Date(iso + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
const same = (a, b) => normName(a) === normName(b);
const inDuel = (du, w) => same(du.from, w) || same(du.to, w);
const otherOf = (du, w) => same(du.from, w) ? du.to : du.from;
const isOpen = du => du.status === "pending" || du.status === "active";
async function pushTo(env, walker, title, body){   // notification à un promeneur (s'il a activé les rappels)
  try{
    const v = await vapid(env, false); if (!v) return;
    const l = await env.WOUAF.list({ prefix:"u:" });
    for (const k of l.keys){ const u = await env.WOUAF.get(k.name, "json"); if (u && same(u.walker, walker)) await push(env, v, u.sub, { title, body, url: APP_URL, tag:"wouaf-duel" }); }
  }catch(e){}
}
async function addAdj(env, walker, cs, why, id){   // les mises passent par les corrections (appliquées par le téléphone, hors plafond)
  const k = "a:" + slug(walker), adj = (await env.WOUAF.get(k, "json")) || [];
  if (adj.some(a => a.id === id)) return;
  adj.push({ id, cs, why, t: Date.now(), duel: 1 });
  await env.WOUAF.put(k, JSON.stringify(adj.slice(-50)));
}
// score : balades valides (≥ 20 min, pas annulées) faites pendant le duel ; à égalité, les minutes. Guerre des rues : nombre de rues possédées.
async function duelScore(env, du){
  if (du.type === "streets"){
    const c = { [du.from]: 0, [du.to]: 0 };
    for (const k in du.cells || {}){ const o = du.cells[k]; if (same(o, du.from)) c[du.from]++; else if (same(o, du.to)) c[du.to]++; }
    return { a: c[du.from], b: c[du.to], am: 0, bm: 0 };
  }
  const one = async w => { const d = await env.WOUAF.get("d:" + slug(w), "json"), r = { n: 0, m: 0 };
    for (const x of (d && d.walks) || []){ const day = isoDay(x.e * 1000); if (!x.v && x.min >= 20 && day >= du.start && day <= du.end){ r.n++; r.m += x.min; } }
    return r; };
  const A = await one(du.from), B = await one(du.to);
  return { a: A.n, b: B.n, am: A.m, bm: B.m };
}
async function finishDuel(env, du, winner, why){
  du.status = "done"; du.res = Object.assign(du.res || {}, { winner: winner || null, why: why || "end" }); du.doneAt = Date.now();
  delete du.cells;   // guerre des rues : plus aucune case gardée sur le serveur
  if (winner && du.stake){
    const loser = otherOf(du, winner);
    await addAdj(env, winner, du.stake, `⚔️ Duel gagné contre ${loser}`, "dw" + du.id);
    await addAdj(env, loser, -du.stake, `⚔️ Duel perdu contre ${winner}`, "dl" + du.id);
  }
  const txt = winner ? `${winner} a gagné le duel${why === "quit" ? " (abandon)" : ""}${du.stake ? ` : +${du.stake} clebsous` : ""} !` : "Égalité : chacun garde sa mise.";
  await pushTo(env, du.from, "⚔️ Duel terminé", txt); await pushTo(env, du.to, "⚔️ Duel terminé", txt);
}
// lit les duels et les met à jour : défi sans réponse au bout de 24 h = expiré ; duel fini (jour de fin passé) = résultat
async function getDuels(env, now){
  const l = (await env.WOUAF.get("duels", "json")) || [], today = isoDay(now);
  let changed = false;
  for (const du of l){
    if (du.status === "pending" && now - du.created > 24 * 3600000){ du.status = "expired"; changed = true; }
    else if (du.status === "active" && today > du.end){
      const sc = await duelScore(env, du); du.res = { a: sc.a, b: sc.b, am: sc.am, bm: sc.bm };
      const w = sc.a !== sc.b ? (sc.a > sc.b ? du.from : du.to) : (du.type === "walks" && sc.am !== sc.bm ? (sc.am > sc.bm ? du.from : du.to) : null);
      await finishDuel(env, du, w, "end"); changed = true;
    }
  }
  if (changed) await env.WOUAF.put("duels", JSON.stringify(l.slice(-60)));
  return l;
}
const saveDuels = (env, l) => env.WOUAF.put("duels", JSON.stringify(l.slice(-60)));
async function duelView(env, du){   // ce que voit l'app : sans les cases (sauf pour la carte, demandée à part)
  const o = Object.assign({}, du); delete o.cells;
  if (du.status === "active") o.score = await duelScore(env, du);
  return o;
}
// promeneurs qu'on peut défier : ceux qui ont déjà envoyé une balade ou une sauvegarde (Éric testeur exclu), avec leur tirelire du mois si connue
async function players(env){
  const out = {}, admin = await env.WOUAF.get("admin");
  for (const pre of ["d:", "b:"]){
    const l = await env.WOUAF.list({ prefix: pre });
    for (const k of l.keys){ const d = await env.WOUAF.get(k.name, "json"); const w = d && d.walker; if (!w || (admin && normName(w) === SUP_NAME)) continue;
      const key = normName(w); if (!out[key]) out[key] = { walker: w, cs: null }; if (pre === "d:" && d.sum && typeof d.sum.cs === "number") out[key].cs = d.sum.cs; }
  }
  return Object.values(out);
}
// 🏅 record du mois : la plus longue balade valide (≥ 20 min) du mois, tous promeneurs (Éric testeur exclu)
async function recomputeRecord(env, mk){
  const l = await env.WOUAF.list({ prefix:"d:" }), admin = await env.WOUAF.get("admin");
  let best = null;
  for (const k of l.keys){ const d = await env.WOUAF.get(k.name, "json"); if (!d || (admin && normName(d.walker) === SUP_NAME)) continue;
    for (const w of d.walks || []) if (!w.v && w.min >= 20 && isoDay(w.e * 1000).slice(0, 7) === mk && (!best || w.min > best.min)) best = { walker: d.walker, min: w.min, e: w.e }; }
  if (best) await env.WOUAF.put("rec:" + mk, JSON.stringify(best)); else await env.WOUAF.delete("rec:" + mk);
}

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
    if (req.method === "GET" && path === "/pause") return json({ pauses: (await env.WOUAF.get("pauses", "json")) || [], boosts: (await env.WOUAF.get("boosts", "json")) || [], last: await env.WOUAF.get("last", "json"), reset: (await env.WOUAF.get("reset", "json")) || 0, treasure: await treasures(env), record: await env.WOUAF.get("rec:" + isoDay(Date.now()).slice(0, 7), "json") });
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
      if (b.code != null && env.SUPERVISOR_CODE){   // 🔑 récupérer Éric avec le code (nouveau téléphone, Safari/icône, prénom volé) : l'ancien jeton ne marche plus
        const fk = "fails:" + isoDay(Date.now()), fails = +((await env.WOUAF.get(fk)) || 0);
        if (fails >= 20) return json({ error:"too many" }, 429);
        if (!safeEq(b.code, env.SUPERVISOR_CODE)){ await env.WOUAF.put(fk, String(fails + 1), { expirationTtl: 172800 }); return json({ error:"bad code" }, 403); }
        const token = newToken();
        await env.WOUAF.put("admin", JSON.stringify({ token, walker: String(b.walker).slice(0, 30), at: Date.now(), moved: true }));
        return json({ ok:true, token, moved:true });
      }
      return json({ error:"taken" }, 403);
    }
    if (path === "/alert"){   // 🚨 un promeneur prévient le superviseur (ex. balade annulée après avoir trouvé le trésor) : visible dans le tableau de bord
      const w = String(b.walker || "").slice(0, 30), wk = String(b.week || "").slice(0, 12);
      if (!w || b.kind !== "hunt") return json({ error:"bad" }, 400);
      const l = (await env.WOUAF.get("alerts", "json")) || [];
      if (!l.some(a => a.walker === w && a.kind === "hunt" && a.week === wk)) l.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), walker: w, kind:"hunt", week: wk, t: Date.now() });
      await env.WOUAF.put("alerts", JSON.stringify(l.slice(-30)));
      return json({ ok:true });
    }
    if (path === "/check" || path === "/pause" || path === "/boost" || path === "/dash" || path === "/restore" || path === "/adjust" || path === "/reset" || path === "/void" || path === "/alert-resolve" || path === "/duel-admin"){
      // routes superviseur : jeton d'Éric OU code superviseur (20 essais ratés par jour au plus)
      const fk = "fails:" + isoDay(Date.now()), fails = +((await env.WOUAF.get(fk)) || 0);
      if (fails >= 20) return json({ error:"too many" }, 429);
      if (!(await supOk(env, b))){ await env.WOUAF.put(fk, String(fails + 1), { expirationTtl: 172800 }); return json({ error:"bad code" }, 403); }
      if (path === "/check") return json({ ok:true });   // vérifie seulement le code (ex. « payé ✓ » dans l'app)
      if (path === "/dash"){   // 📊 tableau de bord : chiffres de chaque promeneur (jamais de position)
        const l = await env.WOUAF.list({ prefix:"d:" });
        const all = [];
        for (const k of l.keys){ const d = await env.WOUAF.get(k.name, "json"); if (d) all.push(d); }
        const dl = (await getDuels(env, Date.now())).filter(isOpen);
        return json({ ok:true, walkers: all, last: await env.WOUAF.get("last", "json"), alerts: (await env.WOUAF.get("alerts", "json")) || [], duels: await Promise.all(dl.map(du => duelView(env, du))) });
      }
      if (path === "/duel-admin"){   // ⚔️ le superviseur annule un duel en cours : chacun garde sa mise
        const l = await getDuels(env, Date.now()), du = l.find(x => x.id === b.id);
        if (!du || !isOpen(du)) return json({ error:"not found" }, 404);
        du.status = "cancelled"; du.by = "sup"; delete du.cells; await saveDuels(env, l);
        await pushTo(env, du.from, "⚔️ Duel annulé", "Le superviseur a annulé le duel : chacun garde sa mise."); await pushTo(env, du.to, "⚔️ Duel annulé", "Le superviseur a annulé le duel : chacun garde sa mise.");
        return json({ ok:true });
      }
      if (path === "/restore"){   // ♻️ sauvegarde d'un promeneur, pour un nouveau téléphone
        const d = await env.WOUAF.get("b:" + slug(b.walker), "json");
        if (!b.walker) { const l = await env.WOUAF.list({ prefix:"b:" }); return json({ ok:true, names: l.keys.map(k => k.name.slice(2)) }); }
        return d ? json({ ok:true, backup: d }) : json({ error:"none" }, 404);
      }
      if (path === "/reset"){   // 🧹 remise à zéro de tout le monde : chiffres, sauvegardes, corrections, trésor. On garde rappels, pauses, jours bonus
        const n = (await wipe(env, "d:")) + (await wipe(env, "b:")) + (await wipe(env, "a:")) + (await wipe(env, "t:")) + (await wipe(env, "duo:")) + (await wipe(env, "rec:"));
        await env.WOUAF.delete("duels");
        await env.WOUAF.delete("last"); await env.WOUAF.delete("alerts");
        const reset = Date.now();
        await env.WOUAF.put("reset", JSON.stringify(reset));
        return json({ ok:true, reset, deleted: n });
      }
      if (path === "/alert-resolve"){   // 🚨 le superviseur ignore l'alerte, ou redonne le trésor (500 clebsous, comme une correction)
        const l = (await env.WOUAF.get("alerts", "json")) || [], a = l.find(x => x.id === b.id);
        if (!a) return json({ error:"not found" }, 404);
        if (b.give){
          const k = "a:" + slug(a.walker), adj = (await env.WOUAF.get(k, "json")) || [];
          adj.push({ id: "g" + a.id, cs: 500, why: "Trésor de la semaine redonné par le superviseur", t: Date.now() });
          await env.WOUAF.put(k, JSON.stringify(adj.slice(-50)));
        }
        await env.WOUAF.put("alerts", JSON.stringify(l.filter(x => x.id !== a.id)));
        return json({ ok:true });
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
        await recomputeLast(env); await recomputeRecord(env, isoDay(e * 1000).slice(0, 7));
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
    if (path.startsWith("/duel")){   // ⚔️ duels entre promeneurs (prénom seulement, comme le reste de l'app)
      const now = Date.now(), w = String(b.walker || "").slice(0, 30);
      if (!w) return json({ error:"bad" }, 400);
      if (await isTester(env, w)) return json({ error:"tester" }, 403);   // 🧪 Éric ne fait pas de duel
      const l = await getDuels(env, now);
      if (path === "/duels"){   // mes duels (en attente, en cours, terminés depuis moins de 14 jours) + qui je peux défier
        const mine = l.filter(du => inDuel(du, w) && (isOpen(du) || now - (du.doneAt || du.created) < 14 * 86400000));
        return json({ ok:true, duels: await Promise.all(mine.map(du => duelView(env, du))), players: (await players(env)).filter(p => !same(p.walker, w)), today: isoDay(now) });
      }
      if (path === "/duel-new"){
        const to = String(b.to || "").slice(0, 30), days = +b.days, stake = +b.stake, type = String(b.type || "");
        if (!to || same(to, w) || !DUEL_DAYS.includes(days) || !DUEL_STAKES.includes(stake) || !DUEL_TYPES.includes(type)) return json({ error:"bad" }, 400);
        if (normName(to) === SUP_NAME && await env.WOUAF.get("admin")) return json({ error:"tester" }, 403);
        if (l.some(du => isOpen(du) && (inDuel(du, w) || inDuel(du, to)))) return json({ error:"busy" }, 409);   // 1 seul duel à la fois par personne
        const op = (await players(env)).find(p => same(p.walker, to));
        if (!op) return json({ error:"unknown" }, 404);
        if (stake > Math.max(0, +b.have || 0) || (op.cs != null && stake > op.cs)) return json({ error:"stake" }, 400);   // pas plus que la tirelire de chacun
        const du = { id: now.toString(36) + Math.random().toString(36).slice(2, 6), from: w, to: op.walker, days, type, stake, status:"pending", created: now };
        l.push(du); await saveDuels(env, l);
        await pushTo(env, op.walker, "⚔️ Nouveau défi !", `${w} te lance un duel de ${days} jours${stake ? `, mise ${stake} clebsous` : ""}. Tu as 24 h pour répondre.`);
        return json({ ok:true, duel: await duelView(env, du) });
      }
      const du = l.find(x => x.id === b.id);
      if (!du || !inDuel(du, w)) return json({ error:"not found" }, 404);
      if (path === "/duel-answer"){   // l'adversaire accepte ou refuse ; le duel commence demain (journée de l'app)
        if (du.status !== "pending" || !same(du.to, w)) return json({ error:"not pending" }, 409);
        if (!b.ok){ du.status = "declined"; await saveDuels(env, l); await pushTo(env, du.from, "⚔️ Défi refusé", `${du.to} a dit non merci cette fois.`); return json({ ok:true, duel: await duelView(env, du) }); }
        if (du.stake > Math.max(0, +b.have || 0)) return json({ error:"stake" }, 400);
        if (l.some(x => x !== du && x.status === "active" && (inDuel(x, du.from) || inDuel(x, du.to)))) return json({ error:"busy" }, 409);
        du.status = "active"; du.start = addDays(isoDay(now), 1); du.end = addDays(du.start, du.days - 1); du.cells = {}; du.lost = {};
        await saveDuels(env, l);
        await pushTo(env, du.from, "⚔️ Défi accepté !", `${du.to} a accepté. Le duel commence demain, ${du.days} jours.`);
        return json({ ok:true, duel: await duelView(env, du) });
      }
      if (path === "/duel-cancel"){   // annuler : défi en attente = retiré par celui qui l'a lancé ; duel en cours = seulement si les deux sont d'accord
        if (du.status === "pending"){ if (!same(du.from, w)) return json({ error:"no" }, 409); du.status = "cancelled"; du.by = w; await saveDuels(env, l); return json({ ok:true, duel: await duelView(env, du) }); }
        if (du.status !== "active") return json({ error:"not active" }, 409);
        du.cancel = du.cancel || []; if (!du.cancel.some(x => same(x, w))) du.cancel.push(w);
        if (du.cancel.length >= 2){ du.status = "cancelled"; du.by = "both"; delete du.cells; }
        await saveDuels(env, l);
        if (du.status === "cancelled") await pushTo(env, otherOf(du, w), "⚔️ Duel annulé", "Vous étiez d'accord tous les deux : chacun garde sa mise.");
        else await pushTo(env, otherOf(du, w), "⚔️ Annuler le duel ?", `${w} propose d'annuler le duel. Ouvre Wouaf pour répondre.`);
        return json({ ok:true, duel: await duelView(env, du) });
      }
      if (path === "/duel-quit"){   // abandon = défaite
        if (du.status !== "active") return json({ error:"not active" }, 409);
        du.res = Object.assign(await duelScore(env, du), { quit: w });
        await finishDuel(env, du, otherOf(du, w), "quit"); await saveDuels(env, l);
        return json({ ok:true, duel: await duelView(env, du) });
      }
      if (path === "/duel-map"){   // 🗺️ guerre des rues : les cases des deux joueurs, seulement pendant le duel
        if (du.type !== "streets" || du.status !== "active") return json({ error:"no map" }, 409);
        return json({ ok:true, cells: du.cells || {}, score: await duelScore(env, du) });
      }
      return json({ error:"not found" }, 404);
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
      const fresh = !d.walks.some(y => y.e === walk.e), out = { ok:true };
      if (fresh) d.walks.unshift(walk);
      d.walks = d.walks.slice(0, 60); d.walker = w; d.sum = cleanState(b.sum); d.at = Date.now();
      await env.WOUAF.put(dk, JSON.stringify(d));
      const last = await env.WOUAF.get("last", "json");
      // dernière sortie de Roxy (tous promeneurs) : sert à l'humeur de Roxy dans l'app. Pas de notification (le récap arrive déjà sur WhatsApp)
      if (!last || walk.e > last.t) await env.WOUAF.put("last", JSON.stringify({ walker: w, t: walk.e, min: walk.min }));
      const tester = await isTester(env, w), day = isoDay(walk.e * 1000);
      if (fresh && !tester && walk.min >= 20){
        // 🏅 record du mois : la plus longue balade valide
        const rk = "rec:" + day.slice(0, 7), rec = await env.WOUAF.get(rk, "json");
        if (!rec || walk.min > rec.min){ await env.WOUAF.put(rk, JSON.stringify({ walker: w, min: walk.min, e: walk.e })); out.record = { min: walk.min, prev: rec || null }; }
        // 🗺️ guerre des rues : les cases de cette balade (envoyées seulement pendant un duel « Guerre des rues »)
        if (Array.isArray(b.cells) && b.cells.length){
          const l = await getDuels(env, Date.now()), du = l.find(x => x.status === "active" && x.type === "streets" && inDuel(x, w) && day >= x.start && day <= x.end);
          if (du){
            const op = otherOf(du, w); let stolen = 0;
            du.cells = du.cells || {};
            for (const c of b.cells.slice(0, 400)){ if (typeof c !== "string" || !/^-?\d{1,6}:-?\d{1,6}$/.test(c)) continue; if (same(du.cells[c], op)) stolen++; du.cells[c] = w; }
            du.lost = du.lost || {}; if (stolen) du.lost[op] = (du.lost[op] || 0) + stolen;
            await saveDuels(env, l); out.stolen = stolen;
            if (stolen) await pushTo(env, op, "🗺️ Guerre des rues", `${w} t'a pris ${stolen} rue${stolen > 1 ? "s" : ""} !`);
          }
        }
      }
      return json(out);
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
    ctx.waitUntil(Promise.all([run(env, event.scheduledTime || Date.now()), getDuels(env, event.scheduledTime || Date.now())]));
  }
};
