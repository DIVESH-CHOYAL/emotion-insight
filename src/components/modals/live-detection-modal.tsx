import { useState, useEffect, useRef } from "react";
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
import { toast } from "sonner";

type Props = { open: boolean; onOpenChange: (v: boolean) => void };

// Simple array of colors for emotions if we wanted to display badge variants dynamically
const EMOTION_COLORS: Record<string, string> = {
  Angry: "bg-red-500/10 text-red-500 border-red-500/20",
  Disgusted: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  Fearful: "bg-orange-500/10 text-orange-500 border-orange-500/20",
  Happy: "bg-green-500/10 text-green-500 border-green-500/20",
  Neutral: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  Sad: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20",
  Surprised: "bg-pink-500/10 text-pink-500 border-pink-500/20",
};

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/70 bg-card p-4">
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold text-foreground">{value}</div>
    </div>
  );
}

export function LiveDetectionModal({ open, onOpenChange }: Props) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState<"Idle" | "Connecting" | "Streaming" | "Error">("Idle");
  const [emotion, setEmotion] = useState("—");
  const [confidence, setConfidence] = useState(0);
  const [faces, setFaces] = useState(0);
  const [fps, setFps] = useState(0);
  
  const pollingIntervalRef = useRef<any>(null);

  const startCamera = async () => {
    setStatus("Connecting");
    try {
      const response = await fetch("http://localhost:8000/camera/start", {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error("Failed to start camera");
      }
      setIsStreaming(true);
      setStatus("Streaming");
      toast.success("Camera feed started.");
    } catch (err) {
      console.error("Error starting camera:", err);
      setStatus("Error");
      toast.error("Could not access camera. Ensure the backend server is running.");
    }
  };

  const stopCamera = async () => {
    try {
      await fetch("http://localhost:8000/camera/stop", {
        method: "POST",
      });
    } catch (err) {
      console.error("Error stopping camera:", err);
    }
    cleanupStream();
    toast.info("Camera stopped.");
  };

  const cleanupStream = () => {
    setIsStreaming(false);
    setStatus("Idle");
    setEmotion("—");
    setConfidence(0);
    setFaces(0);
    setFps(0);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const captureSnapshot = () => {
    if (!isStreaming || status !== "Streaming") {
      toast.error("Webcam stream is not active.");
      return;
    }
    
    // Create an anchor and download snapshot
    const link = document.createElement("a");
    link.href = `http://localhost:8000/camera/snapshot?t=${new Date().getTime()}`;
    link.download = `EmotionSense_Capture_${new Date().getTime()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success("Snapshot downloaded.");
  };

  // Poll status endpoint
  useEffect(() => {
    if (isStreaming && status === "Streaming") {
      pollingIntervalRef.current = setInterval(async () => {
        try {
          const res = await fetch("http://localhost:8000/camera-status");
          if (res.ok) {
            const data = await res.json();
            setEmotion(data.emotion);
            setConfidence(data.confidence);
            setFaces(data.faces);
            setFps(data.fps);
          }
        } catch (err) {
          console.error("Failed to fetch camera status:", err);
        }
      }, 500);
    } else {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [isStreaming, status]);

  // Stop camera when closing modal
  useEffect(() => {
    if (!open) {
      if (isStreaming) {
        stopCamera();
      } else {
        cleanupStream();
      }
    }
  }, [open]);

  const emotionBadgeClass = emotion !== "—" ? EMOTION_COLORS[emotion] || "" : "";

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
              {isStreaming && status === "Streaming" ? (
                <img 
                  src="http://localhost:8000/video-feed" 
                  className="h-full w-full object-cover" 
                  alt="Live Webcam Feed" 
                  onError={() => {
                    toast.error("Stream interrupted.");
                    cleanupStream();
                  }}
                />
              ) : (
                <div className="text-center">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-background shadow-soft">
                    <Camera className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <p className="mt-3 text-sm text-muted-foreground">
                    {status === "Connecting" ? "Initializing webcam..." : "Camera feed will appear here"}
                  </p>
                </div>
              )}
              <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full bg-background/80 px-3 py-1 text-xs backdrop-blur">
                <Circle 
                  className={`h-2 w-2 ${
                    status === "Streaming" 
                      ? "fill-green-500 text-green-500" 
                      : status === "Connecting" 
                      ? "fill-yellow-500 text-yellow-500" 
                      : "fill-muted-foreground text-muted-foreground"
                  }`} 
                />
                <span className="text-muted-foreground">
                  {status === "Streaming" ? "Active" : status === "Connecting" ? "Connecting" : "Idle"}
                </span>
              </div>
            </div>
            <div className="rounded-2xl border border-border/70 bg-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="text-sm font-medium">Emotion Timeline</div>
                <span className="text-xs text-muted-foreground">Last 30s</span>
              </div>
              <div className="h-20 rounded-xl bg-secondary/60 flex items-center justify-center text-xs text-muted-foreground">
                Timeline visualization (Standard Placeholder)
              </div>
            </div>
          </div>
          <aside className="space-y-3">
            <div className="rounded-2xl border border-border/70 bg-card p-5">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">
                Current Emotion
              </div>
              <div className="mt-2 text-2xl font-semibold flex items-center gap-2">
                {emotion}
              </div>
              <div className="mt-1 text-sm text-muted-foreground">
                {emotion !== "—" ? `Primary detected emotion` : "Awaiting input"}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Metric label="Confidence" value={confidence > 0 ? `${Math.round(confidence)}%` : "—"} />
              <Metric label="Faces" value={faces.toString()} />
              <Metric label="FPS" value={fps > 0 ? fps.toString() : "—"} />
              <div className="rounded-2xl border border-border/70 bg-card p-4">
                <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Status
                </div>
                <Badge 
                  variant={status === "Streaming" ? "default" : "secondary"} 
                  className={`mt-2 rounded-full font-normal ${
                    status === "Streaming" ? "bg-green-500/10 text-green-500 border-green-500/20" : ""
                  }`}
                >
                  {status === "Streaming" ? "Connected" : status === "Connecting" ? "Connecting" : "Disconnected"}
                </Badge>
              </div>
            </div>
          </aside>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2 border-t border-border/70 bg-secondary/40 px-6 py-4">
          <Button variant="outline" className="rounded-xl" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button 
            variant="outline" 
            className="rounded-xl" 
            onClick={captureSnapshot} 
            disabled={!isStreaming || status !== "Streaming"}
          >
            <ImageDown className="h-4 w-4" /> Capture
          </Button>
          <Button 
            variant="outline" 
            className="rounded-xl" 
            onClick={stopCamera} 
            disabled={!isStreaming}
          >
            <CameraOff className="h-4 w-4" /> Stop
          </Button>
          <Button 
            className="rounded-xl" 
            onClick={startCamera} 
            disabled={isStreaming || status === "Connecting"}
          >
            <Camera className="h-4 w-4" /> Start Camera
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
