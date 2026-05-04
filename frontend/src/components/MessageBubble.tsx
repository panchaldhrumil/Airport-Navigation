import React from "react";
import { Message } from "../types";

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === "user";
  const isAudio = message.type === "audio";

  const formatTime = (date: Date) =>
    new Date(date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <div className={`bubble-wrapper ${isUser ? "user" : "bot"}`}>
      {!isUser && (
        <div className="avatar bot-avatar" title="Airport AI">✈</div>
      )}

      <div className={`bubble ${isUser ? "user-bubble" : "bot-bubble"} ${message.isLoading ? "loading-bubble" : ""}`}>
        {message.isLoading ? (
          <div className="typing-indicator">
            <span /><span /><span />
          </div>
        ) : (
          <>
            {isAudio && (
              <div className="audio-tag">
                <span className="mic-icon">🎙</span>
                <span>Voice message</span>
              </div>
            )}

            <div className="bubble-content">{message.content}</div>

            {isAudio && message.transcribed_text && (
              <div className="transcribed-text">
                <span className="transcribed-label">Heard: </span>
                {message.transcribed_text}
              </div>
            )}

            {message.language && message.language === "hi" && (
              <div className="lang-badge">🇮🇳 Hindi</div>
            )}

            <div className="bubble-time">{formatTime(message.timestamp)}</div>
          </>
        )}
      </div>

      {isUser && (
        <div className="avatar user-avatar" title="You">👤</div>
      )}
    </div>
  );
};

export default MessageBubble;
