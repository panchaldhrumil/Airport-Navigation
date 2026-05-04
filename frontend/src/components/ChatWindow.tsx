import React, { useEffect, useRef } from "react";
import { Session } from "../types";
import MessageBubble from "./MessageBubble";
import InputBar from "./InputBar";

interface ChatWindowProps {
  session: Session | null;
  onSendText: (text: string) => void;
  onSendAudio: (blob: Blob, filename: string) => void;
  isLoading: boolean;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  session,
  onSendText,
  onSendAudio,
  isLoading,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // auto-scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages]);

  if (!session) {
    return (
      <div className="chat-empty">
        <div className="empty-icon">✈</div>
        <div className="empty-title">Welcome to AeroChat</div>
        <div className="empty-sub">
          Ask me anything about the airport — gates, lounges, food, transport, and more.
        </div>
        <div className="empty-hint">← Create a new chat to get started</div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="chat-header-name">{session.name}</div>
          <div className="chat-header-sub">
            {session.messages.length} message{session.messages.length !== 1 ? "s" : ""}
          </div>
        </div>
        <div className="chat-header-badge">🛫 Airport AI</div>
      </div>

      {/* Messages */}
      <div className="messages-area">
        {session.messages.length === 0 && (
          <div className="no-messages">
            <p>Say hello or ask about gates, food, transport, lounges...</p>
            <p>You can type or send a voice message 🎙</p>
          </div>
        )}
        {session.messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <InputBar
        onSendText={onSendText}
        onSendAudio={onSendAudio}
        isLoading={isLoading}
      />
    </div>
  );
};

export default ChatWindow;
