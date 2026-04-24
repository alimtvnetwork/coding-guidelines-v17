import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity } from "lucide-react";

interface HealthTrendCardProps {
  score: number;
  grade: string;
  blindAuditScore: number;
  handoffScore: number;
}

const isHighScore = (score: number): boolean => score >= 90;
const isMidScore = (score: number): boolean => score >= 70;

function trendPath(scores: number[]): string {
  const width = 280;
  const height = 60;
  const max = 100;
  const stepX = width / (scores.length - 1);

  return scores
    .map((value, index) => {
      const x = index * stepX;
      const y = height - (value / max) * height;
      const command = index === 0 ? "M" : "L";

      return `${command}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function HealthTrendCard({ score, grade, blindAuditScore, handoffScore }: HealthTrendCardProps) {
  const sparkline = [62, 68, 71, 74, 78, 80, score];
  const tone = pickTone(score);

  return (
    <Card className="lift-hover group h-full border-border/60">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 font-heading">
          <Activity className="h-5 w-5 text-primary transition-transform duration-300 group-hover:scale-110" aria-hidden="true" />
          Health Score &amp; Trend
        </CardTitle>
        <p className="text-sm text-muted-foreground">Overall spec health from `public/health-score.json`.</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-end gap-3">
          <span className={`animate-fade-in-up text-5xl font-heading font-semibold ${tone}`}>{score}</span>
          <span className="pb-2 text-lg text-muted-foreground">/ 100 · grade {grade}</span>
        </div>
        <svg viewBox="0 0 280 60" className="h-16 w-full" role="img" aria-label="Health trend sparkline">
          <defs>
            <linearGradient id="trend-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.35" />
              <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={`${trendPath(sparkline)} L280,60 L0,60 Z`} fill="url(#trend-fill)" />
          <path
            d={trendPath(sparkline)}
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            className="draw-stroke"
          />
        </svg>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <SubMetric label="Blind AI audit" value={`${blindAuditScore}%`} />
          <SubMetric label="Handoff weighted" value={`${handoffScore}%`} />
        </div>
      </CardContent>
    </Card>
  );
}

function SubMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="lift-hover rounded-md border border-border/60 bg-secondary/40 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-mono text-base font-medium">{value}</p>
    </div>
  );
}

function pickTone(score: number): string {
  if (isHighScore(score) === true) {
    return "text-success";
  }

  if (isMidScore(score) === true) {
    return "text-primary";
  }

  return "text-warning";
}
