import { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import { Session, Message } from "../types";

const STORAGE_KEY = "airport_chatbot_sessions";

export const useSessions = () => {
  const [sessions, setSessions] = useState<Session[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // restore Date objects
        return parsed.map((s: Session) => ({
          ...s,
          createdAt: new Date(s.createdAt),
          messages: s.messages.map((m: Message) => ({
            ...m,
            timestamp: new Date(m.timestamp),
          })),
        }));
      }
    } catch {}
    return [];
  });

  const [activeSessionId, setActiveSessionId] = useState<string | null>(
    () => sessions[0]?.id ?? null
  );

  // persist to localStorage on every change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  }, [sessions]);

  const createSession = useCallback(() => {
    const newSession: Session = {
      id: uuidv4(),
      name: `Chat ${sessions.length + 1}`,
      messages: [],
      createdAt: new Date(),
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    return newSession;
  }, [sessions.length]);

  const deleteSession = useCallback(
    (sessionId: string) => {
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setSessions((prev) => {
          const remaining = prev.filter((s) => s.id !== sessionId);
          setActiveSessionId(remaining[0]?.id ?? null);
          return remaining;
        });
      }
    },
    [activeSessionId]
  );

  const addMessage = useCallback((sessionId: string, message: Message) => {
    setSessions((prev) =>
      prev.map((s) =>
        s.id === sessionId ? { ...s, messages: [...s.messages, message] } : s
      )
    );
  }, []);

  const updateMessage = useCallback(
    (sessionId: string, messageId: string, updates: Partial<Message>) => {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                messages: s.messages.map((m) =>
                  m.id === messageId ? { ...m, ...updates } : m
                ),
              }
            : s
        )
      );
    },
    []
  );

  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? null;

  return {
    sessions,
    activeSession,
    activeSessionId,
    setActiveSessionId,
    createSession,
    deleteSession,
    addMessage,
    updateMessage,
  };
};
