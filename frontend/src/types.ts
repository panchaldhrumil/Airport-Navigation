export type MessageRole = "user" | "bot";
export type MessageType = "text" | "audio";

export interface Message {
  id: string;
  role: MessageRole;
  type: MessageType;
  content: string;
  transcribed_text?: string;
  language?: string;
  timestamp: Date;
  isLoading?: boolean;
}

export interface Session {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
}

export interface TextChatResponse {
  session_id: string;
  response: string;
  intent?: string;
  language?: string;
}

export interface AudioChatResponse {
  session_id: string;
  response: string;
  intent?: string;
  language?: string;
  transcribed_text?: string;
}
