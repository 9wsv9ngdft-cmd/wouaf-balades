import test from "node:test";
import assert from "node:assert/strict";
import { loadWorker, makeEnv, client } from "./load-worker.mjs";

const setup = async () => { const worker = await loadWorker(), env = makeEnv(); return { worker, env, api: client(worker, env) }; };
const walk = (e, extra) => Object.assign({ s: e - 1800, e, min: 30, m: 2500, cs: 40 }, extra);

test("claim : le 1er téléphone qui prend « Éric » (sans accents ni majuscules) devient superviseur, les autres sont refusés", async () => {
  const { api, env } = await setup();
  const a = await api.post("/claim", { walker: "  ÉRIC " });
  assert.equal(a.status, 200); assert.ok(a.j.token && a.j.token.length >= 16);
  assert.equal((await api.post("/claim", { walker: "eric" })).status, 403);            // autre téléphone : refusé
  assert.equal((await api.post("/claim", { walker: "Éric", token: "faux" })).status, 403);
  const again = await api.post("/claim", { walker: "Eric", token: a.j.token });         // même téléphone : ok, même jeton
  assert.equal(again.status, 200); assert.equal(again.j.token, a.j.token);
  assert.equal((await api.post("/claim", { walker: "Léa" })).status, 400);              // un autre prénom ne réclame rien
  assert.ok(await env.WOUAF.get("admin"));
});

test("routes superviseur : jeton d'Éric OU code, rien d'autre ; 20 essais ratés maximum par jour", async () => {
  const { api } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  assert.equal((await api.post("/dash", { token: j.token })).status, 200);
  assert.equal((await api.post("/dash", { code: "1234" })).status, 200);
  assert.equal((await api.post("/dash", { token: "x".repeat(32) })).status, 403);
  assert.equal((await api.post("/dash", { code: "0000" })).status, 403);
  assert.equal((await api.post("/dash", {})).status, 403);
  for (let i = 0; i < 25; i++) await api.post("/dash", { code: "nope" });
  assert.equal((await api.post("/dash", { token: j.token })).status, 429);               // trop d'essais ratés aujourd'hui
});

test("sans SUPERVISOR_CODE, le code vide n'ouvre rien", async () => {
  const worker = await loadWorker(), env = makeEnv(undefined), api = client(worker, env);
  assert.equal((await api.post("/dash", { code: "undefined" })).status, 403);
  assert.equal((await api.post("/reset", { code: "" })).status, 403);
});

test("trésor : un seul gagnant ; les autres reçoivent « déjà trouvé » ; Éric (testeur) ne le prend jamais", async () => {
  const { api } = await setup();
  await api.post("/claim", { walker: "Éric" });
  assert.deepEqual((await api.post("/treasure", { week: "2026-11-9", walker: "Éric" })).j, { first:false, test:true });
  const a = await api.post("/treasure", { week: "2026-11-9", walker: "Léa" });
  assert.equal(a.j.first, true);
  const b = await api.post("/treasure", { week: "2026-11-9", walker: "Tom" });
  assert.equal(b.j.first, false); assert.equal(b.j.found, true); assert.equal(b.j.by, "Léa");
  assert.equal((await api.post("/treasure", { week: "2026-11-9", walker: "Léa" })).j.first, true);   // nouvelle tentative du gagnant (réseau)
  assert.equal((await api.post("/treasure", { week: "2026-11-16", walker: "Tom" })).j.first, true);  // autre semaine : nouveau trésor
  const p = (await api.get("/pause")).j;
  assert.deepEqual(p.treasure.map(t => [t.wk, t.by]).sort(), [["2026-11-16", "Tom"], ["2026-11-9", "Léa"]]);
});

test("balade annulée : motif, balade barrée, correction pour le téléphone, dernière sortie recalculée", async () => {
  const { api } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  await api.post("/walk", { walker: "Léa", walk: walk(1_700_000_000), sum: {} });
  await api.post("/walk", { walker: "Tom", walk: walk(1_700_005_000), sum: {} });
  assert.equal((await api.get("/pause")).j.last.walker, "Tom");
  assert.equal((await api.post("/void", { token: j.token, walker: "Tom", e: 1_700_005_000, why: "en voiture" })).status, 200);
  assert.equal((await api.post("/void", { token: j.token, walker: "Tom", e: 42, why: "?" })).status, 404);   // balade inconnue
  assert.equal((await api.post("/void", { token: "x".repeat(30), walker: "Tom", e: 1_700_005_000 })).status, 403);
  assert.equal((await api.get("/pause")).j.last.walker, "Léa");                          // la balade annulée ne compte plus pour l'humeur
  const adj = (await api.get("/adjust?w=Tom")).j.list;
  assert.deepEqual(adj.map(a => [a.type, a.e, a.why, a.id]), [["void", 1_700_005_000, "en voiture", "v1700005000"]]);
  const recent = (await api.get("/recent")).j.walks, tom = recent.find(x => x.w === "Tom");
  assert.equal(tom.v, 1); assert.equal(recent.find(x => x.w === "Léa").v, 0);
  const dash = (await api.post("/dash", { token: j.token })).j.walkers.find(d => d.walker === "Tom");
  assert.equal(dash.walks[0].v, "en voiture");
  await api.post("/void", { token: j.token, walker: "Tom", e: 1_700_005_000, why: "motif corrigé" });   // ré-annuler : pas de doublon
  assert.equal((await api.get("/adjust?w=Tom")).j.list.length, 1);
});

test("remise à zéro : efface chiffres, sauvegardes, corrections, trésor, dernière sortie ; garde rappels, pauses, admin", async () => {
  const { api, env } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  for (const w of ["Léa", "Tom", "Zoé", "Max"]){
    await api.post("/walk", { walker: w, walk: walk(1_700_000_000), sum: {} });
    await api.post("/backup", { walker: w, data: { jeu: { total: 5 } } });
    await api.post("/adjust", { token: j.token, walker: w, cs: 10, why: "x" });
  }
  await api.post("/treasure", { week: "2026-11-9", walker: "Léa" });
  await env.WOUAF.put("u:abc12345", JSON.stringify({ walker: "Léa", sched: [] }));
  await api.post("/pause", { token: j.token, pauses: [{ from: "2026-12-01", to: "2026-12-05" }] });
  assert.equal((await api.post("/reset", { code: "oups" })).status, 403);               // sans le bon code : rien ne bouge
  assert.ok(await env.WOUAF.get("d:léa") || await env.WOUAF.get("d:lea"));
  const r = await api.post("/reset", { token: j.token });
  assert.equal(r.status, 200); assert.ok(r.j.reset > 0); assert.ok(r.j.deleted >= 13);
  for (const pre of ["d:", "b:", "a:", "t:"]) assert.equal((await env.WOUAF.list({ prefix: pre })).keys.length, 0, pre);
  assert.equal(await env.WOUAF.get("last"), null);
  assert.ok(await env.WOUAF.get("u:abc12345")); assert.ok(await env.WOUAF.get("admin"));
  const p = (await api.get("/pause")).j;
  assert.equal(p.reset, r.j.reset); assert.equal(p.pauses.length, 1); assert.deepEqual(p.treasure, []); assert.equal(p.last, null);
  assert.deepEqual((await api.get("/recent")).j.walks, []);
  // envois en retard d'avant la remise à zéro : ignorés ; nouvelles balades : acceptées
  const old = await api.post("/walk", { walker: "Léa", walk: walk(1_700_000_000), sum: {} });
  assert.equal(old.j.ignored, true);
  const now = Math.floor(Date.now() / 1000) + 10;
  assert.equal((await api.post("/walk", { walker: "Léa", walk: walk(now), sum: {} })).j.ignored, undefined);
  assert.equal((await api.get("/recent")).j.walks.length, 1);
});

test("rappels : Éric (testeur) n'est jamais inscrit", async () => {
  const { api, env } = await setup();
  const sub = { endpoint: "https://web.push.apple.com/abc", keys: { p256dh: "a", auth: "b" } };
  const before = await api.post("/register", { id: "abcdefgh1", sub, sched: [], walker: "Éric" });
  assert.equal((await env.WOUAF.list({ prefix: "u:" })).keys.length, 1);                 // pas encore superviseur : inscrit comme les autres
  await api.post("/claim", { walker: "Éric" });
  await api.post("/register", { id: "abcdefgh2", sub, sched: [], walker: "éric" });
  assert.equal((await env.WOUAF.list({ prefix: "u:" })).keys.length, 1);                 // devenu testeur : plus d'inscription
  assert.equal(before.status, 200);
});

test("alerte trésor : balade annulée après la trouvaille → alerte pour Éric, qui peut redonner 500 clebsous ou ignorer", async () => {
  const { api } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  await api.post("/alert", { walker: "Léa", kind: "hunt", week: "2026-11-9" });
  await api.post("/alert", { walker: "Léa", kind: "hunt", week: "2026-11-9" });            // doublon ignoré
  await api.post("/alert", { walker: "Tom", kind: "hunt", week: "2026-11-9" });
  assert.equal((await api.post("/alert", { walker: "Tom", kind: "autre" })).status, 400);
  let al = (await api.post("/dash", { token: j.token })).j.alerts;
  assert.equal(al.length, 2);
  assert.equal((await api.post("/alert-resolve", { token: "x".repeat(30), id: al[0].id, give: true })).status, 403);
  assert.equal((await api.post("/alert-resolve", { token: j.token, id: al[0].id, give: true })).status, 200);   // redonner à Léa
  assert.equal((await api.post("/alert-resolve", { token: j.token, id: al[1].id })).status, 200);               // ignorer Tom
  assert.equal((await api.post("/dash", { token: j.token })).j.alerts.length, 0);
  const lea = (await api.get("/adjust?w=Léa")).j.list;
  assert.equal(lea.length, 1); assert.equal(lea[0].cs, 500);
  assert.equal((await api.get("/adjust?w=Tom")).j.list.length, 0);
  assert.equal((await api.post("/alert-resolve", { token: j.token, id: al[0].id })).status, 404);               // déjà traitée
});

test("v4.4 : un 2e téléphone se connecte au compte superviseur avec le code, le 1er reste connecté", async () => {
  const { api } = await setup();
  const old = (await api.post("/claim", { walker: "Éric" })).j.token;
  assert.equal((await api.post("/claim", { walker: "Éric", code: "0000" })).status, 403);   // mauvais code
  const n = await api.post("/claim", { walker: "Éric", code: "1234" });
  assert.equal(n.status, 200); assert.notEqual(n.j.token, old); assert.equal(n.j.phones, 2);
  assert.equal((await api.post("/dash", { token: n.j.token })).status, 200);
  assert.equal((await api.post("/dash", { token: old })).status, 200);                     // le 1er téléphone n'est plus déconnecté
  const again = await api.post("/claim", { walker: "Éric", token: old });                   // chaque téléphone se reconnaît avec son jeton
  assert.equal(again.status, 200); assert.equal(again.j.token, old);
  assert.equal((await api.post("/claim", { walker: "Éric" })).status, 403);                 // sans code ni jeton : toujours refusé
  const ph = await api.post("/sup-phones", { token: old });
  assert.equal(ph.j.phones, 2);
  assert.equal((await api.post("/sup-phones", { token: "faux-jeton-0123456789" })).status, 403);
  assert.equal((await api.post("/sup-phones", { code: "1234", only: 1 })).status, 400);    // le code seul ne dit pas quel téléphone garder
  const only = await api.post("/sup-phones", { token: n.j.token, only: 1 });                // déconnecter les autres
  assert.equal(only.j.phones, 1);
  assert.equal((await api.post("/dash", { token: old })).status, 403);
  assert.equal((await api.post("/dash", { token: n.j.token })).status, 200);
});

test("v4.4 : ancien format (un seul jeton) toujours accepté, et 6 téléphones au plus", async () => {
  const { api, env } = await setup();
  await env.WOUAF.put("admin", JSON.stringify({ token: "jeton-d-avant-0123456789", walker: "Éric", at: Date.now() }));
  assert.equal((await api.post("/dash", { token: "jeton-d-avant-0123456789" })).status, 200);
  const toks = [];
  for (let i = 0; i < 6; i++) toks.push((await api.post("/claim", { walker: "Éric", code: "1234" })).j.token);
  assert.equal((await api.post("/dash", { token: "jeton-d-avant-0123456789" })).status, 403);   // le plus ancien est sorti
  for (const t of toks) assert.equal((await api.post("/dash", { token: t })).status, 200);
  assert.equal((await api.post("/sup-phones", { token: toks[0] })).j.phones, 6);
});

test("Éric pris avant la libération du 14/11 : le premier téléphone qui tape Éric le reprend, sans code", async () => {
  const { api, env } = await setup();
  await env.WOUAF.put("admin", JSON.stringify({ token: "ancien-jeton-0123456789", walker: "Éric", at: Date.parse("2026-11-14T17:00:00Z") }));
  const r = await api.post("/claim", { walker: "Éric" });
  assert.equal(r.status, 200); assert.ok(r.j.created);
  assert.equal((await api.post("/claim", { walker: "Eric" })).status, 403);   // ensuite, verrouillé comme avant
  assert.equal((await api.post("/dash", { token: "ancien-jeton-0123456789" })).status, 403);
});

test("statistiques d'utilisation : gardées 14 jours, visibles dans le tableau de bord, jamais pour Éric", async () => {
  const { api } = await setup();
  const tok = (await api.post("/claim", { walker: "Éric" })).j.token;
  assert.equal((await api.post("/usage", { walker: "Léa", days: { "2026-11-14": { o: 3, s: 600, p: { "🪙 Tirelire": 2 } }, "pas-une-date": {} } })).status, 200);
  assert.ok((await api.post("/usage", { walker: "Éric", days: { "2026-11-14": { o: 1, s: 10, p: {} } } })).j.skipped);
  const u = (await api.post("/dash", { token: tok })).j.usage;
  assert.equal(u.length, 1); assert.equal(u[0].walker, "Léa"); assert.deepEqual(Object.keys(u[0].days), ["2026-11-14"]); assert.equal(u[0].days["2026-11-14"].p["🪙 Tirelire"], 2);
});

test("🎒 heures de cours (v2.6) : pas de rappel pendant un cours, il part à la fin du cours ; vacances = comme d'habitude", async () => {
  const { api, env, worker } = await setup();
  await api.get("/key");
  const paris = t => { const p = Object.fromEntries(new Intl.DateTimeFormat("en-GB", { timeZone:"Europe/Paris", hour:"2-digit", minute:"2-digit", weekday:"short", hour12:false }).formatToParts(new Date(t)).map(x => [x.type, x.value]));
    return { dow: ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].indexOf(p.weekday), hm: `${p.hour === "24" ? "00" : p.hour}:${p.minute}` }; };
  const T = Date.UTC(2026, 10, 17, 9, 0);   // mardi 17/11, 10 h à Paris
  const { dow, hm } = paris(T);
  const sub = { endpoint:"https://fcm.googleapis.com/fcm/send/abc", keys:{ p256dh:"x", auth:"y" } };
  const sched = Array.from({ length:7 }, () => ["", ""]); sched[dow] = [hm, ""];
  const cours = Array.from({ length:7 }, () => ["", ""]); cours[dow] = ["08:00", "10:30"];
  const id = "a".repeat(22);
  const reg = await api.post("/register", { id, sub, sched, cours, vac:false, walker:"Léa", state:{} });
  assert.equal(reg.status, 200);
  const u = JSON.parse(await env.WOUAF.get("u:" + id));
  assert.deepEqual(u.cours[dow], ["08:00", "10:30"]); assert.equal(u.vac, false);
  const realFetch = globalThis.fetch; globalThis.fetch = async () => new Response("", { status: 201 });
  try{
    await worker.scheduled({ scheduledTime: T }, env, { waitUntil: p => p }); await new Promise(r => setTimeout(r, 30));
    assert.equal(await env.WOUAF.get("s:" + id), null, "rien pendant le cours");
    await worker.scheduled({ scheduledTime: T + 31 * 60000 }, env, { waitUntil: p => p }); await new Promise(r => setTimeout(r, 30));
    assert.ok(await env.WOUAF.get("s:" + id), "le rappel part à la fin du cours (10 h 30)");
    await env.WOUAF.delete("s:" + id);
    await api.post("/register", { id, sub, sched, cours, vac:true, walker:"Léa", state:{} });
    await worker.scheduled({ scheduledTime: T }, env, { waitUntil: p => p }); await new Promise(r => setTimeout(r, 30));
    assert.ok(await env.WOUAF.get("s:" + id), "vacances : le rappel part à l'heure");
  } finally { globalThis.fetch = realFetch; }
});

test("💶 paie de la semaine (v2.6) : le téléphone l'annonce, le superviseur la marque versée, /pause le dit au téléphone", async () => {
  const { api } = await setup();
  assert.equal((await api.post("/week-pay", { walker:"Léa", wk:"2026-11-16", eur: 3.4 })).status, 200);
  assert.equal((await api.post("/week-pay", { walker:"Léa", wk:"pas une date", eur: 1 })).j.ok, false);
  const d = await api.post("/dash", { code:"1234" });
  assert.deepEqual(d.j.pays.map(x => [x.walker, x.w["2026-11-16"].eur]), [["Léa", 3.4]]);
  assert.equal((await api.post("/pay-mark", { code:"0000", walker:"Léa", wk:"2026-11-16" })).status, 403);
  assert.equal((await api.post("/pay-mark", { code:"1234", walker:"Léa", wk:"2026-11-16" })).status, 200);
  const p = await api.get("/pause");
  assert.ok(p.j.paid["léa"]["2026-11-16"] > 0);
  await api.post("/reset", { code:"1234" });
  assert.deepEqual((await api.get("/pause")).j.paid, {});
});

test("trésor placé à la main (v43) : superviseur seulement, renvoyé par /pause, effacé par « automatique » et par la remise à zéro", async () => {
  const { api } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  assert.equal((await api.post("/hunt-move", { wk: "2026-11-16", lat: 48.85, lon: 2.35 })).status, 403);          // pas superviseur
  assert.equal((await api.post("/hunt-move", { token: j.token, wk: "lundi", lat: 48.85, lon: 2.35 })).status, 400);
  assert.equal((await api.post("/hunt-move", { token: j.token, wk: "2026-11-16", lat: 91, lon: 2.35 })).status, 400);
  const m = await api.post("/hunt-move", { token: j.token, wk: "2026-11-16", lat: 48.8512345678, lon: 2.35 });
  assert.equal(m.status, 200); assert.equal(m.j.hpos.lat, 48.851235);
  assert.equal((await api.get("/pause")).j.hpos.wk, "2026-11-16");
  assert.equal((await api.post("/hunt-move", { code: "1234", clear: 1 })).j.hpos, null);
  assert.equal((await api.get("/pause")).j.hpos, null);
  await api.post("/hunt-move", { token: j.token, wk: "2026-11-16", lat: 48.85, lon: 2.35 });
  await api.post("/reset", { token: j.token });
  assert.equal((await api.get("/pause")).j.hpos, null);
});

test("v44 : maison de la famille arrondie (~200 m), trésor automatique publié par Éric sans écraser une position à la main", async () => {
  const { api } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  assert.equal((await api.post("/home-set", { lat: 48.85, lon: 2.35 })).status, 403);
  const h = await api.post("/home-set", { token: j.token, lat: 48.856613, lon: 2.352222 });
  assert.equal(h.status, 200);
  assert.ok(Math.abs(h.j.home.lat - 48.856) < 1e-9 && Math.abs(h.j.home.lon - 2.352) < 1e-9, JSON.stringify(h.j.home));   // jamais l'adresse exacte
  assert.equal((await api.get("/pause")).j.home.lat, 48.856);
  // trésor automatique : le 1er publié reste, un 2e automatique ne le remplace pas
  const a1 = await api.post("/hunt-move", { token: j.token, wk: "2026-12-7", lat: 48.86, lon: 2.36, auto: 1 });
  assert.equal(a1.status, 200); assert.equal(a1.j.hpos.auto, 1); assert.equal(a1.j.hpos.wk, "2026-12-7");      // date sans zéro acceptée
  assert.equal((await api.post("/hunt-move", { token: j.token, wk: "2026-12-7", lat: 1, lon: 1, auto: 1 })).j.hpos.lat, 48.86);
  // à la main : remplace l'automatique ; puis un automatique ne l'écrase plus
  await api.post("/hunt-move", { token: j.token, wk: "2026-12-7", lat: 48.87, lon: 2.37 });
  assert.equal((await api.post("/hunt-move", { token: j.token, wk: "2026-12-7", lat: 1, lon: 1, auto: 1 })).j.hpos.lat, 48.87);
  // changer la maison efface un trésor automatique (calculé autour de l'ancienne), pas un trésor placé à la main
  await api.post("/home-set", { token: j.token, lat: 48.9, lon: 2.4 });
  assert.equal((await api.get("/pause")).j.hpos.lat, 48.87);
  await api.post("/hunt-move", { token: j.token, clear: 1 });
  await api.post("/hunt-move", { token: j.token, wk: "2026-12-7", lat: 48.86, lon: 2.36, auto: 1 });
  await api.post("/home-set", { token: j.token, lat: 48.91, lon: 2.41 });
  assert.equal((await api.get("/pause")).j.hpos, null);
});

test("v44 : nuages argentés envoyés par les ados, lus seulement par Éric ; jamais pour Éric ; « off » les retire ; remise à zéro les efface", async () => {
  const { api } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  assert.equal((await api.post("/cloud", { walker: "Léa", day: "2026-11-17", lat: 48.861234567, lon: 2.35 })).status, 200);
  await api.post("/cloud", { walker: "Tom", day: "2026-11-17", lat: 48.84, lon: 2.34 });
  assert.equal((await api.post("/cloud", { walker: "Éric", day: "2026-11-17", lat: 48.84, lon: 2.34 })).j.skipped, true);
  assert.equal((await api.post("/cloud", { walker: "Léa", day: "hier", lat: 48.84, lon: 2.34 })).status, 400);
  assert.equal((await api.post("/clouds", {})).status, 403);                                                    // un ado ne lit rien
  assert.ok(!JSON.stringify((await api.get("/pause")).j).includes("Tom"));                                     // rien dans la route publique
  let c = (await api.post("/clouds", { token: j.token })).j.clouds;
  assert.equal(c.length, 2); assert.equal(c.find(x => x.w === "Léa").lat, 48.8612);
  await api.post("/cloud", { walker: "Tom", off: 1 });
  c = (await api.post("/clouds", { token: j.token })).j.clouds; assert.deepEqual(c.map(x => x.w), ["Léa"]);
  await api.post("/reset", { token: j.token });
  assert.equal((await api.post("/clouds", { token: j.token })).j.clouds.length, 0);
});

test("v47 : journal de bord de Roxy : chiffres par promeneur et de la famille (balades annulées exclues, ni trajet ni position)", async () => {
  const { api } = await setup();
  const now = Math.floor(Date.now() / 1000);
  await api.post("/walk", { walker: "Léa", walk: walk(now - 3600, { pp: 1 }), sum: {} });
  await api.post("/walk", { walker: "Léa", walk: walk(now - 10 * 86400, { min: 45, m: 3500 }), sum: {} });
  await api.post("/walk", { walker: "Tom", walk: walk(now - 7200, { cc: 1 }), sum: {} });
  const j = (await api.get("/journal")).j;
  const lea = j.walkers.find(x => x.w === "Léa"), tom = j.walkers.find(x => x.w === "Tom");
  assert.equal(lea.n, 2); assert.equal(lea.n7, 1); assert.equal(lea.n30, 2); assert.equal(lea.min, 75); assert.equal(lea.pp, 1); assert.equal(lea.best, 45);
  assert.equal(tom.cc, 1);
  assert.equal(j.fam.n, 3); assert.equal(j.fam.min, 105);
  assert.ok(!JSON.stringify(j).includes("lat"));
});

test("bugs : un promeneur signale, seul le superviseur lit, « Réglé ✓ », rouvrir, supprimer", async () => {
  const { api } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  assert.equal((await api.post("/bug", { walker: "Léa", text: "  " })).status, 400);
  assert.equal((await api.post("/bug", { walker: "Léa", text: "Le bouton Photo ne répond pas", v: "3.5" })).status, 200);
  assert.equal((await api.post("/bug", { walker: "Tom", text: "x".repeat(900) })).status, 200);
  assert.equal((await api.post("/bugs", {})).status, 403);                               // les ados ne lisent pas la liste
  const l = (await api.post("/bugs", { token: j.token })).j.bugs;
  assert.equal(l.length, 2); assert.equal(l[0].walker, "Tom"); assert.equal(l[0].text.length, 500); assert.equal(l[1].done, false);
  assert.equal((await api.post("/bug-done", { token: j.token, id: l[1].id })).status, 200);
  assert.equal((await api.post("/bugs", { token: j.token })).j.bugs[1].done, true);
  await api.post("/bug-done", { token: j.token, id: l[1].id, done: false });
  assert.equal((await api.post("/bugs", { token: j.token })).j.bugs[1].done, false);
  await api.post("/bug-done", { token: j.token, id: l[0].id, del: true });
  assert.equal((await api.post("/bugs", { token: j.token })).j.bugs.length, 1);
  for (let i = 0; i < 12; i++) await api.post("/bug", { walker: "Zoé", text: "encore un" });
  assert.equal((await api.post("/bug", { walker: "Zoé", text: "trop" })).status, 429);   // 10 par jour au plus
});

test("bugs avec capture : image gardée à part, lue seulement par le superviseur, effacée avec le bug", async () => {
  const { api, env } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  const img = "data:image/jpeg;base64,/9j/4AAQSkZJRg==";
  await api.post("/bug", { walker: "Léa", text: "Voilà ce que je vois", img });
  await api.post("/bug", { walker: "Tom", text: "Image bizarre", img: "data:text/html;base64,PHNjcmlwdD4=" });
  const l = (await api.post("/bugs", { token: j.token })).j.bugs;
  const lea = l.find(x => x.walker === "Léa"), tom = l.find(x => x.walker === "Tom");
  assert.equal(lea.img, true); assert.equal(tom.img, false);                              // seul un JPEG est accepté
  assert.equal((await api.post("/bug-img", { id: lea.id })).status, 403);                  // les ados ne lisent pas
  assert.equal((await api.post("/bug-img", { token: j.token, id: lea.id })).j.img, img);
  await api.post("/bug-done", { token: j.token, id: lea.id, del: true });
  assert.equal((await api.post("/bug-img", { token: j.token, id: lea.id })).j.img, "");
});
