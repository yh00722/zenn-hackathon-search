// API client for backend
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Project {
    id: number;
    project_name: string;
    url: string;
    author_name: string;
    author_type: string;
    description: string;
    likes: number;
    bookmarks: number;
    is_winner: boolean;
    award_name: string | null;
    award_comment: string | null;
    hackathon_id: number;
    is_final_pitch: boolean;
    content_raw?: string;
}

export interface LeaderboardItem {
    rank: number;
    project_name: string;
    url: string;
    author_name: string;
    likes: number;
    bookmarks: number;
    is_winner: boolean;
    award_name: string | null;
    edition: number;
}

export interface ChatResponse {
    answer: string;
    sources: Array<{
        project_name: string;
        url: string;
        edition: number;
        is_winner: boolean;
    }>;
}

export interface Stats {
    total_projects: number;
    edition_1: number;
    edition_2: number;
    edition_3: number;
    winners: number;
}

// API Functions
export async function getStats(): Promise<Stats> {
    const res = await fetch(`${API_BASE}/api/stats`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
}

export async function getProjects(params?: {
    edition?: number;
    limit?: number;
    offset?: number;
    winners_only?: boolean;
}): Promise<{ total: number; projects: Project[] }> {
    const searchParams = new URLSearchParams();
    if (params?.edition) searchParams.set('edition', String(params.edition));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    if (params?.winners_only) searchParams.set('winners_only', 'true');

    const res = await fetch(`${API_BASE}/api/projects?${searchParams}`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
}

export async function getLeaderboard(params?: {
    edition?: number;
    limit?: number;
}): Promise<{ leaderboard: LeaderboardItem[] }> {
    const searchParams = new URLSearchParams();
    if (params?.edition) searchParams.set('edition', String(params.edition));
    if (params?.limit) searchParams.set('limit', String(params.limit));

    const res = await fetch(`${API_BASE}/api/projects/leaderboard?${searchParams}`);
    if (!res.ok) throw new Error('Failed to fetch leaderboard');
    return res.json();
}

export async function getWinners(edition?: number): Promise<{ winners: Project[] }> {
    const searchParams = new URLSearchParams();
    if (edition) searchParams.set('edition', String(edition));

    const res = await fetch(`${API_BASE}/api/projects/winners?${searchParams}`);
    if (!res.ok) throw new Error('Failed to fetch winners');
    return res.json();
}

export async function getProject(id: number): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/projects/${id}`);
    if (!res.ok) throw new Error('Failed to fetch project');
    return res.json();
}

export async function searchProjects(q: string, edition?: number): Promise<{
    query: string;
    count: number;
    results: Project[];
}> {
    const searchParams = new URLSearchParams({ q });
    if (edition) searchParams.set('edition', String(edition));

    const res = await fetch(`${API_BASE}/api/search?${searchParams}`);
    if (!res.ok) throw new Error('Failed to search');
    return res.json();
}

export async function chat(message: string): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
    });
    if (!res.ok) throw new Error('Failed to send message');
    return res.json();
}

export interface StreamCallbacks {
    signal?: AbortSignal;
    onMetadata?: (metadata: { strategy: string; sources: ChatResponse['sources']; explanation?: string }) => void;
    onToken?: (token: string) => void;
    onDone?: () => void;
    onError?: (error: string) => void;
}

export async function chatStream(message: string, callbacks: StreamCallbacks): Promise<void> {
    const res = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
        signal: callbacks.signal,
    });

    if (!res.ok) {
        throw new Error('Failed to start stream');
    }

    const reader = res.body?.getReader();
    if (!reader) {
        throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    let currentEventType = '';

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('event:')) {
                    currentEventType = line.slice(6).trim();
                    continue;
                }
                if (line.startsWith('data:')) {
                    const dataStr = line.slice(5).trim();
                    if (!dataStr) continue;

                    try {
                        const data = JSON.parse(dataStr);

                        // Use event type for accurate dispatch
                        switch (currentEventType) {
                            case 'metadata':
                                callbacks.onMetadata?.(data);
                                break;
                            case 'token':
                                callbacks.onToken?.(data.content);
                                break;
                            case 'done':
                                callbacks.onDone?.();
                                break;
                            case 'error':
                                callbacks.onError?.(data.message);
                                break;
                            default:
                                // Fallback: infer from data structure for backward compatibility
                                if (data.strategy !== undefined) {
                                    callbacks.onMetadata?.(data);
                                } else if (data.content !== undefined) {
                                    callbacks.onToken?.(data.content);
                                } else if (data.status === 'complete') {
                                    callbacks.onDone?.();
                                } else if (data.message !== undefined) {
                                    callbacks.onError?.(data.message);
                                }
                        }
                    } catch {
                        // Ignore parse errors for incomplete data
                    }
                    currentEventType = ''; // Reset after processing
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}
