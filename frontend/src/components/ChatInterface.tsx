"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Square, Sparkles, User, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import TextareaAutosize from "react-textarea-autosize";
import { MessageContent } from "@/components/MessageContent";
import { SourcesPanel } from "@/components/SourcesPanel";
import { chatStream, type ChatResponse } from "@/lib/api";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    sources?: ChatResponse["sources"];
    strategy?: string;
    isStreaming?: boolean;
}

const EXAMPLE_QUERIES = [
    "受賞作品の共通点は何ですか？",
    "いいね数トップ5のプロジェクトは？",
    "Flutterを使った作品を教えて",
    "ヘルスケア分野のプロジェクトは？",
];

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isComposing, setIsComposing] = useState(false);  // IME 入力中フラグ
    const [abortController, setAbortController] = useState<AbortController | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // マウント時に sessionStorage から会話履歴を復元
    useEffect(() => {
        const saved = sessionStorage.getItem('chat_messages');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    setMessages(parsed);
                }
            } catch {
                // パースエラーは無視
            }
        }
    }, []);

    // 会話履歴を sessionStorage に保存（ストリーミング中のメッセージは除外）
    useEffect(() => {
        // 完了したメッセージのみ保存
        const completedMessages = messages.filter(m => !m.isStreaming);
        if (completedMessages.length > 0) {
            sessionStorage.setItem('chat_messages', JSON.stringify(completedMessages));
        }
    }, [messages]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const handleStop = useCallback(() => {
        abortController?.abort();
        setIsLoading(false);
        // ストリーミング中のメッセージを更新
        setMessages((prev) =>
            prev.map((m) =>
                m.isStreaming ? { ...m, isStreaming: false, content: m.content || "中断されました" } : m
            )
        );
    }, [abortController]);

    const handleSend = async (message?: string) => {
        const text = message || input.trim();
        if (!text || isLoading) return;

        const userMessageId = `user-${Date.now()}`;
        const assistantMessageId = `assistant-${Date.now()}`;

        setInput("");
        setMessages((prev) => [
            ...prev,
            { id: userMessageId, role: "user", content: text },
            { id: assistantMessageId, role: "assistant", content: "", isStreaming: true },
        ]);
        setIsLoading(true);

        const controller = new AbortController();
        setAbortController(controller);

        try {
            let currentContent = "";
            let sources: ChatResponse["sources"] = [];
            let strategy = "";

            await chatStream(text, {
                signal: controller.signal,
                onMetadata: (metadata) => {
                    sources = metadata.sources;
                    strategy = metadata.strategy;
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantMessageId ? { ...m, sources, strategy } : m
                        )
                    );
                },
                onToken: (token) => {
                    currentContent += token;
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantMessageId ? { ...m, content: currentContent } : m
                        )
                    );
                },
                onDone: () => {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantMessageId ? { ...m, isStreaming: false } : m
                        )
                    );
                },
                onError: (error) => {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantMessageId
                                ? { ...m, content: `Error: ${error}`, isStreaming: false }
                                : m
                        )
                    );
                },
            });
        } catch (error) {
            if ((error as Error).name !== "AbortError") {
                setMessages((prev) =>
                    prev.map((m) =>
                        m.id === assistantMessageId
                            ? { ...m, content: "Connection error. Please check if backend is running.", isStreaming: false }
                            : m
                    )
                );
            }
        } finally {
            setIsLoading(false);
            setAbortController(null);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        // IME 入力中（日本語等）は Enter を無視
        // keyCode 229 は IME 処理中を示す
        if (e.keyCode === 229) return;
        if (isComposing || e.nativeEvent.isComposing) return;

        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleCompositionStart = () => setIsComposing(true);
    const handleCompositionEnd = () => {
        // 少し遅延させてから isComposing を false にする
        // これにより、Enter キーが送信をトリガーするのを防ぐ
        setTimeout(() => setIsComposing(false), 100);
    };

    return (
        <div className="flex-1 flex flex-col overflow-hidden bg-neutral-50 dark:bg-neutral-950">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-2xl mx-auto px-6 py-8 md:py-12">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center min-h-[65vh]">
                            <div className="w-12 h-12 rounded-2xl bg-neutral-900 dark:bg-white flex items-center justify-center mb-8">
                                <MessageSquare className="w-6 h-6 text-white dark:text-neutral-900" />
                            </div>
                            <h1 className="text-2xl font-light tracking-tight text-neutral-900 dark:text-neutral-100 mb-3">
                                Hackathon Explorer
                            </h1>
                            <p className="text-neutral-500 dark:text-neutral-400 text-center max-w-sm mb-12 font-light">
                                Search and explore 400+ AI Agent Hackathon projects with natural language.
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-md">
                                {EXAMPLE_QUERIES.map((q) => (
                                    <button
                                        key={q}
                                        onClick={() => handleSend(q)}
                                        className="text-left px-4 py-3 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 hover:border-neutral-300 dark:hover:border-neutral-700 transition-colors text-sm text-neutral-700 dark:text-neutral-300"
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-8">
                            {messages.map((msg) => (
                                <div key={msg.id} className="group">
                                    {msg.role === "user" ? (
                                        <div className="flex items-start gap-4">
                                            <div className="w-8 h-8 rounded-full bg-neutral-900 dark:bg-white flex items-center justify-center flex-shrink-0">
                                                <User className="w-4 h-4 text-white dark:text-neutral-900" />
                                            </div>
                                            <div className="flex-1 pt-1">
                                                <p className="text-neutral-900 dark:text-neutral-100 leading-relaxed">
                                                    {msg.content}
                                                </p>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex items-start gap-4">
                                            <div className="w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center flex-shrink-0">
                                                <Sparkles className="w-4 h-4 text-neutral-600 dark:text-neutral-400" />
                                            </div>
                                            <div className="flex-1 pt-1 min-w-0">
                                                {msg.content ? (
                                                    <MessageContent content={msg.content} />
                                                ) : msg.isStreaming ? (
                                                    <div className="flex items-center gap-1.5 text-neutral-400">
                                                        <span className="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-pulse" />
                                                        <span className="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-pulse" style={{ animationDelay: "150ms" }} />
                                                        <span className="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-pulse" style={{ animationDelay: "300ms" }} />
                                                    </div>
                                                ) : null}
                                                {msg.isStreaming && msg.content && (
                                                    <span className="inline-block w-0.5 h-4 bg-neutral-400 animate-pulse ml-0.5" />
                                                )}
                                                {!msg.isStreaming && msg.sources && msg.sources.length > 0 && (
                                                    <SourcesPanel sources={msg.sources} />
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>
            </div>

            {/* Input Area */}
            <div className="flex-shrink-0 border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                <div className="max-w-2xl mx-auto px-6 py-4">
                    <div className="flex items-end gap-3">
                        <div className="flex-1 relative">
                            <TextareaAutosize
                                ref={inputRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                onCompositionStart={handleCompositionStart}
                                onCompositionEnd={handleCompositionEnd}
                                placeholder="Ask anything..."
                                disabled={isLoading}
                                minRows={1}
                                maxRows={6}
                                className="w-full resize-none bg-neutral-100 dark:bg-neutral-800 border-0 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white placeholder:text-neutral-400 dark:placeholder:text-neutral-500"
                            />
                        </div>
                        {isLoading ? (
                            <Button
                                onClick={handleStop}
                                size="icon"
                                className="h-11 w-11 rounded-xl bg-neutral-900 dark:bg-white hover:bg-neutral-800 dark:hover:bg-neutral-100"
                            >
                                <Square className="w-4 h-4 fill-current text-white dark:text-neutral-900" />
                            </Button>
                        ) : (
                            <Button
                                onClick={() => handleSend()}
                                disabled={!input.trim()}
                                size="icon"
                                className="h-11 w-11 rounded-xl bg-neutral-900 dark:bg-white hover:bg-neutral-800 dark:hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed"
                            >
                                <Send className="w-4 h-4 text-white dark:text-neutral-900" />
                            </Button>
                        )}
                    </div>
                    <p className="text-xs text-center text-neutral-400 mt-3">
                        Enter to send · Shift+Enter for new line
                    </p>
                </div>
            </div>
        </div>
    );
}
