import test from "node:test";
import assert from "node:assert/strict";
import { loadWorker, makeEnv, client } from "./load-worker.mjs";

const setup = async () => { const worker = await loadWorker(), env = makeEnv(); return { worker, env, api: client(worker, env) }; };
const now = () => Math.round(Date.now() / 1000);
const walk = (e, min = 30) => ({ s: e - min * 60, e, min, m: 2500, cs: 40 });
// deux promeneurs connus du serveur (une balade chacun avant le duel), tirelire 200
const players = async api => { for (const w of ["Léa", "Tom"]) await api.post("/walk", { walker: w, walk: walk(now() - 10 * 86400, 10), sum: { cs: 200 } }); };
// déplace le duel dans le passé (fini hier) pour tester la fin sans attendre
const age = async (env, start, end) => { const l = await env.WOUAF.get("duels", "json"); l[0].start = start; l[0].end = end; await env.WOUAF.put("duels", JSON.stringify(l)); };
const day = d => { const x = new Date(Date.now() - 4 * 3600000 - d * 86400000); return x.toLocaleDateString("sv-SE", { timeZone: "Europe/Paris" }); };

test("duel complet « Balades » : défi, acceptation, score, fin, mises transférées", async () => {
  const { api, env } = await setup(); await players(api);
  const p = await api.post("/duels", { walker: "Léa" });
  assert.deepEqual(p.j.players.map(x => x.walker), ["Tom"]);
  const n = await api.post("/duel-new", { walker: "Léa", to: "Tom", days: 3, type: "walks", stake: 50, have: 200 });
  assert.equal(n.status, 200); const id = n.j.duel.id;
  assert.equal((await api.post("/duel-new", { walker: "Tom", to: "Léa", days: 3, type: "walks", stake: 25, have: 200 })).status, 409);   // 1 seul duel à la fois
  const a = await api.post("/duel-answer", { walker: "Tom", id, ok: true, have: 200 });
  assert.equal(a.j.duel.status, "active"); assert.equal(a.j.duel.start, day(-1));   // commence demain
  await age(env, day(3), day(1));
  const t = Math.round(Date.now() / 1000) - 2 * 86400;
  await api.post("/walk", { walker: "Léa", walk: walk(t, 30), sum: {} });
  await api.post("/walk", { walker: "Léa", walk: walk(t + 7200, 25), sum: {} });
  await api.post("/walk", { walker: "Tom", walk: walk(t + 100, 45), sum: {} });
  await api.post("/walk", { walker: "Tom", walk: walk(t + 300, 15), sum: {} });   // < 20 min : ne compte pas
  const r = (await api.post("/duels", { walker: "Tom" })).j.duels.find(d => d.id === id);
  assert.equal(r.status, "done"); assert.equal(r.res.winner, "Léa"); assert.equal(r.res.a, 2); assert.equal(r.res.b, 1);
  const aL = (await api.get("/adjust?w=Léa")).j.list, aT = (await api.get("/adjust?w=Tom")).j.list;
  assert.equal(aL.find(x => x.duel).cs, 50); assert.equal(aT.find(x => x.duel).cs, -50);
});

test("égalité : mêmes balades et mêmes minutes = personne ne perd sa mise ; à minutes différentes, le total départage", async () => {
  const { api, env } = await setup(); await players(api);
  const id = (await api.post("/duel-new", { walker: "Léa", to: "Tom", days: 3, type: "walks", stake: 25, have: 200 })).j.duel.id;
  await api.post("/duel-answer", { walker: "Tom", id, ok: true, have: 200 });
  await age(env, day(3), day(1));
  const t = now() - 2 * 86400;
  await api.post("/walk", { walker: "Léa", walk: walk(t, 30), sum: {} }); await api.post("/walk", { walker: "Tom", walk: walk(t + 60, 30), sum: {} });
  const r = (await api.post("/duels", { walker: "Léa" })).j.duels[0];
  assert.equal(r.status, "done"); assert.equal(r.res.winner, null);
  assert.equal((await api.get("/adjust?w=Léa")).j.list.length, 0);
});

test("abandon = défaite ; annulation seulement à deux ; expiration au bout de 24 h ; mise trop grosse refusée ; Éric exclu", async () => {
  const { api, env } = await setup(); await players(api);
  assert.equal((await api.post("/duel-new", { walker: "Léa", to: "Tom", days: 7, type: "walks", stake: 100, have: 50 })).status, 400);   // plus que sa tirelire
  assert.equal((await api.post("/duel-new", { walker: "Léa", to: "Tom", days: 1, type: "walks", stake: 25, have: 50 })).status, 400);    // 1 jour : n'existe plus
  let id = (await api.post("/duel-new", { walker: "Léa", to: "Tom", days: 7, type: "walks", stake: 25, have: 200 })).j.duel.id;
  await api.post("/duel-answer", { walker: "Tom", id, ok: true, have: 200 });
  let c = await api.post("/duel-cancel", { walker: "Léa", id }); assert.equal(c.j.duel.status, "active");   // un seul veut annuler
  c = await api.post("/duel-cancel", { walker: "Tom", id }); assert.equal(c.j.duel.status, "cancelled");
  id = (await api.post("/duel-new", { walker: "Tom", to: "Léa", days: 3, type: "walks", stake: 25, have: 200 })).j.duel.id;
  await api.post("/duel-answer", { walker: "Léa", id, ok: true, have: 200 });
  const q = await api.post("/duel-quit", { walker: "Tom", id });
  assert.equal(q.j.duel.res.winner, "Léa"); assert.equal(q.j.duel.res.why, "quit");
  // expiration
  id = (await api.post("/duel-new", { walker: "Tom", to: "Léa", days: 3, type: "walks", stake: 25, have: 200 })).j.duel.id;
  const l = await env.WOUAF.get("duels", "json"); l.find(d => d.id === id).created -= 25 * 3600000; await env.WOUAF.put("duels", JSON.stringify(l));
  assert.equal((await api.post("/duels", { walker: "Tom" })).j.duels.find(d => d.id === id).status, "expired");
  // Éric (superviseur) : pas de duel, et n'apparaît pas dans les adversaires
  const tok = (await api.post("/claim", { walker: "Éric" })).j.token;
  await api.post("/walk", { walker: "Éric", walk: walk(now() - 86400), sum: { test: 1 } });
  assert.equal((await api.post("/duels", { walker: "Éric" })).status, 403);
  assert.ok(!(await api.post("/duels", { walker: "Léa" })).j.players.some(p => p.walker === "Éric"));
  // Éric annule un duel en cours depuis son tableau de bord
  id = (await api.post("/duel-new", { walker: "Tom", to: "Léa", days: 3, type: "walks", stake: 25, have: 200 })).j.duel.id;
  await api.post("/duel-answer", { walker: "Léa", id, ok: true, have: 200 });
  assert.equal((await api.post("/dash", { token: tok })).j.duels.length, 1);
  assert.equal((await api.post("/duel-admin", { token: tok, id })).status, 200);
  assert.equal((await api.post("/duel-admin", { token: "x".repeat(30), id })).status, 403);
  assert.equal((await api.post("/duels", { walker: "Tom" })).j.duels.find(d => d.id === id).status, "cancelled");
});

test("guerre des rues : les cases ne sont gardées que pendant le duel, voler une rue, gagnant, cases effacées à la fin", async () => {
  const { api, env } = await setup(); await players(api);
  // hors duel : les cases sont ignorées
  await api.post("/walk", { walker: "Léa", walk: walk(now() - 3600), sum: {}, cells: ["1:1"] });
  const id = (await api.post("/duel-new", { walker: "Léa", to: "Tom", days: 3, type: "streets", stake: 50, have: 200 })).j.duel.id;
  await api.post("/duel-answer", { walker: "Tom", id, ok: true, have: 200 });
  await age(env, day(2), day(-1));   // en cours (commencé avant-hier, finit demain)
  const t = now() - 1800;
  await api.post("/walk", { walker: "Léa", walk: walk(t), sum: {}, cells: ["1:1", "1:2", "1:3"] });
  const s = await api.post("/walk", { walker: "Tom", walk: walk(t + 60), sum: {}, cells: ["1:2", "1:3", "9:9"] });
  assert.equal(s.j.stolen, 2);
  const m = await api.post("/duel-map", { walker: "Léa", id });
  assert.equal(m.j.cells["1:2"], "Tom"); assert.equal(m.j.score.a, 1); assert.equal(m.j.score.b, 3);
  await age(env, day(3), day(1));
  const r = (await api.post("/duels", { walker: "Léa" })).j.duels.find(d => d.id === id);
  assert.equal(r.res.winner, "Tom");
  assert.ok(!(await env.WOUAF.get("duels", "json"))[0].cells);   // plus aucune case sur le serveur
  assert.equal((await api.post("/duel-map", { walker: "Léa", id })).status, 409);
});

test("record du mois : la plus longue balade valide, Éric exclu, recalculé si la balade est annulée", async () => {
  const { api } = await setup();
  const tok = (await api.post("/claim", { walker: "Éric" })).j.token;
  const t = now() - 3600;
  assert.ok((await api.post("/walk", { walker: "Tom", walk: walk(t, 72), sum: {} })).j.record);
  assert.ok(!(await api.post("/walk", { walker: "Léa", walk: walk(t + 10, 60), sum: {} })).j.record);
  assert.ok(!(await api.post("/walk", { walker: "Éric", walk: walk(t + 20, 120), sum: {} })).j.record);
  const r = await api.post("/walk", { walker: "Léa", walk: walk(t + 30, 78), sum: {} });
  assert.equal(r.j.record.min, 78); assert.equal(r.j.record.prev.walker, "Tom");
  assert.equal((await api.get("/pause")).j.record.walker, "Léa");
  await api.post("/void", { token: tok, walker: "Léa", e: t + 30, why: "test" });
  assert.equal((await api.get("/pause")).j.record.walker, "Tom");
});

test("contre-proposition : l'adversaire propose une autre mise, nouveau défi dans l'autre sens ; expiration à 6 h", async () => {
  const { api, env } = await setup(); await players(api);
  const id = (await api.post("/duel-new", { walker: "Léa", to: "Tom", days: 7, type: "streets", stake: 100, have: 200 })).j.duel.id;
  assert.equal((await api.post("/duel-counter", { walker: "Léa", id, stake: 25, have: 200 })).status, 409);   // seul l'adversaire peut
  assert.equal((await api.post("/duel-counter", { walker: "Tom", id, stake: 100, have: 200 })).status, 400);  // même mise : non
  const c = await api.post("/duel-counter", { walker: "Tom", id, stake: 25, have: 200 });
  assert.equal(c.status, 200); assert.equal(c.j.duel.from, "Tom"); assert.equal(c.j.duel.to, "Léa"); assert.equal(c.j.duel.stake, 25); assert.equal(c.j.duel.type, "streets");
  const l = (await api.post("/duels", { walker: "Léa" })).j.duels;
  assert.equal(l.find(d => d.id === id).status, "countered");
  assert.equal((await api.post("/duel-answer", { walker: "Léa", id: c.j.duel.id, ok: true, have: 200 })).j.duel.status, "active");
  // 6 h sans réponse = expiré
  const { api: api2, env: env2 } = await setup(); await players(api2);
  const id2 = (await api2.post("/duel-new", { walker: "Léa", to: "Tom", days: 3, type: "walks", stake: 25, have: 200 })).j.duel.id;
  const d2 = await env2.WOUAF.get("duels", "json"); d2[0].created -= 6.5 * 3600000; await env2.WOUAF.put("duels", JSON.stringify(d2));
  assert.equal((await api2.post("/duels", { walker: "Tom" })).j.duels.find(d => d.id === id2).status, "expired");
});

test("que des paris : une mise de 0 est refusée", async () => {
  const { api } = await setup(); await players(api);
  assert.equal((await api.post("/duel-new", { walker: "Léa", to: "Tom", days: 3, type: "walks", stake: 0, have: 200 })).status, 400);
});
