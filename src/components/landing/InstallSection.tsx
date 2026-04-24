import { Terminal } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import versionData from "@/../version.json";
import bundlesManifest from "@/../bundles.json";
import { CopyButton } from "./install/CopyButton";
import { HighlightedCommand } from "./install/HighlightedCommand";
import { BundleCard, type BundleCommand } from "./install/BundleCard";

type InstallCommand = {
  platform: string;
  shell: string;
  command: string;
};

const installCommands: InstallCommand[] = [
  {
    platform: "Windows",
    shell: "PowerShell",
    command: "irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.ps1 | iex",
  },
  {
    platform: "Windows (skip latest probe)",
    shell: "PowerShell",
    command: "& ([scriptblock]::Create((irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.ps1))) -n",
  },
  {
    platform: "macOS / Linux",
    shell: "Bash",
    command: "curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.sh | bash",
  },
  {
    platform: "macOS / Linux (skip latest probe)",
    shell: "Bash",
    command: "curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.sh | bash -s -- -n",
  },
];

const RAW_BASE = bundlesManifest.rawBase;

const bundleCommands: BundleCommand[] = bundlesManifest.bundles.map((b) => ({
  bundle: b.name,
  description: b.description,
  folders: b.folders.map((f) => f.dest),
  bash: `curl -fsSL ${RAW_BASE}/${b.name}-install.sh | bash`,
  ps: `irm ${RAW_BASE}/${b.name}-install.ps1 | iex`,
  archive: `${b.archive.stableName}.zip`,
}));

const SHA256_BIT_LENGTH = 256;

function InstallCardHeader({ item }: { item: InstallCommand }) {
  return (
    <CardHeader className="pb-3">
      <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
        <Terminal className="h-4 w-4 text-primary" />
        {item.platform}
        <span className="ml-auto rounded-full border border-border bg-secondary px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {item.shell}
        </span>
      </CardTitle>
    </CardHeader>
  );
}

function InstallCardBody({ command }: { command: string }) {
  return (
    <CardContent>
      <div className="flex items-center gap-2 rounded-md border border-border bg-secondary/60 px-3 py-2.5 font-mono text-foreground/90">
        <span className="mr-1 select-none text-muted-foreground/60">$</span>
        <code className="flex-1 break-all text-[11px] leading-relaxed sm:text-xs md:text-sm md:break-normal md:whitespace-nowrap">
          <HighlightedCommand command={command} />
        </code>
        <CopyButton command={command} />
      </div>
    </CardContent>
  );
}

function InstallCard({ item }: { item: InstallCommand }) {
  return (
    <Card className="overflow-hidden border-border/60 bg-card/50 transition-colors hover:border-primary/40">
      <InstallCardHeader item={item} />
      <InstallCardBody command={item.command} />
    </Card>
  );
}

function InstallHeading() {
  return (
    <div className="mb-10 text-center">
      <div className="flex items-center justify-center gap-3">
        <h2 className="text-3xl font-bold text-foreground">Install in One Line</h2>
        <Badge variant="secondary" className="text-xs">
          Latest: v{versionData.version}
        </Badge>
      </div>
      <p className="mt-3 text-muted-foreground">
        Version-pinned install scripts with SHA-{SHA256_BIT_LENGTH} verification
      </p>
    </div>
  );
}

function InstallList() {
  return (
    <div className="flex flex-col gap-4">
      {installCommands.map((item) => (
        <InstallCard key={item.platform} item={item} />
      ))}
    </div>
  );
}

function BundleHeading() {
  return (
    <div className="mb-6 text-center">
      <h3 className="text-2xl font-bold text-foreground">Named Bundle Installers</h3>
      <p className="mt-2 text-sm text-muted-foreground">
        Install just the spec folders you need — each bundle wraps the main installer with a curated folder list.
      </p>
    </div>
  );
}

function BundleGrid() {
  return (
    <div className="mt-16">
      <BundleHeading />
      <div className="grid gap-4 md:grid-cols-2">
        {bundleCommands.map((bundle) => (
          <BundleCard key={bundle.bundle} bundle={bundle} />
        ))}
      </div>
    </div>
  );
}

export function InstallSection() {
  return (
    <section className="border-y border-border bg-secondary/20 py-20">
      <div className="mx-auto max-w-6xl px-6">
        <InstallHeading />
        <InstallList />
        <BundleGrid />
      </div>
    </section>
  );
}
