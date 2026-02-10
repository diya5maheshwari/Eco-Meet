import axios from "axios";

export const transcribeAudio = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: "Audio file is required" });
    }
    if (!process.env.DEEPGRAM_API_KEY) {
      return res.status(500).json({ message: "Missing DEEPGRAM_API_KEY" });
    }

    const response = await axios.post(
      "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true",
      req.file.buffer,
      {
        headers: {
          Authorization: `Token ${process.env.DEEPGRAM_API_KEY}`,
          "Content-Type": req.file.mimetype || "audio/m4a",
        },
        maxBodyLength: Infinity,
      }
    );

    const text =
      response.data?.results?.channels?.[0]?.alternatives?.[0]?.transcript || "";

    res.json({ text });
  } catch (error) {
    res
      .status(500)
      .json({ message: error.response?.data || error.message });
  }
};

export const pingDeepgram = async (req, res) => {
  try {
    if (!process.env.DEEPGRAM_API_KEY) {
      return res.status(500).json({ message: "Missing DEEPGRAM_API_KEY" });
    }

    const response = await axios.get(
      "https://api.deepgram.com/v1/projects",
      {
        headers: {
          Authorization: `Token ${process.env.DEEPGRAM_API_KEY}`,
        },
      }
    );

    res.json({ ok: true, status: response.status });
  } catch (error) {
    res
      .status(500)
      .json({ ok: false, message: error.response?.data || error.message });
  }
};
