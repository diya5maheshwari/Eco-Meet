import SpeechText from "../models/SpeechText.js";

export const saveText = async (req, res) => {
  try {
    const { text } = req.body;
    if (!text || !text.trim()) {
      return res.status(400).json({ message: "Text is required" });
    }

    const saved = await SpeechText.create({
      user: req.user._id,
      text: text.trim(),
    });

    res.status(201).json({ message: "Text saved", item: saved });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

export const getTexts = async (req, res) => {
  try {
    const items = await SpeechText.find({ user: req.user._id })
      .sort({ createdAt: -1 })
      .limit(50);

    res.json({ items });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};
