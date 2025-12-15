"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Search, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ProjectCard } from "@/components/ProjectCard";
import { Leaderboard } from "@/components/Leaderboard";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { getProjects, searchProjects, type Project } from "@/lib/api";

export default function ProjectsPage() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [edition, setEdition] = useState<number | undefined>(undefined);
    const [offset, setOffset] = useState(0);
    const limit = 20;

    useEffect(() => {
        async function fetchProjects() {
            setLoading(true);
            try {
                if (searchQuery) {
                    const result = await searchProjects(searchQuery, edition);
                    setProjects(result.results);
                    setTotal(result.count);
                } else {
                    const result = await getProjects({ edition, limit, offset });
                    setProjects(result.projects);
                    setTotal(result.total);
                }
            } catch (error) {
                console.error("Failed to fetch projects:", error);
            } finally {
                setLoading(false);
            }
        }
        fetchProjects();
    }, [edition, offset, searchQuery]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setOffset(0);
    };

    return (
        <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
            {/* Header */}
            <header className="sticky top-0 z-10 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" asChild className="h-8 w-8 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800">
                            <Link href="/">
                                <ArrowLeft className="w-4 h-4" />
                            </Link>
                        </Button>
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-neutral-900 dark:bg-white flex items-center justify-center">
                                <Zap className="w-4 h-4 text-white dark:text-neutral-900" />
                            </div>
                            <span className="font-medium text-neutral-900 dark:text-neutral-100">Projects</span>
                        </div>
                    </div>
                    <Button variant="ghost" size="sm" asChild className="text-neutral-600 dark:text-neutral-400">
                        <Link href="/chat">Chat</Link>
                    </Button>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-8">
                <Tabs defaultValue="browse" className="w-full">
                    <TabsList className="mb-8 bg-neutral-100 dark:bg-neutral-800 p-1 rounded-lg">
                        <TabsTrigger value="browse" className="rounded-md px-4 py-2 text-sm data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-900">
                            Browse
                        </TabsTrigger>
                        <TabsTrigger value="ranking" className="rounded-md px-4 py-2 text-sm data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-900">
                            Rankings
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="browse">
                        {/* Search & Filter */}
                        <div className="flex flex-col md:flex-row gap-4 mb-8">
                            <form onSubmit={handleSearch} className="flex-1 flex gap-2">
                                <Input
                                    placeholder="Search projects..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="flex-1 h-10 rounded-lg bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800"
                                />
                                <Button type="submit" size="icon" className="h-10 w-10 rounded-lg bg-neutral-900 dark:bg-white hover:bg-neutral-800 dark:hover:bg-neutral-100">
                                    <Search className="w-4 h-4 text-white dark:text-neutral-900" />
                                </Button>
                            </form>
                            <div className="flex gap-2">
                                {[undefined, 1, 2, 3].map((e) => (
                                    <Button
                                        key={e ?? "all"}
                                        variant={edition === e ? "default" : "outline"}
                                        size="sm"
                                        onClick={() => { setEdition(e); setOffset(0); }}
                                        className={`rounded-lg ${edition === e
                                            ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900'
                                            : 'border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-800'}`}
                                    >
                                        {e ? `Vol.${e}` : 'All'}
                                    </Button>
                                ))}
                            </div>
                        </div>

                        {/* Results */}
                        <p className="text-sm text-neutral-500 mb-6">
                            {searchQuery ? `Results for "${searchQuery}": ` : ""}
                            {total} projects
                        </p>

                        {loading ? (
                            <div className="text-center py-16 text-neutral-400">Loading...</div>
                        ) : projects.length === 0 ? (
                            <div className="text-center py-16 text-neutral-400">No projects found</div>
                        ) : (
                            <>
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {projects.map((project) => (
                                        <ProjectCard key={project.id} project={project} />
                                    ))}
                                </div>

                                {!searchQuery && total > limit && (
                                    <div className="flex justify-center gap-3 mt-12">
                                        <Button
                                            variant="outline"
                                            disabled={offset === 0}
                                            onClick={() => setOffset(Math.max(0, offset - limit))}
                                            className="rounded-lg border-neutral-200 dark:border-neutral-800"
                                        >
                                            Previous
                                        </Button>
                                        <span className="flex items-center px-4 text-sm text-neutral-500">
                                            {Math.floor(offset / limit) + 1} / {Math.ceil(total / limit)}
                                        </span>
                                        <Button
                                            variant="outline"
                                            disabled={offset + limit >= total}
                                            onClick={() => setOffset(offset + limit)}
                                            className="rounded-lg border-neutral-200 dark:border-neutral-800"
                                        >
                                            Next
                                        </Button>
                                    </div>
                                )}
                            </>
                        )}
                    </TabsContent>

                    <TabsContent value="ranking">
                        <Leaderboard />
                    </TabsContent>
                </Tabs>
            </main>
        </div>
    );
}
