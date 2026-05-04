import React, { useState, useRef } from "react";
import { useAudioRecorder } from "../hooks/useAudioRecorder";

interface InputBarProps {
  onSendText: (text: string) => void;
  onSendAudio: (blob: Blob, filename: string) => void;
  isLoading: boolean;
}

const InputBar: React.FC<InputBarProps> = ({ onSendText, onSendAudio, isLoading }) => {
  const [text, setText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { isRecording, startRecording, stopRecording, error } = useAudioRecorder(
    (blob) => onSendAudio(blob, "recording.ogg")
  );

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSendText(trimmed);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    onSendAudio(file, file.name);
    e.target.value = ""; // reset so same file can be re-uploaded
  };

  const handleMicClick = () => {
    if (isRecording) stopRecording();
    else startRecording();
  };

  return (
    <div className="input-bar-wrapper">
      {error && <div className="mic-error">{error}</div>}

      <div className={`input-bar ${isRecording ? "recording" : ""}`}>
        {/* Hidden file input for audio upload */}
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          style={{ display: "none" }}
          onChange={handleFileUpload}
        />

        {/* Upload audio file button */}
        <button
          className="icon-btn upload-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading || isRecording}
          title="Upload audio file"
        >
          📎
        </button>

        {/* Text input */}
        <textarea
          className="text-input"
          placeholder={isRecording ? "Recording... click stop when done" : "Ask about the airport..."}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || isRecording}
          rows={1}
        />

        {/* Mic button */}
        <button
          className={`icon-btn mic-btn ${isRecording ? "mic-active" : ""}`}
          onClick={handleMicClick}
          disabled={isLoading}
          title={isRecording ? "Stop recording" : "Record voice message"}
        >
          {isRecording ? "⏹" : "🎙"}
        </button>

        {/* Send button */}
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={isLoading || !text.trim() || isRecording}
          title="Send message"
        >
          {isLoading ? (
            <span className="send-spinner" />
          ) : (
            "Send"
          )}
        </button>
      </div>

      <div className="input-hint">
        Press Enter to send · Shift+Enter for new line · 🎙 to record · 📎 to upload audio
      </div>
    </div>
  );
};

export default InputBar;
