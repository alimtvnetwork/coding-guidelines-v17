import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";
import { useCountUp } from "@/hooks/useCountUp";

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  caption: string;
  tone?: "default" | "success" | "warning";
  /** Optional numeric value — when provided, animates with a count-up effect. */
  numericValue?: number;
  /** Format for the count-up output (defaults to localeString). */
  formatValue?: (value: number) => string;
}

const TONE_CLASS: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "text-primary",
  success: "text-success",
  warning: "text-warning",
};

const defaultFormatter = (value: number): string => Math.round(value).toLocaleString();

export function MetricCard({
  icon: Icon,
  label,
  value,
  caption,
  tone = "default",
  numericValue,
  formatValue,
}: MetricCardProps) {
  const accentClass = TONE_CLASS[tone];
  const hasNumeric = typeof numericValue === "number";
  const animated = useCountUp(hasNumeric === true ? (numericValue as number) : 0);
  const displayValue = hasNumeric === true ? (formatValue ?? defaultFormatter)(animated) : value;

  const [flashKey, setFlashKey] = useState<number>(0);
  const [captionKey, setCaptionKey] = useState<number>(0);
  const previousValueRef = useRef<string>(value);
  const previousNumericRef = useRef<number | undefined>(numericValue);
  const previousToneRef = useRef<MetricCardProps["tone"]>(tone);
  const previousCaptionRef = useRef<string>(caption);

  useEffect(() => {
    const valueChanged = previousValueRef.current !== value;
    const numericChanged = previousNumericRef.current !== numericValue;
    const toneChanged = previousToneRef.current !== tone;
    const isFirstRender = previousValueRef.current === value && previousNumericRef.current === numericValue && previousToneRef.current === tone;

    if (isFirstRender === true) {
      return;
    }

    if (valueChanged === true || numericChanged === true || toneChanged === true) {
      setFlashKey((prev) => prev + 1);
    }

    previousValueRef.current = value;
    previousNumericRef.current = numericValue;
    previousToneRef.current = tone;
  }, [value, numericValue, tone]);

  useEffect(() => {
    if (previousCaptionRef.current === caption) {
      return;
    }
    setCaptionKey((prev) => prev + 1);
    previousCaptionRef.current = caption;
  }, [caption]);

  return (
    <Card className="lift-hover group relative overflow-hidden border-border/60">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <span className={`tone-transition inline-flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3 ${accentClass}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
      </CardHeader>
      <CardContent>
        <div
          key={flashKey}
          className={`tone-transition value-flash text-3xl font-heading font-semibold ${accentClass}`}
          aria-live="polite"
        >
          {displayValue}
        </div>
        <p
          key={captionKey}
          className="caption-fade mt-1 text-xs text-muted-foreground"
        >
          {caption}
        </p>
      </CardContent>
    </Card>
  );
}
