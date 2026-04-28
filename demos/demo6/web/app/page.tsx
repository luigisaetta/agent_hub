"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Role = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: Role;
  content: string;
};

type ReferenceItem = {
  filename: string;
  pages: Array<number | string>;
};

type Demo6Envelope = {
  id?: string;
  type?: string;
  run_id?: string;
  node?: string;
  data?: {
    delta?: unknown;
    text?: string;
    output_text?: string;
    message?: string;
    final_state?: {
      reranked_chunks?: Array<{ filename?: string; pages?: Array<number | string> }>;
    };
  };
};

const DEFAULT_CHAT_URL = "http://127.0.0.1:8080/chat";

function normalizeReferences(raw: unknown): ReferenceItem[] {
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .filter((item): item is { filename?: unknown; pages?: unknown } => {
      return Boolean(item) && typeof item === "object";
    })
    .map((item) => {
      const filename = typeof item.filename === "string" ? item.filename : "unknown_file";
      const pages = Array.isArray(item.pages)
        ? item.pages.map((page) => String(page))
        : [];
      return { filename, pages };
    });
}

function parseSseBlocks(chunk: string): { events: Array<{ type: string; payload: string }>; rest: string } {
  const normalized = chunk.replace(/\r\n/g, "\n");
  const blocks = normalized.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: Array<{ type: string; payload: string }> = [];

  for (const block of blocks) {
    if (!block.trim()) {
      continue;
    }

    let eventType = "message";
    const dataLines: string[] = [];

    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) {
        eventType = line.slice(6).trim() || "message";
      }
      if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    }

    events.push({ type: eventType, payload: dataLines.join("\n") });
  }

  return { events, rest };
}

export default function HomePage() {
  const defaultUrl = useMemo(() => {
    const envUrl = process.env.NEXT_PUBLIC_DEMO6_CHAT_URL?.trim();
    return envUrl || DEFAULT_CHAT_URL;
  }, []);

  const [chatUrl, setChatUrl] = useState(defaultUrl);
  const [modelId, setModelId] = useState("openai.gpt-5.4");
  const [rerankerModelId, setRerankerModelId] = useState("openai.gpt-5.4");
  const [vectorStoreId, setVectorStoreId] = useState("");
  const [topK, setTopK] = useState("10");
  const [topN, setTopN] = useState("8");
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [references, setReferences] = useState<ReferenceItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const chatScrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const target = chatScrollRef.current;
    if (!target) {
      return;
    }
    target.scrollTop = target.scrollHeight;
  }, [messages, isLoading]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isLoading) {
      return;
    }

    const trimmedPrompt = prompt.trim();
    const trimmedUrl = chatUrl.trim();
    if (!trimmedPrompt || !trimmedUrl) {
      return;
    }

    const parsedTopK = Number.parseInt(topK, 10);
    const parsedTopN = Number.parseInt(topN, 10);
    if (!Number.isInteger(parsedTopK) || parsedTopK < 1) {
      setError("top_k must be a positive integer.");
      return;
    }
    if (!Number.isInteger(parsedTopN) || parsedTopN < 1) {
      setError("top_n must be a positive integer.");
      return;
    }

    setError("");
    setReferences([]);
    setIsLoading(true);

    const userMessage: ChatMessage = {
      id: `u_${Date.now()}`,
      role: "user",
      content: trimmedPrompt
    };

    const assistantMessageId = `a_${Date.now()}`;
    const assistantPlaceholder: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: ""
    };

    const history = messages.map((message) => ({
      role: message.role,
      content: message.content
    }));

    setMessages((previous) => [...previous, userMessage, assistantPlaceholder]);
    setPrompt("");

    try {
      const response = await fetch(trimmedUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream"
        },
        body: JSON.stringify({
          user_request: trimmedPrompt,
          history,
          model_id: modelId.trim() || undefined,
          reranker_model_id: rerankerModelId.trim() || undefined,
          vector_store_id: vectorStoreId.trim() || undefined,
          top_k: parsedTopK,
          top_n: parsedTopN
        })
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status} ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("Streaming response body is not available.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let finalText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const parsed = parseSseBlocks(buffer);
        buffer = parsed.rest;

        for (const evt of parsed.events) {
          if (!evt.payload) {
            continue;
          }

          let envelope: Demo6Envelope;
          try {
            envelope = JSON.parse(evt.payload) as Demo6Envelope;
          } catch {
            continue;
          }

          if (evt.type === "response.output_text.delta") {
            const delta =
              typeof envelope.data?.delta === "string" ? envelope.data.delta : "";
            if (delta) {
              finalText += delta;
              setMessages((previous) =>
                previous.map((message) => {
                  if (message.id !== assistantMessageId) {
                    return message;
                  }
                  return { ...message, content: message.content + delta };
                })
              );
            }
            continue;
          }

          if (evt.type === "graph.state.delta" && envelope.node === "Reranker") {
            const deltaData =
              envelope.data?.delta && typeof envelope.data.delta === "object"
                ? (envelope.data.delta as {
                    reranked_chunks?: Array<{
                      filename?: string;
                      pages?: Array<number | string>;
                    }>;
                  })
                : undefined;
            const reranked = normalizeReferences(deltaData?.reranked_chunks);
            if (reranked.length > 0) {
              setReferences(reranked);
            }
            continue;
          }

          if (evt.type === "response.output_text.completed") {
            const completedText = String(envelope.data?.text ?? "").trim();
            if (completedText) {
              finalText = completedText;
              setMessages((previous) =>
                previous.map((message) => {
                  if (message.id !== assistantMessageId) {
                    return message;
                  }
                  return { ...message, content: completedText };
                })
              );
            }
            continue;
          }

          if (evt.type === "response.completed") {
            const outputText = String(envelope.data?.output_text ?? "").trim();
            const finalRefs = normalizeReferences(
              envelope.data?.final_state?.reranked_chunks
            );
            if (finalRefs.length > 0) {
              setReferences(finalRefs);
            }

            const finalContent = outputText || finalText || "No text answer was produced.";
            setMessages((previous) =>
              previous.map((message) => {
                if (message.id !== assistantMessageId) {
                  return message;
                }
                return { ...message, content: finalContent };
              })
            );
            continue;
          }

          if (evt.type === "response.error") {
            const errorMessage = String(envelope.data?.message ?? "Backend error.");
            throw new Error(errorMessage);
          }
        }
      }
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Unexpected error while calling the backend.";
      setError(message);
      setMessages((previous) =>
        previous.map((item) => {
          if (item.id !== assistantMessageId) {
            return item;
          }
          return {
            ...item,
            content: `Error: ${message}`
          };
        })
      );
    } finally {
      setIsLoading(false);
    }
  }

  function onNewConversation() {
    if (isLoading) {
      return;
    }
    setMessages([]);
    setReferences([]);
    setError("");
  }

  return (
    <main className="chat-layout">
      <aside className="sidebar reveal-up">
        <div>
          <p className="eyebrow">OCI Enterprise AI</p>
          <h1>Demo6 RAG Chat</h1>
          <p className="sidebar-text">
            Streaming interface for demo6: settings sidebar with chatbot-style
            user/assistant conversation.
          </p>
        </div>

        <div className="sidebar-section">
          <label htmlFor="chat-url">Backend /chat URL</label>
          <input
            id="chat-url"
            type="url"
            value={chatUrl}
            onChange={(e) => setChatUrl(e.target.value)}
            required
          />

          <label htmlFor="model-id">model_id</label>
          <input
            id="model-id"
            type="text"
            value={modelId}
            onChange={(e) => setModelId(e.target.value)}
          />

          <label htmlFor="reranker-model-id">reranker_model_id</label>
          <input
            id="reranker-model-id"
            type="text"
            value={rerankerModelId}
            onChange={(e) => setRerankerModelId(e.target.value)}
          />

          <label htmlFor="vector-store-id">vector_store_id</label>
          <input
            id="vector-store-id"
            type="text"
            value={vectorStoreId}
            onChange={(e) => setVectorStoreId(e.target.value)}
          />

          <div className="field-grid">
            <div>
              <label htmlFor="top-k">top_k</label>
              <input
                id="top-k"
                type="number"
                min={1}
                value={topK}
                onChange={(e) => setTopK(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="top-n">top_n</label>
              <input
                id="top-n"
                type="number"
                min={1}
                value={topN}
                onChange={(e) => setTopN(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="section-title">References</p>
          {references.length === 0 ? (
            <p className="empty-state">No references yet.</p>
          ) : (
            <ul className="doc-list">
              {references.map((ref, index) => (
                <li key={`${ref.filename}-${index}`}>
                  <span className="doc-index">{index + 1}</span>
                  <div>
                    <p className="doc-main">{ref.filename}</p>
                    <p className="doc-sub">Pages: {ref.pages.join(", ") || "N/A"}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="sidebar-actions">
          <button type="button" onClick={onNewConversation} disabled={isLoading}>
            New Conversation
          </button>
        </div>
      </aside>

      <section className="chat-pane reveal-up delay-1">
        <div className="messages-scroll" ref={chatScrollRef}>
          {messages.length === 0 ? (
            <div className="empty-chat">
              <p>Start the conversation by asking a question about demo6.</p>
            </div>
          ) : (
            messages.map((message) => (
              <article
                key={message.id}
                className={`bubble-row ${message.role === "user" ? "from-user" : "from-ai"}`}
              >
                <div className="bubble">
                  {message.role === "assistant" ? (
                    <div className="markdown-output">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content || (isLoading ? "..." : "")}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>
              </article>
            ))
          )}
        </div>

        <form className="composer" onSubmit={onSubmit}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Write your message..."
            rows={3}
            disabled={isLoading}
            required
          />
          <div className="composer-actions">
            {error ? <p className="error-box">{error}</p> : <span />}
            <button type="submit" disabled={isLoading || !prompt.trim() || !chatUrl.trim()}>
              {isLoading ? "Streaming..." : "Send"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
