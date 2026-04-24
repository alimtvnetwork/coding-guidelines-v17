import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, ShieldCheck, Activity, CheckCircle2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import versionInfo from "../../version.json";

interface PillarCard {
  icon: typeof BookOpen;
  title: string;
  description: string;
  to: string;
  cta: string;
}

const pillarCards: PillarCard[] = [
  {
    icon: BookOpen,
    title: "Browse the Specs",
    description: "Read the full spec tree — cross-language standards, TypeScript, Go, database conventions, and more.",
    to: "/docs",
    cta: "Open docs viewer",
  },
  {
    icon: ShieldCheck,
    title: "Code Review Checklist",
    description: "Run through the canonical CODE RED checklist before opening a pull request.",
    to: "/checklist",
    cta: "Open checklist",
  },
  {
    icon: Activity,
    title: "CI / Linter Dashboard",
    description: "Live pass/fail status, recent runs, health score and tracked rules pulled from the validator.",
    to: "/dashboard",
    cta: "Open dashboard",
  },
];

const headlineRules = [
  "Zero nested if statements — flatten every conditional",
  "Booleans always start with is or has, max 2 operands",
  "Functions ≤ 15 lines, files ≤ 300 lines, components ≤ 100 lines",
  "Never swallow errors — explicit file/path logging required",
];

export default function Index() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <IndexHero />
      <IndexHighlights />
      <IndexPillars />
    </main>
  );
}

function IndexHero() {
  return (
    <section className="relative overflow-hidden border-b border-border/60 bg-mesh-hero animate-gradient-pan">
      <div className="container relative mx-auto px-6 py-24 text-center">
        <span className="mb-5 inline-flex animate-fade-in-up items-center gap-2 rounded-full border border-border/60 bg-card/70 px-4 py-1.5 text-sm text-muted-foreground backdrop-blur">
          <span className="status-dot" aria-hidden="true" />
          v{versionInfo.version} — Production-Ready
        </span>
        <h1 className="mx-auto max-w-3xl animate-fade-in-up font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl [animation-delay:80ms]">
          <span className="text-gradient-brand animate-gradient-pan">Coding Guidelines</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl animate-fade-in-up text-lg text-muted-foreground [animation-delay:160ms]">
          One canonical source of truth for TypeScript, Go, PHP, Rust, and C# —
          tuned for AI assistants and human reviewers alike.
        </p>
        <div className="mt-8 flex animate-fade-in-up flex-wrap items-center justify-center gap-3 [animation-delay:240ms]">
          <Button asChild size="lg" className="shine-on-hover lift-hover">
            <Link to="/docs">
              <Sparkles className="mr-2 h-4 w-4" aria-hidden="true" />
              Browse Documentation
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="lift-hover">
            <Link to="/dashboard">View CI Dashboard</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

function IndexHighlights() {
  return (
    <section className="container mx-auto px-6 py-14">
      <h2 className="animate-fade-in-up font-heading text-2xl font-semibold">CODE RED at a glance</h2>
      <p className="mt-2 animate-fade-in-up text-sm text-muted-foreground [animation-delay:80ms]">
        Four rules that block merge if violated. Full enforcement runs in `linter-scripts/validate-guidelines.py`.
      </p>
      <ul className="stagger-children mt-6 grid gap-3 md:grid-cols-2">
        {headlineRules.map((rule) => (
          <li
            key={rule}
            className="lift-hover flex items-start gap-3 rounded-md border border-border/60 bg-card px-4 py-3 text-sm"
          >
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" aria-hidden="true" />
            <span>{rule}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function IndexPillars() {
  return (
    <section className="container mx-auto px-6 pb-24">
      <h2 className="animate-fade-in-up font-heading text-2xl font-semibold">Where to go next</h2>
      <div className="stagger-children mt-6 grid gap-4 md:grid-cols-3">
        {pillarCards.map((card) => (
          <PillarCardView key={card.to} card={card} />
        ))}
      </div>
    </section>
  );
}

function PillarCardView({ card }: { card: PillarCard }) {
  const Icon = card.icon;

  return (
    <Card className="ring-gradient lift-hover group relative overflow-hidden border-border/60">
      <CardHeader>
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary transition-transform duration-300 group-hover:scale-110">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
        <CardTitle className="mt-3 font-heading text-lg">{card.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">{card.description}</p>
        <Button asChild variant="outline" size="sm" className="shine-on-hover">
          <Link to={card.to}>
            {card.cta}
            <ArrowRight className="ml-2 h-3 w-3 transition-transform duration-300 group-hover:translate-x-1" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
