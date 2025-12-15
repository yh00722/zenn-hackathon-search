"use client";

import { memo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy } from "lucide-react";

interface MessageContentProps {
    content: string;
}

function CodeBlock({ className, children, ...props }: React.ComponentPropsWithoutRef<"code">) {
    const [copied, setCopied] = useState(false);
    const match = /language-(\w+)/.exec(className || "");
    const isInline = !match && !className?.includes("block");

    const handleCopy = async () => {
        const text = String(children).replace(/\n$/, "");
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (isInline) {
        return (
            <code className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded text-sm font-mono text-neutral-800 dark:text-neutral-200" {...props}>
                {children}
            </code>
        );
    }

    return (
        <div className="relative group my-4">
            <button
                onClick={handleCopy}
                className="absolute right-3 top-3 p-1.5 rounded-md bg-neutral-200 dark:bg-neutral-700 hover:bg-neutral-300 dark:hover:bg-neutral-600 text-neutral-600 dark:text-neutral-300 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Copy"
            >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
            {match && (
                <span className="absolute left-3 top-3 text-xs text-neutral-400 font-mono">
                    {match[1]}
                </span>
            )}
            <pre className="bg-neutral-100 dark:bg-neutral-800/80 rounded-xl p-4 pt-10 overflow-x-auto border border-neutral-200 dark:border-neutral-700">
                <code className={`text-sm font-mono text-neutral-800 dark:text-neutral-200 ${className || ""}`} {...props}>
                    {children}
                </code>
            </pre>
        </div>
    );
}

export const MessageContent = memo(function MessageContent({ content }: MessageContentProps) {
    return (
        <div className="prose prose-neutral dark:prose-invert max-w-none prose-p:leading-relaxed prose-p:text-neutral-700 dark:prose-p:text-neutral-300 prose-headings:font-medium prose-headings:text-neutral-900 dark:prose-headings:text-neutral-100 prose-pre:p-0 prose-pre:bg-transparent prose-pre:border-0">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    code: CodeBlock,
                    table: ({ children }) => (
                        <div className="overflow-x-auto my-4 rounded-lg border border-neutral-200 dark:border-neutral-700">
                            <table className="min-w-full">
                                {children}
                            </table>
                        </div>
                    ),
                    th: ({ children }) => (
                        <th className="bg-neutral-100 dark:bg-neutral-800 px-4 py-2.5 text-left text-sm font-medium text-neutral-700 dark:text-neutral-300 border-b border-neutral-200 dark:border-neutral-700">
                            {children}
                        </th>
                    ),
                    td: ({ children }) => (
                        <td className="px-4 py-2.5 text-sm border-b border-neutral-100 dark:border-neutral-800">
                            {children}
                        </td>
                    ),
                    a: ({ href, children }) => (
                        <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-neutral-900 dark:text-neutral-100 underline underline-offset-2 hover:no-underline"
                        >
                            {children}
                        </a>
                    ),
                    ul: ({ children }) => (
                        <ul className="space-y-1 my-3">
                            {children}
                        </ul>
                    ),
                    li: ({ children }) => (
                        <li className="text-neutral-700 dark:text-neutral-300">
                            {children}
                        </li>
                    ),
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
});
