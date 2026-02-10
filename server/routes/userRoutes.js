import express from "express";
import protect from "../middleware/authMiddleware.js";
import { getTexts, saveText } from "../controllers/userController.js";

const router = express.Router();

router.get("/profile", protect, (req, res) => {
  res.json({
    message: "Profile accessed",
    user: req.user,
  });
});

router.post("/save-text", protect, saveText);
router.get("/texts", protect, getTexts);

export default router;
