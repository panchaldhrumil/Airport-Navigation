import axios from "axios";
import { TextChatResponse, AudioChatResponse } from "./types";

const BASE_URL = "http://localhost:8000";

export const sendTextMessage = async (
  sessionId: string,
  query: string
): Promise<TextChatResponse> => {
  const res = await axios.post<TextChatResponse>(`${BASE_URL}/chat/text`, {
    session_id: sessionId,
    query,
  });
  return res.data;
};

export const sendAudioMessage = async (
  sessionId: string,
  audioBlob: Blob,
  filename: string = "recording.ogg"
): Promise<AudioChatResponse> => {
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("file", audioBlob, filename);

  const res = await axios.post<AudioChatResponse>(
    `${BASE_URL}/chat/audio`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return res.data;
};

export const checkHealth = async (): Promise<boolean> => {
  try {
    await axios.get(`${BASE_URL}/health`);
    return true;
  } catch {
    return false;
  }
};
