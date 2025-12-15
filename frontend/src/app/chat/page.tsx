import Link from "next/link";
import { ArrowLeft, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatInterface } from "@/components/ChatInterface";

export default function ChatPage() {
    return (
        <div className="flex flex-col h-screen bg-neutral-50 dark:bg-neutral-950">
            {/* Minimal Header */}
            <header className="flex-shrink-0 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                <div className="max-w-2xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" asChild className="h-8 w-8 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800">
                            <Link href="/">
                                <ArrowLeft className="w-4 h-4" />
                            </Link>
                        </Button>
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-neutral-900 dark:bg-white flex items-center justify-center">
                                <MessageSquare className="w-4 h-4 text-white dark:text-neutral-900" />
                            </div>
                            <span className="font-medium text-sm text-neutral-900 dark:text-neutral-100">Chat</span>
                        </div>
                    </div>
                    <Button variant="ghost" size="sm" asChild className="text-xs text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100">
                        <Link href="/projects">Projects</Link>
                    </Button>
                </div>
            </header>

            <ChatInterface />
        </div>
    );
}
