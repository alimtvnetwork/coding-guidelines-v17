import { Terminal } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CopyButton } from "./CopyButton";
import { HighlightedCommand } from "./HighlightedCommand";

interface CommandExpandDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  shell: string;
  command: string;
}

export function CommandExpandDialog({
  open,
  onOpenChange,
  title,
  shell,
  command,
}: CommandExpandDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl border-border/70 bg-card">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
            <Terminal className="h-4 w-4 text-primary" />
            {title}
            <span className="ml-2 rounded-full border border-border bg-secondary px-2 py-0.5 text-xs font-medium text-muted-foreground">
              {shell}
            </span>
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Full install command — wrapped for readability.
          </DialogDescription>
        </DialogHeader>

        <div className="relative rounded-md border border-border bg-secondary/60 p-4 font-mono">
          <div className="absolute right-2 top-2">
            <CopyButton command={command} />
          </div>
          <pre className="overflow-x-auto whitespace-pre-wrap break-all pr-10 text-xs leading-relaxed text-foreground/90 sm:text-sm">
            <code>
              <HighlightedCommand command={command} />
            </code>
          </pre>
        </div>
      </DialogContent>
    </Dialog>
  );
}