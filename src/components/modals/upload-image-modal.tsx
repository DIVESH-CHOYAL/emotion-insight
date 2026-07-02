import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { UploadCloud, ImageIcon, ScanFace } from "lucide-react";

type Props = { open: boolean; onOpenChange: (v: boolean) => void };

export function UploadImageModal({ open, onOpenChange }: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl rounded-3xl p-0 overflow-hidden border-border/70">
        <div className="px-6 pt-6">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-semibold">
              <ImageIcon className="h-5 w-5 text-primary" />
              Upload Image
            </DialogTitle>
            <DialogDescription>
              Drop an image to analyze facial emotions.
            </DialogDescription>
          </DialogHeader>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
          <div className="flex flex-col rounded-2xl border-2 border-dashed border-border bg-secondary/40 p-8 items-center justify-center text-center min-h-[280px]">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-background shadow-soft">
              <UploadCloud className="h-6 w-6 text-primary" />
            </div>
            <div className="mt-4 text-sm font-medium">Drag & drop an image</div>
            <div className="mt-1 text-xs text-muted-foreground">PNG, JPG up to 10MB</div>
            <Button variant="outline" className="mt-5 rounded-xl">
              Browse Files
            </Button>
          </div>
          <div className="space-y-3">
            <div className="rounded-2xl border border-border/70 bg-card p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">
                Detected Face
              </div>
              <div className="mt-3 aspect-square w-full rounded-xl bg-secondary/60 flex items-center justify-center">
                <ScanFace className="h-6 w-6 text-muted-foreground" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-border/70 bg-card p-4">
                <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Emotion
                </div>
                <div className="mt-1 text-lg font-semibold">—</div>
              </div>
              <div className="rounded-2xl border border-border/70 bg-card p-4">
                <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Confidence
                </div>
                <div className="mt-1 text-lg font-semibold">—</div>
              </div>
            </div>
            <div className="rounded-2xl border border-border/70 bg-card p-4">
              <div className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">
                Probability Chart
              </div>
              <div className="h-24 rounded-xl bg-secondary/60" />
            </div>
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-border/70 bg-secondary/40 px-6 py-4">
          <Button variant="outline" className="rounded-xl" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button className="rounded-xl">Analyze</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
