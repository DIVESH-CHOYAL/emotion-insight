import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Camera, CameraOff, Circle, ImageDown, Video } from "lucide-react";

type Props = { open: boolean; onOpenChange: (v: boolean) => void };

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/70 bg-card p-4">
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold text-foreground">{value}</div>
    </div>
  );
}

export function LiveDetectionModal({ open, onOpenChange }: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl rounded-3xl p-0 overflow-hidden border-border/70">
        <div className="px-6 pt-6">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-semibold">
              <Video className="h-5 w-5 text-primary" />
              Live Detection
            </DialogTitle>
            <DialogDescription>
              Real-time facial emotion detection from your webcam.
            </DialogDescription>
          </DialogHeader>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 p-6">
          <div className="space-y-4">
            <div className="relative aspect-video w-full rounded-2xl border border-border/70 bg-secondary/60 overflow-hidden flex items-center justify-center">
              <div className="text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-background shadow-soft">
                  <Camera className="h-6 w-6 text-muted-foreground" />
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                  Camera feed will appear here
                </p>
              </div>
              <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full bg-background/80 px-3 py-1 text-xs backdrop-blur">
                <Circle className="h-2 w-2 fill-muted-foreground text-muted-foreground" />
                <span className="text-muted-foreground">Idle</span>
              </div>
            </div>
            <div className="rounded-2xl border border-border/70 bg-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="text-sm font-medium">Emotion Timeline</div>
                <span className="text-xs text-muted-foreground">Last 30s</span>
              </div>
              <div className="h-20 rounded-xl bg-secondary/60" />
            </div>
          </div>
          <aside className="space-y-3">
            <div className="rounded-2xl border border-border/70 bg-card p-5">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">
                Current Emotion
              </div>
              <div className="mt-2 text-2xl font-semibold">—</div>
              <div className="mt-1 text-sm text-muted-foreground">Awaiting input</div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Metric label="Confidence" value="—" />
              <Metric label="Faces" value="0" />
              <Metric label="FPS" value="—" />
              <div className="rounded-2xl border border-border/70 bg-card p-4">
                <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Status
                </div>
                <Badge variant="secondary" className="mt-2 rounded-full font-normal">
                  Disconnected
                </Badge>
              </div>
            </div>
          </aside>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2 border-t border-border/70 bg-secondary/40 px-6 py-4">
          <Button variant="outline" className="rounded-xl" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button variant="outline" className="rounded-xl">
            <ImageDown className="h-4 w-4" /> Capture
          </Button>
          <Button variant="outline" className="rounded-xl">
            <CameraOff className="h-4 w-4" /> Stop
          </Button>
          <Button className="rounded-xl">
            <Camera className="h-4 w-4" /> Start Camera
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
