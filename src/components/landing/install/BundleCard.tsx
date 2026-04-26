import { Package } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CommandRow } from "./CommandRow";

export type BundleCommand = {
  bundle: string;
  description: string;
  folders: string[];
  bash: string;
  ps: string;
  archive: string;
};

function BundleCardHeader({ bundle }: { bundle: BundleCommand }) {
  const folderSuffix = bundle.folders.length === 1 ? "" : "s";

  return (
    <CardHeader className="pb-3">
      <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
        <Package className="h-4 w-4 text-primary" />
        <span className="font-mono text-sm">{bundle.bundle}</span>
        <span className="ml-auto rounded-full border border-border bg-secondary px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {bundle.folders.length} folder{folderSuffix}
        </span>
      </CardTitle>
      <p className="mt-1 text-xs text-muted-foreground">{bundle.description}</p>
    </CardHeader>
  );
}

function BundleFoldersList({ folders }: { folders: string[] }) {
  return (
    <ul className="mt-2 flex flex-wrap gap-1.5">
      {folders.map((folder) => (
        <li
          key={folder}
          className="rounded-md border border-border/60 bg-secondary/40 px-2 py-0.5 font-mono text-[10px] text-muted-foreground"
        >
          {folder}
        </li>
      ))}
    </ul>
  );
}

export function BundleCard({ bundle }: { bundle: BundleCommand }) {
  return (
    <Card className="overflow-hidden border-border/60 bg-card/50 transition-colors hover:border-primary/40">
      <BundleCardHeader bundle={bundle} />
      <CardContent className="space-y-2">
        <CommandRow
          label="bash"
          command={bundle.bash}
          expandTitle={bundle.bundle}
          expandShell="Bash"
        />
        <CommandRow
          label="pwsh"
          command={bundle.ps}
          expandTitle={bundle.bundle}
          expandShell="PowerShell"
        />
        <BundleFoldersList folders={bundle.folders} />
      </CardContent>
    </Card>
  );
}