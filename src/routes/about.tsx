import { createFileRoute } from "@tanstack/react-router";
import { Database, Layers, Eye, Cpu, Server, ArrowRight } from "lucide-react";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About — EmotionSense AI" },
      {
        name: "description",
        content:
          "Learn about the AI pipeline behind EmotionSense — FER2013, TensorFlow, OpenCV, CNN, and FastAPI.",
      },
      { property: "og:title", content: "About — EmotionSense AI" },
      { property: "og:description", content: "The AI pipeline behind EmotionSense." },
    ],
  }),
  component: AboutPage,
});

const sections = [
  {
    icon: Database,
    title: "FER2013 Dataset",
    body: "35,000+ grayscale facial expressions across 7 emotion classes, the gold standard for training facial emotion models.",
  },
  {
    icon: Layers,
    title: "TensorFlow",
    body: "The deep learning framework used to train and serve the CNN weights that power EmotionSense.",
  },
  {
    icon: Eye,
    title: "OpenCV",
    body: "Face detection and image preprocessing — cropping, aligning, and normalizing input before inference.",
  },
  {
    icon: Cpu,
    title: "CNN Architecture",
    body: "A compact convolutional neural network optimized for real-time inference on modest hardware.",
  },
  {
    icon: Server,
    title: "FastAPI Backend",
    body: "A high-performance Python API that serves predictions to the dashboard with low latency.",
  },
];

const pipeline = [
  { icon: Eye, label: "Detect Face" },
  { icon: Layers, label: "Preprocess" },
  { icon: Cpu, label: "CNN Inference" },
  { icon: Server, label: "Return Emotion" },
];

function AboutPage() {
  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-10">
        <h1 className="text-3xl font-semibold tracking-tight">About EmotionSense</h1>
        <p className="mt-2 text-sm text-muted-foreground max-w-2xl">
          A modern interface for a well-understood computer vision problem. Here's what powers
          it under the hood.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sections.map((s) => (
          <div
            key={s.title}
            className="rounded-2xl border border-border/70 bg-card p-6 shadow-soft transition-all hover:-translate-y-0.5 hover:shadow-elevated"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-secondary text-primary">
              <s.icon className="h-5 w-5" />
            </div>
            <h3 className="mt-4 text-base font-semibold">{s.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
          </div>
        ))}
      </div>

      <div className="mt-10 rounded-3xl border border-border/70 bg-card p-6 shadow-soft">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
          AI Pipeline
        </h2>
        <div className="mt-5 flex flex-wrap items-center gap-3">
          {pipeline.map((step, i) => (
            <div key={step.label} className="flex items-center gap-3">
              <div className="flex items-center gap-2.5 rounded-2xl border border-border/70 bg-background px-4 py-3">
                <step.icon className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">{step.label}</span>
              </div>
              {i < pipeline.length - 1 && (
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
