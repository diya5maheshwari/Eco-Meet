import express from "express";
import multer from "multer";
import protect from "../middleware/authMiddleware.js";
import { pingDeepgram, transcribeAudio } from "../controllers/speechController.js";

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage() });

router.post("/transcribe", protect, upload.single("file"), transcribeAudio);
router.get("/ping", protect, pingDeepgram);

export default router;
