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
// Code du superviseur pour mettre l'app en pause (à changer ici quand tu veux, puis « Déployer »)
const SUPERVISOR_CODE = "731948";
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
const walkEuros = min => Math.round(0.35 * Math.pow(min / 25, 1.5) * 100) / 100;
const fmtEur = v => (v || 0).toFixed(2).replace(".", ",") + " €";

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
  () => `Et si tu prenais une rue jamais faite ? Les coins neufs rapportent double 🗺️`,
  () => `25 min de balade ≈ 0,35 € dans ta tirelire 💶 Et plus c'est long, plus ça rapporte.`,
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
    if (walked) return { title:`🏅 Ta semaine avec ${DOG}`, body:`${w.n} balade${w.n > 1 ? "s" : ""} · ${fmtMin(w.min)} · 💶 ${fmtEur(w.eur)}. Bravo ${n} !` };
    return { title:`🏅 Ta semaine avec ${DOG}`, body: w.n
      ? `${w.n} balade${w.n > 1 ? "s" : ""} · ${fmtMin(w.min)} · 💶 ${fmtEur(w.eur)}. Une dernière ce soir pour finir en beauté ?`
      : `Pas encore de balade cette semaine. ${DOG} compte sur toi ce soir 🐾` };
  }
  if (walked) return null;   // déjà sortie aujourd'hui : on ne dérange pas
  if (slot === 1 && danger) return { title:`🔥 Série de ${s.sn} jours en danger !`, body:`Sors ${DOG} au moins 15 min ce soir pour la garder.` };
  const gain = { title:"⏳ Pas encore de balade aujourd'hui", body:`À gagner : 15 min ${fmtEur(walkEuros(15))} · 25 min ${fmtEur(walkEuros(25))} · 45 min ${fmtEur(walkEuros(45))} · 1 h ${fmtEur(walkEuros(60))}. Ne passe pas à côté !` };
  if (slot === 1) return gain;
  const ideas = [gain];
  if (defi) ideas.push({ title:"🎯 Défi du jour", body:`${defi} (+15 pts)` });
  if (hot) ideas.push({ title:"🔥 Le coffre est chaud !", body:`💰 5 € peuvent se cacher sur une rue que tu n'as jamais prise. Pars à la chasse avec ${DOG} ?` });
  const g = GENERIC[(dayNo + slot) % GENERIC.length];
  ideas.push({ title:"Wouaf Balades 🐾", body: g(n) });
  return ideas[(dayNo * 2 + slot) % ideas.length];
}

// ---------- envoi programmé ----------
async function run(env, now){
  const v = await vapid(env, false); if (!v) return;
  const l = local(now), nowMin = l.h * 60 + l.min, date = `${l.y}-${l.m}-${l.d}`;
  const pauses = (await env.WOUAF.get("pauses", "json")) || [];
  const today = isoDay(now);
  if (pauses.some(p => today >= p.from && today <= p.to)) return;   // pause du superviseur : aucun rappel
  const list = await env.WOUAF.list({ prefix:"u:" });
  for (const k of list.keys){
    const id = k.name.slice(2);
    const u = await env.WOUAF.get(k.name, "json"); if (!u) continue;
    const day = (u.sched || [])[l.dow] || [];
    const sent = (await env.WOUAF.get("s:" + id, "json")) || {};
    let changed = false;
    for (const slot of [0, 1]){
      const t = day[slot]; if (!t || !/^\d\d:\d\d$/.test(t)) continue;
      const tm = +t.slice(0, 2) * 60 + +t.slice(3);
      if (nowMin < tm || nowMin - tm >= 30 || sent[slot] === date) continue;
      sent[slot] = date; changed = true;
      const msg = pickMessage(u, slot, now);
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
const okId = id => typeof id === "string" && /^[A-Za-z0-9-]{8,64}$/.test(id);
const cleanSched = s => Array.from({ length:7 }, (_, i) => [0, 1].map(j => { const t = s && s[i] && s[i][j]; return typeof t === "string" && /^\d\d:\d\d$/.test(t) ? t : ""; }));
const cleanState = s => (s && typeof s === "object" && JSON.stringify(s).length < 3000) ? s : {};

export default {
  async fetch(req, env){
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
    const path = new URL(req.url).pathname;
    if (req.method === "GET" && path === "/key"){
      const v = await vapid(env, true);
      return json({ key: v.pub });
    }
    if (req.method === "GET" && path === "/") return json({ ok:true, app:"Wouaf Balades : rappels" });
    if (req.method === "GET" && path === "/pause") return json({ pauses: (await env.WOUAF.get("pauses", "json")) || [] });
    if (req.method !== "POST") return json({ error:"not found" }, 404);
    let b; try{ b = JSON.parse(await req.text()); }catch(e){ return json({ error:"bad json" }, 400); }
    if (path === "/pause"){
      // pause pour tous les promeneurs, seulement avec le code du superviseur (20 essais ratés par jour au plus)
      const fk = "fails:" + isoDay(Date.now()), fails = +((await env.WOUAF.get(fk)) || 0);
      if (fails >= 20) return json({ error:"too many" }, 429);
      if (!b || String(b.code) !== SUPERVISOR_CODE){ await env.WOUAF.put(fk, String(fails + 1), { expirationTtl: 172800 }); return json({ error:"bad code" }, 403); }
      const ok = d => typeof d === "string" && /^\d{4}-\d\d-\d\d$/.test(d);
      const pauses = (Array.isArray(b.pauses) ? b.pauses : []).filter(p => p && ok(p.from) && ok(p.to) && p.from <= p.to).slice(-20).map(p => ({ from: p.from, to: p.to }));
      await env.WOUAF.put("pauses", JSON.stringify(pauses));
      return json({ ok:true, pauses });
    }
    if (!b || !okId(b.id)) return json({ error:"bad id" }, 400);
    const key = "u:" + b.id;
    if (path === "/register"){
      if (!okSub(b.sub)) return json({ error:"bad subscription" }, 400);
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
