import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";

const root = path.resolve("creator_app/web");
const files = new Map([
  ["/workspace", ["workspace.html", "text/html; charset=utf-8"]],
  ["/static/workspace.css", ["workspace.css", "text/css; charset=utf-8"]],
  ["/static/workspace.js", ["workspace.js", "text/javascript; charset=utf-8"]],
]);

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || "/", "http://127.0.0.1");
  if (files.has(url.pathname) && req.method === "GET") {
    const [name, type] = files.get(url.pathname);
    try {
      const body = await readFile(path.join(root, name));
      res.writeHead(200, { "Content-Type": type, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
      res.end(body);
    } catch {
      res.writeHead(404); res.end("Not found");
    }
    return;
  }
  if (/^\/api\/[a-zA-Z0-9/_-]*$/.test(url.pathname) && ["GET", "POST"].includes(req.method || "")) {
    try {
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      const upstreamResponse = await new Promise((resolve, reject) => {
        const proxyRequest = http.request({
          hostname: "127.0.0.1",
          port: 8775,
          method: req.method,
          path: url.pathname + url.search,
          headers: {
            ...(req.headers.authorization ? { Authorization: req.headers.authorization } : {}),
            ...(req.headers["content-type"] ? { "Content-Type": req.headers["content-type"] } : {}),
          },
        }, (proxyResponse) => {
          const responseChunks = [];
          proxyResponse.on("data", (chunk) => responseChunks.push(chunk));
          proxyResponse.on("end", () => resolve({
            status: proxyResponse.statusCode || 502,
            contentType: proxyResponse.headers["content-type"] || "application/json",
            body: Buffer.concat(responseChunks),
          }));
        });
        proxyRequest.on("error", reject);
        proxyRequest.end(chunks.length ? Buffer.concat(chunks) : undefined);
      });
      res.writeHead(upstreamResponse.status, {
        "Content-Type": upstreamResponse.contentType,
        "Cache-Control": "no-store",
      });
      res.end(upstreamResponse.body);
    } catch {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ detail: { error: "UPSTREAM_UNAVAILABLE", message: "CK-NEXUS API is unavailable." } }));
    }
    return;
  }
  res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
  res.end("Not found");
});

server.listen(8780, "127.0.0.1", () => {
  process.stdout.write("NEXUS workspace preview: http://127.0.0.1:8780/workspace (API proxy -> 127.0.0.1:8775)\n");
});
