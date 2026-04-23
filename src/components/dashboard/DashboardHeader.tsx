import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ExternalLink } from "lucide-react";

interface DashboardHeaderProps {
  version: string;
  generatedAt: string;
}

export function DashboardHeader({ version, generatedAt }: DashboardHeaderProps) {
  const generatedLabel = formatGenerated(generatedAt);

  return (
    <header className="border-b border-border/60 bg-card/40 backdrop-blur">
      <div className="container flex flex-wrap items-center justify-between gap-4 py-6">
        <div>
          <Button variant="ghost" size="sm" asChild className="-ml-3 mb-2 text-muted-foreground">
            <Link to="/">
              <ArrowLeft className="mr-1 h-4 w-4" />
              Back to landing
            </Link>
          </Button>
          <h1 className="font-heading text-3xl font-semibold">CI / Linter Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            v{version} · snapshot generated {generatedLabel}
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link to="/docs?file=.lovable/cicd-index.md">
            View CI/CD index
            <ExternalLink className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </div>
    </header>
  );
}

function formatGenerated(iso: string): string {
  const safeIso = iso.length > 0 ? iso : new Date().toISOString();

  return new Date(safeIso).toLocaleString();
}
