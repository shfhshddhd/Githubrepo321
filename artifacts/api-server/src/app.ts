import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import router from "./routes";
import miniAppProxy from "./routes/mini-app-proxy";
import { logger } from "./lib/logger";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Older bot messages may still contain the host root URL. Keep those cached
// buttons useful while the current Mini App URL uses /api/mini-app/.
app.get("/", (_req, res) => {
  res.redirect("/api/mini-app/");
});

// Keep the public Mini App URL canonical so its relative assets and API paths
// always resolve below /api/mini-app/. Express's default route matching is
// not strict, so check the path explicitly to avoid redirecting the slash
// form back to itself.
app.use((req, res, next) => {
  if (req.method === "GET" && req.path === "/api/mini-app") {
    res.redirect("/api/mini-app/");
    return;
  }
  next();
});

// Keep Mini App auth and account ownership in the existing Python process.
// This public proxy only makes that HTTP surface reachable through the
// artifact router; it never sees Telegram or Telethon credentials.
app.use("/api/mini-app", miniAppProxy);
app.use("/api", router);

export default app;
