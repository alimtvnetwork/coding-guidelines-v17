import { useEffect, useRef, useState } from "react";

interface UseCountUpOptions {
  duration?: number;
  decimals?: number;
}

const DEFAULT_DURATION = 900;

function easeOutCubic(t: number): number {
  const inv = 1 - t;
  return 1 - inv * inv * inv;
}

export function useCountUp(target: number, options: UseCountUpOptions = {}): number {
  const duration = options.duration ?? DEFAULT_DURATION;
  const decimals = options.decimals ?? 0;
  const [value, setValue] = useState<number>(target);
  const fromRef = useRef<number>(target);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const prefersReduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReduce === true) {
      setValue(target);
      return;
    }

    const start = fromRef.current;
    const delta = target - start;

    if (delta === 0) {
      return;
    }

    const startTime = performance.now();
    const factor = Math.pow(10, decimals);

    const tick = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutCubic(progress);
      const next = start + delta * eased;

      setValue(Math.round(next * factor) / factor);

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }

      fromRef.current = target;
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
      fromRef.current = target;
    };
  }, [target, duration, decimals]);

  return value;
}
