import { useDashboardData } from "@/hooks/useDashboardData";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { HealthTrendCard } from "@/components/dashboard/HealthTrendCard";
import { RuleStatusGrid } from "@/components/dashboard/RuleStatusGrid";
import { RecentRunsTimeline } from "@/components/dashboard/RecentRunsTimeline";
import { IssueLogCard } from "@/components/dashboard/IssueLogCard";
import { CheckCircle2, FileCode2, ScrollText, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const isLoaded = (status: string): boolean => status === "success";

export default function Dashboard() {
  const query = useDashboardData();
  const loaded = isLoaded(query.status);

  if (loaded === false) {
    return <DashboardFallback isError={query.isError} message={query.error?.message ?? null} />;
  }

  const { health, version, ci } = query.data;
  const lastRun = ci.lastCleanRun;
  const passLabel = lastRun.violations === 0 ? "Passing" : "Failing";

  return (
    <main className="min-h-screen bg-background">
      <DashboardHeader version={version.version} generatedAt={ci.generated} />
      <div className="container space-y-6 py-8">
        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            icon={CheckCircle2}
            label="Last validator run"
            value={passLabel}
            caption={`${lastRun.violations} violations · v${lastRun.version} · ${lastRun.date}`}
            tone="success"
          />
          <MetricCard
            icon={FileCode2}
            label="Files scanned"
            value={lastRun.filesScanned.toLocaleString()}
            caption={`${lastRun.linesScanned.toLocaleString()} lines covered`}
          />
          <MetricCard
            icon={ScrollText}
            label="Tracked rules"
            value={String(ci.rules.length)}
            caption={`${ci.issues.length} historical issues, all cleared`}
          />
          <MetricCard
            icon={AlertTriangle}
            label="Open issues"
            value={String(ci.issues.filter((issue) => issue.status === "pending").length)}
            caption="Pending CI/CD findings awaiting fix"
            tone="warning"
          />
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <HealthTrendCard
              score={health.overallScore}
              grade={health.grade}
              blindAuditScore={health.blindAiAudit.score}
              handoffScore={health.blindAiAudit.handoffWeighted}
            />
          </div>
          <div className="lg:col-span-2">
            <RecentRunsTimeline runs={ci.recentRuns} />
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <RuleStatusGrid rules={ci.rules} />
          <IssueLogCard issues={ci.issues} />
        </section>
      </div>
    </main>
  );
}

interface FallbackProps {
  isError: boolean;
  message: string | null;
}

function DashboardFallback({ isError, message }: FallbackProps) {
  const headline = isError === true ? "Could not load dashboard" : "Loading dashboard…";
  const detail = isError === true ? message ?? "Unknown error" : "Reading static JSON snapshots.";

  return (
    <main className="flex min-h-screen items-center justify-center bg-background">
      <Card className="max-w-md border-border/60">
        <CardContent className="space-y-2 p-6">
          <h1 className="font-heading text-xl font-semibold">{headline}</h1>
          <p className="text-sm text-muted-foreground">{detail}</p>
        </CardContent>
      </Card>
    </main>
  );
}
