import test from "node:test";
import assert from "node:assert/strict";
import { loadWorker, makeEnv, client } from "./load-worker.mjs";

const setup = async () => { const worker = await loadWorker(), env = makeEnv(); return { worker, env, api: client(worker, env) }; };
// balade du mois « mk » (AAAA-MM), jour d, à 7 h ou 14 h (heure de Paris ≈ UTC+1 en novembre)
const at = (mk, d, h) => Math.floor(Date.parse(`${mk}-${String(d).padStart(2, "0")}T${String(h - 1).padStart(2, "0")}:00:00Z`) / 1000);
const walk = (e, extra) => Object.assign({ s: e - 1800, e, min: 30, m: 2500, cs: 40 }, extra);

test("cadeau argenté : posé par Éric seulement, un seul gagnant, visible dans /pause, retirable", async () => {
  const { api, env } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  assert.equal((await api.post("/silver-set", { lat: 48.85, lon: 2.35 })).status, 403);                    // pas superviseur
  assert.equal((await api.post("/silver-set", { token: j.token, lat: 91, lon: 2.35 })).status, 400);
  const set = await api.post("/silver-set", { token: j.token, lat: 48.8512345, lon: 2.35 });
  assert.equal(set.status, 200); assert.ok(set.j.silver.id); assert.equal(set.j.silver.by, null);
  const id = set.j.silver.id;
  assert.equal((await api.get("/pause")).j.silver.id, id);
  assert.equal((await api.post("/silver-found", { id, walker: "Éric" })).j.test, true);                      // le testeur ne le prend jamais
  const a = await api.post("/silver-found", { id, walker: "Léa" });
  assert.equal(a.j.first, true);
  const b = await api.post("/silver-found", { id, walker: "Tom" });
  assert.equal(b.j.first, false); assert.equal(b.j.by, "Léa");
  assert.equal((await api.post("/silver-found", { id, walker: "Léa" })).j.first, true);                      // même promeneur : reconnu
  assert.equal((await api.get("/pause")).j.silver.by, "Léa");
  await env.WOUAF.delete("sv:" + id);                                                                     // même après expiration de sv:, le gagnant reste
  assert.equal((await api.get("/pause")).j.silver.by, "Léa");
  assert.equal((await api.post("/silver-found", { id, walker: "Tom" })).j.first, false);
  assert.equal((await api.post("/silver-found", { id: "nimporte", walker: "Tom" })).j.gone, true);         // id inconnu / remplacé
  const clear = await api.post("/silver-set", { token: j.token, clear: 1 });
  assert.equal(clear.j.silver, null); assert.equal((await api.get("/pause")).j.silver, null);
});

test("cadeau argenté : un nouveau cadeau a un nouvel identifiant, l'ancien gagnant ne bloque pas le suivant", async () => {
  const { api } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  const one = (await api.post("/silver-set", { token: j.token, lat: 48.85, lon: 2.35 })).j.silver.id;
  await api.post("/silver-found", { id: one, walker: "Léa" });
  await new Promise(r => setTimeout(r, 3));
  const two = (await api.post("/silver-set", { token: j.token, lat: 48.86, lon: 2.36 })).j.silver.id;
  assert.notEqual(one, two);
  assert.equal((await api.post("/silver-found", { id: two, walker: "Tom" })).j.first, true);
});

test("alerte : annuler une balade après le cadeau argenté prévient Éric, qui peut redonner 250", async () => {
  const { api, env } = await setup();
  const { j } = await api.post("/claim", { walker: "Éric" });
  assert.equal((await api.post("/alert", { walker: "Léa", kind: "silver", week: "abc" })).status, 200);
  assert.equal((await api.post("/alert", { walker: "Léa", kind: "autre", week: "abc" })).status, 400);
  const al = (await env.WOUAF.get("alerts", "json"))[0];
  assert.equal((await api.post("/alert-resolve", { token: j.token, id: al.id, give: true })).status, 200);
  const adj = await env.WOUAF.get("a:léa", "json");
  assert.equal(adj[0].cs, 250);
});

test("trophées du mois : le gagnant de chaque trophée, ex æquo partagés, Éric exclu, mois en cours jamais figé", async () => {
  const { api, env } = await setup();
  await api.post("/claim", { walker: "Éric" });
  const mk = "2026-09";
  const send = (w, e, x) => api.post("/walk", { walker: w, walk: walk(e, x), sum: {} });
  await send("Léa", at(mk, 3, 7), { cc: 3, pp: 2, nc: 10, rn: 1, m: 4000 });              // 7 h : Lève-tôt
  await send("Léa", at(mk, 4, 14), { cc: 2, pp: 1, nc: 5, m: 3000, min: 50 });
  await send("Tom", at(mk, 3, 14), { cc: 5, pp: 6, nc: 10, du: 1, m: 9000, min: 40 });    // Tom : caca 5 = Léa 5 → ex æquo ; pipis 6 > 3
  await send("Éric", at(mk, 5, 14), { cc: 99, pp: 99, nc: 99, m: 99000 });                  // testeur : ne compte pas
  await send("Tom", Math.floor(Date.now() / 1000) - 60, { cc: 50 });                       // mois en cours : pas de trophées
  const h = (await api.get("/honors")).j;
  assert.deepEqual(h.honors.map(x => x.mk), [mk]);
  const t = h.honors[0].t;
  assert.deepEqual(t.cc.w.sort(), ["Léa", "Tom"]); assert.equal(t.cc.v, 5);                    // ex æquo
  assert.deepEqual(t.pp.w, ["Tom"]); assert.equal(t.pp.v, 6);
  assert.deepEqual(t.nc.w, ["Léa"]); assert.equal(t.nc.v, 15);
  assert.deepEqual(t.km.w, ["Tom"]); assert.equal(t.km.v, 9);                                  // 9 km
  assert.deepEqual(t.best.w, ["Léa"]); assert.equal(t.best.v, 50);                             // la plus longue balade
  assert.deepEqual(t.rain.w, ["Léa"]); assert.deepEqual(t.early.w, ["Léa"]); assert.deepEqual(t.duo.w, ["Tom"]);
  assert.equal(h.honors[0].fam.walkers, 2); assert.equal(h.honors[0].fam.cc, 10);
  assert.ok(await env.WOUAF.get("hon:" + mk));                                                 // gardé pour le palmarès
  assert.equal((await api.get("/honors")).j.honors.length, 1);                                // idempotent
  await api.post("/void", { code: "1234", walker: "Tom", e: at(mk, 3, 14), why: "test" });    // balade annulée après coup : trophées du mois recalculés
  const t2 = (await api.get("/honors")).j.honors[0].t;
  assert.deepEqual(t2.cc.w, ["Léa"]); assert.deepEqual(t2.pp.w, ["Léa"]); assert.equal(t2.duo, undefined);
});

test("trophées : rien à montrer sans balade, et la remise à zéro efface le palmarès et le cadeau argenté", async () => {
  const { api, env } = await setup();
  assert.deepEqual((await api.get("/honors")).j.honors, []);
  const { j } = await api.post("/claim", { walker: "Éric" });
  await api.post("/walk", { walker: "Léa", walk: walk(at("2026-08", 3, 14), { cc: 1 }), sum: {} });
  await api.post("/silver-set", { token: j.token, lat: 48.85, lon: 2.35 });
  assert.equal((await api.get("/honors")).j.honors.length, 1);
  assert.equal((await api.post("/reset", { token: j.token })).status, 200);
  assert.equal(await env.WOUAF.get("hon:2026-08"), null); assert.equal(await env.WOUAF.get("spos"), null);
  assert.equal((await api.get("/pause")).j.silver, null);
});
