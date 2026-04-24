import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  caption: string;
  tone?: "default" | "success" | "warning";
}

const TONE_CLASS: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "text-primary",
  success: "text-success",
  warning: "text-warning",
};

export function MetricCard({ icon: Icon, label, value, caption, tone = "default" }: MetricCardProps) {
  const accentClass = TONE_CLASS[tone];

  return (
    <Card className="lift-hover group relative overflow-hidden border-border/60">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <span className={`inline-flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3 ${accentClass}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
      </CardHeader>
      <CardContent>
        <div className={`animate-fade-in-up text-3xl font-heading font-semibold ${accentClass}`}>{value}</div>
        <p className="mt-1 animate-fade-in text-xs text-muted-foreground [animation-delay:120ms]">{caption}</p>
      </CardContent>
    </Card>
  );
}
