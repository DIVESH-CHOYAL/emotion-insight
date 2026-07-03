import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState, useEffect } from "react";
import { BACKEND_URL } from "@/lib/backend";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings � EmotionSense AI" },
      {
        name: "description",
        content: "Configure camera, confidence thresholds, theme, and detection preferences.",
      },
    ],
  }),
  component: SettingsPage,
});

function SettingsCard({ title, description, children }: { title: string; description?: string; children: React.ReactNode; }) {
  return (
    <div className="rounded-2xl border border-border/70 bg-card p-6 shadow-soft">
      <div className="mb-4">
        <h3 className="text-sm font-semibold">{title}</h3>
        {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
      </div>
      {children}
    </div>
  );
}

function ToggleRow({ label, description, checked, onCheckedChange }: { label: string; description: string; checked?: boolean; onCheckedChange?: (checked: boolean) => void; }) {
  return (
    <div className="flex items-center justify-between gap-4 py-3 border-t border-border/70 first:border-t-0 first:pt-0 last:pb-0">
      <div>
        <Label className="text-sm font-medium">{label}</Label>
        <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  );
}

function SettingsPage() {
  const [cameraIndex, setCameraIndex] = useState<number>(0);
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(35);
  const [drawBoundingBoxes, setDrawBoundingBoxes] = useState<boolean>(true);

  const [theme, setTheme] = useState<string>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("theme") || "light";
    }
    return "light";
  });
  const [notifications, setNotifications] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("notifications") !== "false";
    }
    return true;
  });
  const [animations, setAnimations] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("animations") !== "false";
    }
    return true;
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await fetch("${BACKEND_URL}/settings");
        if (res.ok) {
          const data = await res.json();
          setCameraIndex(data.camera_index);
          setConfidenceThreshold(data.confidence_threshold);
          setDrawBoundingBoxes(data.draw_bounding_boxes ?? true);
        }
      } catch (err) {
        console.error("Failed to load backend settings:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSettings();
  }, []);

  // Auto-apply frontend settings immediately
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
    if (typeof window !== "undefined") {
      localStorage.setItem("theme", theme);
    }
  }, [theme]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("notifications", notifications.toString());
    }
  }, [notifications]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("animations", animations.toString());
    }
  }, [animations]);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage("");
    
    try {
      const res = await fetch("${BACKEND_URL}/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          camera_index: cameraIndex,
          confidence_threshold: confidenceThreshold,
          draw_bounding_boxes: drawBoundingBoxes,
        }),
      });

      if (res.ok) {
        setSaveMessage("Settings saved & Applied!");
      } else {
        setSaveMessage("Failed to save camera settings.");
      }
    } catch (err) {
      console.error(err);
      setSaveMessage("Network error saving settings.");
    } finally {
      setIsSaving(false);
      setTimeout(() => setSaveMessage(""), 4000);
    }
  };

  if (isLoading) {
    return <div className="mx-auto max-w-4xl p-8 text-center text-muted-foreground">Loading settings...</div>;
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-2 text-sm text-muted-foreground">Configure your detection pipeline and interface preferences.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SettingsCard title="Camera" description="Choose the device used for live detection.">
          <Select value={cameraIndex.toString()} onValueChange={(val) => setCameraIndex(parseInt(val))}>
            <SelectTrigger className="rounded-xl h-10"><SelectValue /></SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="0">Default Camera (Webcam)</SelectItem>
              <SelectItem value="1">DroidCam Video</SelectItem>
            </SelectContent>
          </Select>
        </SettingsCard>

        <SettingsCard title="Theme" description="Interface color mode (Updates instantly).">
          <Select value={theme} onValueChange={(val) => setTheme(val)}>
            <SelectTrigger className="rounded-xl h-10"><SelectValue /></SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="light">Light</SelectItem>
              <SelectItem value="dark">Dark</SelectItem>
              <SelectItem value="system">System</SelectItem>
            </SelectContent>
          </Select>
        </SettingsCard>

        <SettingsCard title="Confidence Threshold" description={`Only surface detections above ${confidenceThreshold}% confidence.`}>
          <div className="pt-2">
            <Slider value={[confidenceThreshold]} onValueChange={(vals) => setConfidenceThreshold(vals[0])} max={100} step={1} />
            <div className="mt-2 flex justify-between text-xs text-muted-foreground"><span>0%</span><span>100%</span></div>
          </div>
        </SettingsCard>

        <SettingsCard title="Preferences" description="Fine-tune detection behavior.">
          <ToggleRow label="Notifications" description="Alert on new detections" checked={notifications} onCheckedChange={setNotifications} />
          <ToggleRow label="Bounding boxes" description="Draw boxes around detected faces on camera feed" checked={drawBoundingBoxes} onCheckedChange={setDrawBoundingBoxes} />
          <ToggleRow label="Animations" description="Enable UI motion" checked={animations} onCheckedChange={setAnimations} />
        </SettingsCard>
      </div>

      <div className="mt-8 flex items-center justify-end gap-4">
        {saveMessage && <span className="text-sm font-medium text-green-600 dark:text-green-400">{saveMessage}</span>}
        <Button className="rounded-xl h-11 px-6" onClick={handleSave} disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Backend Changes"}
        </Button>
      </div>
    </div>
  );
}

