import { useMemo, useState } from "react";
import { ArrowUpDown, CheckCircle2, ExternalLink, GitBranch, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CiRun } from "@/types/dashboard";

type SortKey = "date" | "branch" | "duration" | "status";
type SortDirection = "asc" | "desc";

interface RecentRunsTableProps {
  runs: CiRun[];
}

const isPassed = (status: CiRun["status"]): boolean => status === "passed";
const isAscending = (direction: SortDirection): boolean => direction === "asc";

export function RecentRunsTable({ runs }: RecentRunsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const sortedRuns = useMemo(() => sortRuns(runs, sortKey, sortDirection), [runs, sortKey, sortDirection]);
  const hasRuns = sortedRuns.length > 0;

  const toggleSort = (key: SortKey): void => {
    const isSameKey = sortKey === key;

    if (isSameKey === true) {
      setSortDirection(isAscending(sortDirection) === true ? "desc" : "asc");
      return;
    }

    setSortKey(key);
    setSortDirection("desc");
  };

  return (
    <Card className="border-border/60">
      <CardHeader>
        <CardTitle className="font-heading">Recent Runs</CardTitle>
        <p className="text-sm text-muted-foreground">
          Click a column header to sort. Each row links to the GitHub Actions log.
        </p>
      </CardHeader>
      <CardContent>
        {hasRuns === false ? (
          <p className="text-sm text-muted-foreground">No runs recorded.</p>
        ) : (
          <RunsTableBody runs={sortedRuns} onSort={toggleSort} sortKey={sortKey} />
        )}
      </CardContent>
    </Card>
  );
}

interface RunsTableBodyProps {
  runs: CiRun[];
  sortKey: SortKey;
  onSort: (key: SortKey) => void;
}

function RunsTableBody({ runs, sortKey, onSort }: RunsTableBodyProps) {
  return (
    <div className="overflow-x-auto rounded-md border border-border/60">
      <Table>
        <TableHeader>
          <TableRow>
            <SortableHeader label="Date" sortKey="date" activeKey={sortKey} onSort={onSort} />
            <SortableHeader label="Branch" sortKey="branch" activeKey={sortKey} onSort={onSort} />
            <TableHead>Commit</TableHead>
            <SortableHeader label="Duration" sortKey="duration" activeKey={sortKey} onSort={onSort} />
            <SortableHeader label="Status" sortKey="status" activeKey={sortKey} onSort={onSort} />
            <TableHead className="text-right">Logs</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {runs.map((run) => (
            <RunRow key={run.id} run={run} />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

interface SortableHeaderProps {
  label: string;
  sortKey: SortKey;
  activeKey: SortKey;
  onSort: (key: SortKey) => void;
}

function SortableHeader({ label, sortKey, activeKey, onSort }: SortableHeaderProps) {
  const isActive = activeKey === sortKey;
  const tone = isActive === true ? "text-foreground" : "text-muted-foreground";

  return (
    <TableHead>
      <button
        type="button"
        onClick={() => onSort(sortKey)}
        className={`inline-flex items-center gap-1 text-xs font-medium uppercase tracking-wide ${tone} hover:text-foreground`}
      >
        {label}
        <ArrowUpDown className="h-3 w-3" aria-hidden="true" />
      </button>
    </TableHead>
  );
}

function RunRow({ run }: { run: CiRun }) {
  const passed = isPassed(run.status);
  const StatusIcon = passed === true ? CheckCircle2 : XCircle;
  const statusVariant = passed === true ? "secondary" : "destructive";
  const statusTone = passed === true ? "text-success" : "text-destructive";

  return (
    <TableRow>
      <TableCell className="font-mono text-sm">{run.date}</TableCell>
      <TableCell>
        <span className="inline-flex items-center gap-1 text-sm">
          <GitBranch className="h-3 w-3 text-muted-foreground" aria-hidden="true" />
          {run.branch}
        </span>
      </TableCell>
      <TableCell>
        <code className="rounded bg-secondary px-2 py-0.5 font-mono text-xs">{run.commitSha}</code>
      </TableCell>
      <TableCell className="font-mono text-sm">{run.durationSeconds}s</TableCell>
      <TableCell>
        <Badge variant={statusVariant} className="inline-flex items-center gap-1 uppercase">
          <StatusIcon className={`h-3 w-3 ${statusTone}`} aria-hidden="true" />
          {run.status}
        </Badge>
      </TableCell>
      <TableCell className="text-right">
        <Button variant="ghost" size="sm" asChild>
          <a href={run.logUrl} target="_blank" rel="noopener noreferrer">
            View
            <ExternalLink className="ml-1 h-3 w-3" />
          </a>
        </Button>
      </TableCell>
    </TableRow>
  );
}

function sortRuns(runs: CiRun[], key: SortKey, direction: SortDirection): CiRun[] {
  const copy = [...runs];
  const factor = isAscending(direction) === true ? 1 : -1;

  copy.sort((a, b) => {
    const left = pickSortValue(a, key);
    const right = pickSortValue(b, key);
    const isLess = left < right;
    const isMore = left > right;

    if (isLess === true) return -1 * factor;
    if (isMore === true) return 1 * factor;
    return 0;
  });

  return copy;
}

function pickSortValue(run: CiRun, key: SortKey): string | number {
  if (key === "duration") return run.durationSeconds;
  if (key === "branch") return run.branch;
  if (key === "status") return run.status;
  return run.date;
}
