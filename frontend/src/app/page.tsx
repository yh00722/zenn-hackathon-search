import Link from "next/link";
import { MessageSquare, BarChart3, Award, ArrowRight, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      {/* Header */}
      <header className="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-neutral-900 dark:bg-white flex items-center justify-center">
              <Zap className="w-4 h-4 text-white dark:text-neutral-900" />
            </div>
            <span className="font-medium text-neutral-900 dark:text-neutral-100">Hackathon Explorer</span>
          </div>
          <nav className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild className="text-neutral-600 dark:text-neutral-400">
              <Link href="/projects">Projects</Link>
            </Button>
            <Button size="sm" asChild className="bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:bg-neutral-800 dark:hover:bg-neutral-100 rounded-lg">
              <Link href="/chat">Chat</Link>
            </Button>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="py-24 md:py-32">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h1 className="text-4xl md:text-5xl font-light tracking-tight text-neutral-900 dark:text-neutral-100 mb-6">
            Explore 400+ AI Agent
            <br />
            <span className="font-medium">Hackathon Projects</span>
          </h1>
          <p className="text-lg text-neutral-500 dark:text-neutral-400 mb-10 max-w-xl mx-auto font-light leading-relaxed">
            Search, browse, and discover insights from three editions of the Zenn AI Agent Hackathon using natural language.
          </p>
          <div className="flex gap-3 justify-center">
            <Button asChild size="lg" className="h-12 px-6 rounded-xl bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:bg-neutral-800 dark:hover:bg-neutral-100">
              <Link href="/chat">
                <MessageSquare className="w-4 h-4 mr-2" />
                Start Chat
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="h-12 px-6 rounded-xl border-neutral-300 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800">
              <Link href="/projects">
                Browse Projects
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 border-t border-neutral-200 dark:border-neutral-800">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-6">
              <div className="w-10 h-10 rounded-xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center mb-4">
                <Award className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
              </div>
              <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">Award Winners</h3>
              <p className="text-neutral-500 dark:text-neutral-400 text-sm leading-relaxed">
                Explore winning projects with judge comments and learn what makes a great submission.
              </p>
            </div>
            <div className="p-6">
              <div className="w-10 h-10 rounded-xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center mb-4">
                <BarChart3 className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
              </div>
              <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">Rankings</h3>
              <p className="text-neutral-500 dark:text-neutral-400 text-sm leading-relaxed">
                See the most popular projects sorted by likes and engagement metrics.
              </p>
            </div>
            <div className="p-6">
              <div className="w-10 h-10 rounded-xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center mb-4">
                <MessageSquare className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
              </div>
              <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">RAG Chat</h3>
              <p className="text-neutral-500 dark:text-neutral-400 text-sm leading-relaxed">
                Ask questions in natural language and get answers with source references.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-20 bg-white dark:bg-neutral-900 border-y border-neutral-200 dark:border-neutral-800">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <p className="text-3xl font-light text-neutral-900 dark:text-neutral-100 mb-1">400+</p>
              <p className="text-sm text-neutral-500">Projects</p>
            </div>
            <div>
              <p className="text-3xl font-light text-neutral-900 dark:text-neutral-100 mb-1">3</p>
              <p className="text-sm text-neutral-500">Editions</p>
            </div>
            <div>
              <p className="text-3xl font-light text-neutral-900 dark:text-neutral-100 mb-1">20+</p>
              <p className="text-sm text-neutral-500">Winners</p>
            </div>
            <div>
              <p className="text-3xl font-light text-neutral-900 dark:text-neutral-100 mb-1">360+</p>
              <p className="text-sm text-neutral-500">Articles</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24">
        <div className="max-w-xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-light text-neutral-900 dark:text-neutral-100 mb-4">
            Ready to explore?
          </h2>
          <p className="text-neutral-500 dark:text-neutral-400 mb-8">
            Start a conversation and discover insights from hundreds of AI projects.
          </p>
          <Button asChild size="lg" className="h-12 px-8 rounded-xl bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:bg-neutral-800 dark:hover:bg-neutral-100">
            <Link href="/chat">
              Get Started
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-neutral-200 dark:border-neutral-800">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <p className="text-sm text-neutral-400">
            Data from <a href="https://zenn.dev" target="_blank" className="hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors">Zenn.dev</a>
          </p>
        </div>
      </footer>
    </div>
  );
}
