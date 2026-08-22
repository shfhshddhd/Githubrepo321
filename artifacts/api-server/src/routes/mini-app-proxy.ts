import { Router, type IRouter, type Request, type Response } from "express";
import { createConnection, type Socket } from "node:net";
import type { IncomingMessage, Server } from "node:http";
import { logger } from "../lib/logger";

const router: IRouter = Router();
const targetPort = Number(process.env["MINI_APP_PROXY_PORT"] ?? "8008");
const publicPrefix = "/api/mini-app";
const privatePrefix = "/mini-app";

const offlineDocument = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <meta name="color-scheme" content="dark" />
    <title>Live VC unavailable</title>
    <style>
      :root {
        color-scheme: dark;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #0b1018;
        color: #f0f5ff;
      }
      * { box-sizing: border-box; }
      body {
        min-height: 100vh;
        margin: 0;
        display: grid;
        place-items: center;
        padding: 24px;
        background: radial-gradient(circle at 20% 0%, #1b2f40 0, transparent 48%), #0b1018;
      }
      main {
        width: min(100%, 440px);
        border: 1px solid rgba(191, 213, 240, .16);
        border-radius: 22px;
        padding: 28px;
        background: rgba(19, 27, 39, .94);
        box-shadow: 0 24px 80px rgba(0, 0, 0, .28);
      }
      .mark {
        width: 42px;
        height: 42px;
        display: grid;
        place-items: center;
        border-radius: 14px;
        background: rgba(255, 155, 155, .14);
        color: #ffb0b0;
        font-size: 22px;
      }
      h1 { margin: 20px 0 10px; font-size: 28px; letter-spacing: -.04em; }
      p { margin: 0; color: #9aabc1; line-height: 1.55; }
      button {
        width: 100%;
        margin-top: 24px;
        border: 0;
        border-radius: 13px;
        padding: 14px 18px;
        background: #70d7c1;
        color: #071612;
        font: inherit;
        font-weight: 800;
        cursor: pointer;
      }
    </style>
  </head>
  <body>
    <main role="status">
      <div class="mark" aria-hidden="true">!</div>
      <h1>Live VC is temporarily offline</h1>
      <p>The Telegram service is not running right now. Start it and try opening this Mini App again.</p>
      <button type="button" onclick="location.reload()">Try again</button>
    </main>
  </body>
</html>`;

function targetUrl(req: Request): string {
  const suffix = req.originalUrl.slice(publicPrefix.length) || "/";
  return `http://127.0.0.1:${targetPort}${privatePrefix}${suffix}`;
}

function isMiniAppDocument(req: Request): boolean {
  const path = req.originalUrl.split("?", 1)[0].replace(/\/+$/, "");
  return path === publicPrefix;
}

router.use(async (req: Request, res: Response) => {
  try {
    const body =
      req.method === "GET" || req.method === "HEAD"
        ? undefined
        : JSON.stringify(req.body ?? {});
    const upstream = await fetch(targetUrl(req), {
      method: req.method,
      headers: {
        accept: req.get("accept") ?? "*/*",
        ...(req.get("authorization")
          ? { authorization: req.get("authorization") as string }
          : {}),
        ...(req.get("content-type")
          ? { "content-type": req.get("content-type") as string }
          : {}),
      },
      body,
    });

    res.status(upstream.status);
    const contentType = upstream.headers.get("content-type");
    if (contentType) {
      res.setHeader("content-type", contentType);
    }
    const cacheControl = upstream.headers.get("cache-control");
    if (cacheControl) {
      res.setHeader("cache-control", cacheControl);
    }
    res.send(Buffer.from(await upstream.arrayBuffer()));
  } catch (error) {
    req.log.error({ err: error }, "Mini App proxy request failed");
    if (isMiniAppDocument(req)) {
      res
        .status(503)
        .setHeader("cache-control", "no-store")
        .type("html")
        .send(offlineDocument);
      return;
    }
    res.status(502).json({
      ok: false,
      code: "mini_app_unavailable",
      message: "The Mini App backend is temporarily unavailable.",
    });
  }
});

function headerValue(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) return value.join(", ");
  return value;
}

function closeSocket(socket: { destroyed: boolean; destroy(): void }): void {
  if (!socket.destroyed) socket.destroy();
}

/**
 * The Mini App audio endpoint is a real WebSocket carrying binary PCM16 frames.
 * Express/fetch cannot proxy an HTTP upgrade, so keep this tunnel at the Node
 * HTTP server layer and leave the frames untouched.
 */
export function attachMiniAppWebSocketProxy(server: Server): void {
  server.on("upgrade", (request: IncomingMessage, clientSocket, head) => {
    const requestUrl = request.url ?? "/";
    if (!requestUrl.startsWith(publicPrefix)) return;

    const suffix = requestUrl.slice(publicPrefix.length) || "/";
    const upstreamPath = `${privatePrefix}${suffix}`;
    const upstreamSocket = createConnection({
      host: "127.0.0.1",
      port: targetPort,
    });

    const abort = () => {
      closeSocket(clientSocket);
      closeSocket(upstreamSocket);
    };

    clientSocket.on("error", abort);
    upstreamSocket.on("error", (error) => {
      logger.error({ err: error }, "Mini App WebSocket proxy failed");
      abort();
    });

    upstreamSocket.on("connect", () => {
      const forwardedHeaders = Object.entries(request.headers)
        .filter(([name]) => name.toLowerCase() !== "host")
        .map(([name, value]) => {
          const normalized = headerValue(value);
          return normalized === undefined ? "" : `${name}: ${normalized}\r\n`;
        })
        .join("");
      const upgradeRequest =
        `GET ${upstreamPath} HTTP/1.1\r\n` +
        `Host: 127.0.0.1:${targetPort}\r\n` +
        forwardedHeaders +
        "\r\n";

      upstreamSocket.write(upgradeRequest);
      if (head.length > 0) upstreamSocket.write(head);

      clientSocket.pipe(upstreamSocket);
      upstreamSocket.pipe(clientSocket);
    });
  });
}

export default router;