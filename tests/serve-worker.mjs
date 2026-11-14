// Lance le VRAI code du Worker avec une KV en mémoire sur http://127.0.0.1:8787 (pour les tests dans le navigateur).
import http from "node:http";
import { loadWorker, makeEnv } from "./load-worker.mjs";
const worker = await loadWorker(), env = makeEnv("1234");
http.createServer(async (req, res) => {
  const chunks = []; for await (const c of req) chunks.push(c);
  const body = chunks.length ? Buffer.concat(chunks) : undefined;
  if (req.url === "/__wipe"){ env.WOUAF.m.clear(); res.end("ok"); return; }   // repartir d'une KV vide avant chaque série de tests
  if (req.url === "/__kv"){ res.setHeader("content-type", "application/json"); res.end(JSON.stringify([...env.WOUAF.m.entries()])); return; }
  const r = await worker.fetch(new Request("http://127.0.0.1:8787" + req.url, { method: req.method, body: ["GET","HEAD","OPTIONS"].includes(req.method) ? undefined : body }), env, {});
  res.statusCode = r.status; r.headers.forEach((v, k) => res.setHeader(k, v)); res.end(Buffer.from(await r.arrayBuffer()));
}).listen(8787, "127.0.0.1", () => console.log("worker prêt"));
