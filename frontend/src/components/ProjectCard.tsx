"use client";

import Link from "next/link";
import { Heart, Bookmark, Award, ExternalLink, Users, User } from "lucide-react";
import type { Project, LeaderboardItem } from "@/lib/api";

interface ProjectCardProps {
    project: Project | LeaderboardItem;
    rank?: number;
}

export function ProjectCard({ project, rank }: ProjectCardProps) {
    const isLeaderboard = "rank" in project;
    const edition = isLeaderboard ? project.edition : (project as Project).hackathon_id;

    return (
        <div className="group p-5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 hover:border-neutral-300 dark:hover:border-neutral-700 transition-colors">
            <div className="flex items-start gap-4">
                {rank && (
                    <span className={`
                        text-sm font-medium w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                        ${rank <= 3
                            ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900'
                            : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'}
                    `}>
                        {rank}
                    </span>
                )}
                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3 mb-2">
                        <h3 className="font-medium text-neutral-900 dark:text-neutral-100 line-clamp-2 text-sm leading-snug">
                            {project.project_name}
                        </h3>
                        {project.is_winner && (
                            <Award className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                        )}
                    </div>

                    {"description" in project && project.description && (
                        <p className="text-xs text-neutral-500 line-clamp-2 mb-3">
                            {project.description}
                        </p>
                    )}

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 text-xs text-neutral-400">
                            <span className="flex items-center gap-1">
                                <Heart className="w-3.5 h-3.5" />
                                {project.likes}
                            </span>
                            <span className="flex items-center gap-1">
                                <Bookmark className="w-3.5 h-3.5" />
                                {project.bookmarks}
                            </span>
                            <span>Vol.{edition}</span>
                        </div>
                        <Link
                            href={project.url}
                            target="_blank"
                            className="p-1.5 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
                        >
                            <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                    </div>

                    <div className="mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center gap-1.5 text-xs text-neutral-400">
                        {"author_type" in project && (project as Project).author_type === "チーム" ? (
                            <Users className="w-3 h-3" />
                        ) : (
                            <User className="w-3 h-3" />
                        )}
                        <span>{project.author_name}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
