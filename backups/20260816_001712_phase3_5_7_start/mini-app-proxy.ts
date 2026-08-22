import { Router, type IRouter, type Request, type Response } from "express";

const router: IRouter = Router();
const targetPort = Number(process.env["MINI_APP_PROXY_PORT"] ?? "8008");
const publicPrefix = "/api/mini-app";
const privatePrefix = "/mini-app";

function targetUrl(req: Request): string {
  const suffix = req.originalUrl.slice(publicPrefix.length) || "/";
  return `http://127.0.0.1:${targetPort}${privatePrefix}${suffix}`;
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
    res.status(502).json({
      ok: false,
      code: "mini_app_unavailable",
      message: "The Mini App backend is temporarily unavailable.",
    });
  }
});

export default router;