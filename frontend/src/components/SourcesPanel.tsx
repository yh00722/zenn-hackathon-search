"use client";

import { useState } from "react";
import { ChevronDown, ExternalLink, Award, Link as LinkIcon } from "lucide-react";
import * as Collapsible from "@radix-ui/react-collapsible";
import type { ChatResponse } from "@/lib/api";

interface SourcesPanelProps {
    sources: ChatResponse["sources"];
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
    const [isOpen, setIsOpen] = useState(false);

    if (!sources || sources.length === 0) return null;

    return (
        <Collapsible.Root open={isOpen} onOpenChange={setIsOpen} className="mt-6 pt-6 border-t border-neutral-200 dark:border-neutral-800">
            <Collapsible.Trigger className="flex items-center gap-2 text-sm text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors">
                <LinkIcon className="w-4 h-4" />
                <span className="font-medium">{sources.length} sources</span>
                <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
            </Collapsible.Trigger>

            <Collapsible.Content className="mt-4 space-y-2">
                {sources.map((source, i) => (
                    <a
                        key={i}
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 px-4 py-3 rounded-lg bg-neutral-100 dark:bg-neutral-800/50 hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-colors group"
                    >
                        <span className="w-6 h-6 rounded-md bg-neutral-200 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 text-xs font-medium flex items-center justify-center flex-shrink-0">
                            {i + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-neutral-800 dark:text-neutral-200 truncate">
                                    {source.project_name}
                                </span>
                                {source.is_winner && (
                                    <Award className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
                                )}
                            </div>
                            {source.edition && (
                                <span className="text-xs text-neutral-500">
                                    Vol.{source.edition}
                                </span>
                            )}
                        </div>
                        <ExternalLink className="w-4 h-4 text-neutral-400 group-hover:text-neutral-600 dark:group-hover:text-neutral-300 transition-colors flex-shrink-0" />
                    </a>
                ))}
            </Collapsible.Content>
        </Collapsible.Root>
    );
}
