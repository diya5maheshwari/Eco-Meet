import express from "express";
import mongoose from "mongoose";
import dotenv from "dotenv";
import cors from "cors";
import cookieParser from "cookie-parser";
import authRoutes from "./routes/authRoutes.js";
import userRoutes from "./routes/userRoutes.js";
import speechRoutes from "./routes/speechRoutes.js";

dotenv.config();

const app = express();

const allowedOrigins = process.env.CORS_ORIGIN
  ? process.env.CORS_ORIGIN.split(",").map((o) => o.trim().replace(/\/$/, ""))
  : null;

app.use(
  cors({
    origin: (origin, cb) => {
      if (!origin) return cb(null, true);
      const normalized = origin.replace(/\/$/, "");
      if (!allowedOrigins || allowedOrigins.includes(normalized)) {
        return cb(null, true);
      }
      return cb(new Error("Not allowed by CORS"));
    },
    credentials: true,
  })
);
app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use("/api/user", userRoutes);


mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("MongoDB connected"))
  .catch((err) => console.log(err));

app.use("/api/auth", authRoutes);
app.use("/api/speech", speechRoutes);

app.listen(5000, () => {
  console.log("Server running on port 5000");
});
