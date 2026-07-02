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

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — EmotionSense AI" },
      {
        name: "description",
        content: "Configure camera, confidence thresholds, theme, and detection preferences.",
      },
      { property: "og:title", content: "Settings — EmotionSense AI" },
      { property: "og:description", content: "Detection and interface preferences." },
    ],
  }),
  component: SettingsPage,
});

function SettingsCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-border/70 bg-card p-6 shadow-soft">
      <div className="mb-4">
        <h3 className="text-sm font-semibold">{title}</h3>
        {description && (
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}

function ToggleRow({
  label,
  description,
  defaultChecked,
}: {
  label: string;
  description: string;
  defaultChecked?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3 border-t border-border/70 first:border-t-0 first:pt-0 last:pb-0">
      <div>
        <Label className="text-sm font-medium">{label}</Label>
        <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
      </div>
      <Switch defaultChecked={defaultChecked} />
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Configure your detection pipeline and interface preferences.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SettingsCard title="Camera" description="Choose the device used for live detection.">
          <Select defaultValue="default">
            <SelectTrigger className="rounded-xl h-10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="default">Default camera</SelectItem>
              <SelectItem value="external">External webcam</SelectItem>
            </SelectContent>
          </Select>
        </SettingsCard>

        <SettingsCard title="Theme" description="Interface color mode.">
          <Select defaultValue="light">
            <SelectTrigger className="rounded-xl h-10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="light">Light</SelectItem>
              <SelectItem value="dark">Dark</SelectItem>
              <SelectItem value="system">System</SelectItem>
            </SelectContent>
          </Select>
        </SettingsCard>

        <SettingsCard
          title="Confidence Threshold"
          description="Only surface detections above this confidence."
        >
          <div className="pt-2">
            <Slider defaultValue={[60]} max={100} step={1} />
            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>
        </SettingsCard>

        <SettingsCard title="Preferences" description="Fine-tune detection behavior.">
          <ToggleRow
            label="Notifications"
            description="Alert on new detections"
            defaultChecked
          />
          <ToggleRow
            label="Bounding boxes"
            description="Draw boxes around detected faces"
            defaultChecked
          />
          <ToggleRow label="Animations" description="Enable UI motion" defaultChecked />
        </SettingsCard>
      </div>

      <div className="mt-8 flex justify-end">
        <Button className="rounded-xl h-11 px-6">Save changes</Button>
      </div>
    </div>
  );
}
