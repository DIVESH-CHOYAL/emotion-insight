import { createFileRoute } from "@tanstack/react-router";
import { Video, ImageUp, ArrowRight, Cpu, Database, Gauge, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppModals } from "@/components/app-modals-context";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — EmotionSense AI" },
      {
        name: "description",
        content:
          "Start live facial emotion detection or upload an image to analyze emotions with EmotionSense AI.",
      },
      { property: "og:title", content: "Dashboard — EmotionSense AI" },
      {
        property: "og:description",
        content: "Real-time facial emotion detection dashboard.",
      },
    ],
  }),
  component: Dashboard,
});

function ActionCard({
  icon: Icon,
  title,
  description,
  cta,
  onClick,
}: {
  icon: typeof Video;
  title: string;
  description: string;
  cta: string;
  onClick: () => void;
}) {
  return (
    <div className="group relative rounded-3xl border border-border/70 bg-card p-8 shadow-soft transition-all duration-300 hover:-translate-y-1 hover:shadow-elevated">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-primary">
        <Icon className="h-6 w-6" strokeWidth={2} />
      </div>
      <h3 className="mt-6 text-xl font-semibold tracking-tight">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground max-w-sm">
        {description}
      </p>
      <Button
        onClick={onClick}
        size="lg"
        className="mt-8 rounded-xl h-11 px-5 text-sm font-medium"
      >
        {cta}
        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
      </Button>
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Cpu;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-border/70 bg-card p-5 transition-shadow hover:shadow-soft">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span className="text-xs uppercase tracking-wide">{label}</span>
      </div>
      <div className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{value}</div>
    </div>
  );
}

function Dashboard() {
  const { openLive, openUpload } = useAppModals();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-10">
        <h1 className="text-3xl font-semibold tracking-tight">Welcome back</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Analyze facial emotions in real time or from uploaded images.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ActionCard
          icon={Video}
          title="Live Detection"
          description="Start real-time facial emotion detection using your webcam. See emotions detected instantly with confidence scores."
          cta="Start Live Detection"
          onClick={openLive}
        />
        <ActionCard
          icon={ImageUp}
          title="Upload Image"
          description="Upload an image and analyze facial emotions with detailed probability breakdowns for every class."
          cta="Upload Image"
          onClick={openUpload}
        />
      </div>

      <div className="mt-12">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Model Overview
        </h2>
        <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Stat icon={Cpu} label="Current Model" value="CNN" />
          <Stat icon={Database} label="Dataset" value="FER2013" />
          <Stat icon={Gauge} label="Avg Accuracy" value="66%" />
          <Stat icon={Activity} label="Total Scans" value="0" />
        </div>
      </div>
    </div>
  );
}
