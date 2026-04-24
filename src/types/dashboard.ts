// Strict named-interface types for the CI/CD dashboard data layer.
// Source files: version.json, public/health-score.json, public/ci-runs.json.

export type RunStatus = "passed" | "failed" | "running";
export type IssueStatus = "solved" | "pending";
export type RuleStatus = "cleared" | "active";

export interface VersionFolderStats {
  path: string;
  name: string;
  fileCount: number;
  lineCount: number;
  byteCount: number;
}

export interface VersionTotals {
  totalFiles: number;
  totalLines: number;
  totalFolders: number;
  totalBytes: number;
}

export interface VersionInfo {
  version: string;
  updated: string;
  stats: VersionTotals;
  folders: VersionFolderStats[];
}

export interface HealthScore {
  schemaVersion: number;
  generated: string;
  version: string;
  overallScore: number;
  grade: string;
  totals: { files: number; folders: number; lines: number };
  blindAiAudit: { version: string; score: number; handoffWeighted: number };
}

export interface CiIssue {
  number: number;
  slug: string;
  title: string;
  status: IssueStatus;
  date: string;
  rules: string[];
}

export interface CiRule {
  rule: string;
  occurrences: number;
  status: RuleStatus;
}

export interface CiRun {
  id: string;
  date: string;
  commitSha: string;
  status: RunStatus;
  durationSeconds: number;
  filesScanned: number;
  linesScanned: number;
  resolvedIssues: number[];
  note: string;
}

export interface CiRunsPayload {
  schemaVersion: number;
  generated: string;
  source: string;
  lastCleanRun: {
    date: string;
    version: string;
    filesScanned: number;
    linesScanned: number;
    violations: number;
  };
  issues: CiIssue[];
  rules: CiRule[];
  recentRuns: CiRun[];
}

export interface DashboardSnapshot {
  health: HealthScore;
  version: VersionInfo;
  ci: CiRunsPayload;
}
