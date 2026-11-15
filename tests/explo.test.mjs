import test from "node:test";
import assert from "node:assert/strict";
import { loadWorker, makeEnv, client } from "./load-worker.mjs";

const setup = async () => { const worker = await loadWorker(), env = makeEnv(); return { worker, env, api: client(worker, env) }; };
const now = () => Math.round(Date.now() / 1000);
const walk = (e, nc, ob, min = 30) => ({ s: e - min * 60, e, min, m: 2500, cs: 40, nc, ob });

test("🧭 classement des explorateurs : places seulement, ex aequo, ≥ 20 min, semaine passée, Éric exclu", async () => {
  const { api, env } = await setup();
  await api.post("/walk", { walker: "Tom", walk: walk(now() - 600, 8, 6), sum: {} });        // 30
  await api.post("/walk", { walker: "Léa", walk: walk(now() - 900, 5, 4), sum: {} });        // 19
  await api.post("/walk", { walker: "Zoé", walk: walk(now() - 1200, 6, 1), sum: {} });       // 19 → ex aequo avec Léa
  await api.post("/walk", { walker: "Max", walk: walk(now() - 1500, 9, 9, 15), sum: {} });   // < 20 min : ne compte pas
  await env.WOUAF.put("admin", JSON.stringify({ token: "x" }));
  await api.post("/walk", { walker: "Éric", walk: walk(now() - 1800, 10, 20), sum: {} });   // superviseur : exclu
  await api.post("/walk", { walker: "Léa", walk: walk(now() - 8 * 86400, 2, 2), sum: {} });  // semaine dernière
  const r = await api.get("/pause"), ex = r.j.explo; if (process.env.DBG) console.log(JSON.stringify(ex));
  assert.deepEqual(ex.rank, [{ w: "Tom", r: 1 }, { w: "Léa", r: 2 }, { w: "Zoé", r: 2 }]);
  assert.ok(!JSON.stringify(ex).match(/"(sc|pts|score)"/), "aucun point renvoyé");
  assert.deepEqual(ex.prev.rank, [{ w: "Léa", r: 1 }]);
  assert.match(ex.wk, /^\d{4}-\d\d-\d\d$/); assert.equal(new Date(ex.wk + "T12:00:00Z").getUTCDay(), 1);   // un lundi
});

test("👃 flair : balade en cours (heure seulement), notification au quart d'heure dès 5 min, finie à la réception de la balade", async () => {
  const { api, env, worker } = await setup();
  const s = now() - 6 * 60;
  assert.equal((await api.post("/walk-live", { walker: "Léa", s, on: 1 })).status, 200);
  let live = JSON.parse(await env.WOUAF.get("live"));
  assert.deepEqual(Object.keys(live), ["léa"]); assert.equal(live["léa"].s, s); assert.ok(!("lat" in live["léa"]));
  await worker.scheduled({ scheduledTime: Date.now() }, env, { waitUntil: p => p });
  await new Promise(r => setTimeout(r, 50));
  live = JSON.parse(await env.WOUAF.get("live")); assert.ok(live["léa"].f > 0, "flair envoyé");
  const f1 = live["léa"].f;
  await worker.scheduled({ scheduledTime: Date.now() + 60000 }, env, { waitUntil: p => p }); await new Promise(r => setTimeout(r, 50));
  assert.equal(JSON.parse(await env.WOUAF.get("live"))["léa"].f, f1, "pas deux flairs de suite");
  await api.post("/walk", { walker: "Léa", walk: walk(now(), 4, 3), sum: {} });
  assert.deepEqual(JSON.parse(await env.WOUAF.get("live")), {});
  await api.post("/walk-live", { walker: "Tom", s: now() - 60, on: 1 });
  await api.post("/walk-live", { walker: "Tom", on: 0 });
  assert.deepEqual(JSON.parse(await env.WOUAF.get("live")), {});
});

test("🐾 compteur de la famille : km et rues neuves de toutes les balades", async () => {
  const { api } = await setup();
  await api.post("/walk", { walker: "Léa", walk: walk(now() - 900, 4, 3), sum: {} });
  await api.post("/walk", { walker: "Tom", walk: walk(now() - 300, 2, 1), sum: {} });
  const f = (await api.get("/pause")).j.fam;
  assert.equal(f.m, 5000); assert.equal(f.nc, 6); assert.equal(f.n, 2);
});
