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
