"use client";

import { useState, useEffect } from "react";
import { Award, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ProjectCard } from "@/components/ProjectCard";
import { getLeaderboard, getWinners, type LeaderboardItem, type Project } from "@/lib/api";

export function Leaderboard() {
    const [edition, setEdition] = useState<number | undefined>(undefined);
    const [leaderboard, setLeaderboard] = useState<LeaderboardItem[]>([]);
    const [winners, setWinners] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            setLoading(true);
            try {
                const [lb, w] = await Promise.all([
                    getLeaderboard({ edition, limit: 10 }),
                    getWinners(edition),
                ]);
                setLeaderboard(lb.leaderboard);
                setWinners(w.winners);
            } catch (error) {
                console.error("Failed to fetch data:", error);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, [edition]);

    return (
        <div className="space-y-8">
            {/* Edition Filter */}
            <div className="flex gap-2">
                {[undefined, 1, 2, 3].map((e) => (
                    <Button
                        key={e ?? "all"}
                        variant={edition === e ? "default" : "outline"}
                        size="sm"
                        onClick={() => setEdition(e)}
                        className={`rounded-lg ${edition === e
                            ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900'
                            : 'border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-800'}`}
                    >
                        {e ? `Vol.${e}` : 'All'}
                    </Button>
                ))}
            </div>

            <Tabs defaultValue="popular" className="w-full">
                <TabsList className="bg-neutral-100 dark:bg-neutral-800 p-1 rounded-lg">
                    <TabsTrigger value="popular" className="rounded-md px-4 py-2 text-sm data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-900 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" />
                        Popular
                    </TabsTrigger>
                    <TabsTrigger value="winners" className="rounded-md px-4 py-2 text-sm data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-900 flex items-center gap-2">
                        <Award className="w-4 h-4" />
                        Winners
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="popular" className="mt-6">
                    {loading ? (
                        <div className="text-center py-12 text-neutral-400">Loading...</div>
                    ) : (
                        <div className="grid gap-4 md:grid-cols-2">
                            {leaderboard.map((item) => (
                                <ProjectCard key={item.url} project={item} rank={item.rank} />
                            ))}
                        </div>
                    )}
                </TabsContent>

                <TabsContent value="winners" className="mt-6">
                    {loading ? (
                        <div className="text-center py-12 text-neutral-400">Loading...</div>
                    ) : winners.length === 0 ? (
                        <div className="text-center py-12 text-neutral-400">
                            No winners for this edition
                        </div>
                    ) : (
                        <div className="grid gap-4 md:grid-cols-2">
                            {winners.map((project) => (
                                <ProjectCard key={project.url} project={project} />
                            ))}
                        </div>
                    )}
                </TabsContent>
            </Tabs>
        </div>
    );
}
