import React, { useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { useSessions } from "./hooks/useSessions";
import { sendTextMessage, sendAudioMessage } from "./utils/api";
import { Message } from "./types";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import "./App.css";

const App: React.FC = () => {
  const {
    sessions,
    activeSession,
    activeSessionId,
    setActiveSessionId,
    createSession,
    deleteSession,
    addMessage,
    updateMessage,
  } = useSessions();

  const [isLoading, setIsLoading] = useState(false);

  // =====================
  // SEND TEXT
  // =====================
  const handleSendText = async (text: string) => {
    if (!activeSession || isLoading) return;

    const userMsg: Message = {
      id: uuidv4(),
      role: "user",
      type: "text",
      content: text,
      timestamp: new Date(),
    };
    addMessage(activeSession.id, userMsg);

    // placeholder loading bubble
    const loadingMsgId = uuidv4();
    const loadingMsg: Message = {
      id: loadingMsgId,
      role: "bot",
      type: "text",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    };
    addMessage(activeSession.id, loadingMsg);
    setIsLoading(true);

    try {
      const res = await sendTextMessage(activeSession.id, text);
      updateMessage(activeSession.id, loadingMsgId, {
        content: res.response,
        language: res.language,
        isLoading: false,
      });
    } catch (err) {
      updateMessage(activeSession.id, loadingMsgId, {
        content: "❌ Something went wrong. Please try again.",
        isLoading: false,
      });
    } finally {
      setIsLoading(false);
    }
  };

  // =====================
  // SEND AUDIO
  // =====================
  const handleSendAudio = async (blob: Blob, filename: string) => {
    if (!activeSession || isLoading) return;

    const userMsg: Message = {
      id: uuidv4(),
      role: "user",
      type: "audio",
      content: "🎙 Voice message sent",
      timestamp: new Date(),
    };
    addMessage(activeSession.id, userMsg);

    const loadingMsgId = uuidv4();
    const loadingMsg: Message = {
      id: loadingMsgId,
      role: "bot",
      type: "text",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    };
    addMessage(activeSession.id, loadingMsg);
    setIsLoading(true);

    try {
      const res = await sendAudioMessage(activeSession.id, blob, filename);

      // update user message with transcribed text
      updateMessage(activeSession.id, userMsg.id, {
        transcribed_text: res.transcribed_text,
      });

      // update bot loading bubble with actual response
      updateMessage(activeSession.id, loadingMsgId, {
        content: res.response,
        language: res.language,
        isLoading: false,
      });
    } catch (err) {
      updateMessage(activeSession.id, loadingMsgId, {
        content: "❌ Could not process audio. Please try again.",
        isLoading: false,
      });
    } finally {
      setIsLoading(false);
    }
  };

  // =====================
  // NEW CHAT — auto-create if none
  // =====================
  const handleNewChat = () => {
    createSession();
  };

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewChat={handleNewChat}
        onDeleteSession={deleteSession}
      />
      <main className="main">
        <ChatWindow
          session={activeSession}
          onSendText={handleSendText}
          onSendAudio={handleSendAudio}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
};

export default App;
