import Link from "next/link";
import Image from "next/image";
import {
  Search,
  MessageSquare,
  Upload,
  Shield,
  Zap,
  BarChart3,
  Layers,
  ArrowRight,
} from "lucide-react";

const features = [
  {
    icon: Upload,
    title: "Document Ingestion",
    description: "Upload PDFs, text files, and documents. Automatic text extraction, chunking, and embedding generation.",
  },
  {
    icon: Search,
    title: "Semantic Search",
    description: "Find relevant information across all your documents using AI-powered vector similarity search.",
  },
  {
    icon: MessageSquare,
    title: "RAG Chat",
    description: "Chat with your documents. Get cited, accurate answers powered by retrieval-augmented generation.",
  },
  {
    icon: Layers,
    title: "Multi-Model Support",
    description: "Switch between Llama 3, Mistral, Phi, DeepSeek, and more. Local models via Ollama.",
  },
  {
    icon: BarChart3,
    title: "Document Intelligence",
    description: "Automatic classification, clustering, and topic discovery across your knowledge base.",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "JWT authentication, workspace isolation, rate limiting, and role-based access control.",
  },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* ── Navigation ────────────────────────────────── */}
      <nav className="flex items-center justify-between px-6 lg:px-12 h-16 border-b border-border/30 glass sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg overflow-hidden">
            <Image src="/logo.png" alt="Aethel" width={36} height={36} className="object-cover" />
          </div>
          <span className="text-lg font-bold tracking-tight gradient-text">
            Aethel
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors px-4 py-2"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="text-sm font-medium bg-primary text-primary-foreground px-5 py-2 rounded-lg hover:opacity-90 transition-opacity"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* ── Hero Section ──────────────────────────────── */}
      <section className="flex flex-col items-center justify-center text-center px-6 pt-24 pb-20 relative overflow-hidden">
        {/* Background gradient orbs */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary/3 rounded-full blur-3xl" />

        <div className="relative z-10 max-w-4xl mx-auto animate-fade-in">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-medium text-muted-foreground mb-8">
            <Zap className="w-3 h-3 text-primary" />
            Powered by Local AI Models
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-6">
            Your Enterprise{" "}
            <span className="gradient-text">AI Knowledge</span>{" "}
            Operating System
          </h1>

          <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload documents. Ask questions. Get cited answers.
            Built with RAG, semantic search, and local LLMs — no data leaves your infrastructure.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center">
            <Link
              href="/register"
              className="group flex items-center gap-2 bg-primary text-primary-foreground px-8 py-3.5 rounded-xl text-sm font-semibold hover:opacity-90 transition-all glow"
            >
              Start Building
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/login"
              className="flex items-center gap-2 border border-border/50 px-8 py-3.5 rounded-xl text-sm font-medium text-muted-foreground hover:text-foreground hover:border-border transition-all"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* ── Features Grid ─────────────────────────────── */}
      <section className="px-6 lg:px-12 py-20 max-w-7xl mx-auto w-full">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            Everything you need for <span className="gradient-text">AI-powered</span> knowledge
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            A complete platform for document intelligence — from ingestion to insights.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature, i) => (
            <div
              key={feature.title}
              className="group p-6 rounded-2xl border border-border/30 bg-card/50 hover:bg-card hover:border-border/60 transition-all duration-300 hover:shadow-lg"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className="flex items-center justify-center w-11 h-11 rounded-xl bg-primary/10 text-primary mb-4 group-hover:scale-110 transition-transform">
                <feature.icon className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Tech Stack Section ────────────────────────── */}
      <section className="px-6 lg:px-12 py-16 border-t border-border/20">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-xs uppercase tracking-widest text-muted-foreground/60 mb-6 font-semibold">
            Built With
          </p>
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
            {["Next.js", "FastAPI", "PyTorch", "ChromaDB", "Ollama", "MySQL", "Tailwind CSS"].map(
              (tech) => (
                <span
                  key={tech}
                  className="px-4 py-2 rounded-full glass text-xs font-medium"
                >
                  {tech}
                </span>
              )
            )}
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────── */}
      <footer className="px-6 lg:px-12 py-8 border-t border-border/20 mt-auto">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/logo.png" alt="Aethel" width={16} height={16} className="object-cover rounded" />
            <span className="text-sm font-semibold">Aethel</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Enterprise AI RAG Platform · Built for production
          </p>
        </div>
      </footer>
    </div>
  );
}