import React from "react";
import { Session } from "../types";

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <span className="logo-icon">✈</span>
          <div>
            <div className="logo-title">AeroChat</div>
            <div className="logo-sub">Airport Assistant</div>
          </div>
        </div>
        <button className="new-chat-btn" onClick={onNewChat}>
          <span>+</span> New Chat
        </button>
      </div>

      <div className="session-list">
        {sessions.length === 0 && (
          <div className="empty-sessions">No chats yet. Start one!</div>
        )}
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`session-item ${activeSessionId === session.id ? "active" : ""}`}
            onClick={() => onSelectSession(session.id)}
          >
            <div className="session-icon">💬</div>
            <div className="session-info">
              <div className="session-name">{session.name}</div>
              <div className="session-preview">
                {session.messages.length > 0
                  ? session.messages[session.messages.length - 1].content.slice(0, 30) + "..."
                  : "No messages yet"}
              </div>
            </div>
            <button
              className="delete-btn"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteSession(session.id);
              }}
              title="Delete chat"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="footer-text">Powered by AI · Airport Guide</div>
      </div>
    </aside>
  );
};

export default Sidebar;
