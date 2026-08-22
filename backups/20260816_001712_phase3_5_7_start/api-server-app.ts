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

// Keep Mini App auth and account ownership in the existing Python process.
// This public proxy only makes that HTTP surface reachable through the
// artifact router; it never sees Telegram or Telethon credentials.
app.use("/api/mini-app", miniAppProxy);
app.use("/api", router);

export default app;
