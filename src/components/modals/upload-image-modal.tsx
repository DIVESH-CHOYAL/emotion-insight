import { useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { UploadCloud, ImageIcon, ScanFace, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { BACKEND_URL } from "@/lib/backend";

type Props = { open: boolean; onOpenChange: (v: boolean) => void };

export function UploadImageModal({ open, onOpenChange }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [croppedFaceUrl, setCroppedFaceUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Results states
  const [faceDetected, setFaceDetected] = useState<boolean | null>(null);
  const [emotion, setEmotion] = useState<string>("—");
  const [confidence, setConfidence] = useState<number | null>(null);
  const [probabilities, setProbabilities] = useState<Record<string, number>>({});

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (file: File) => {
    if (!file.type.startsWith("image/")) {
      toast.error("Please upload an image file (PNG, JPG, WEBP).");
      return;
    }
    
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    
    // Reset previous prediction states
    setCroppedFaceUrl(null);
    setFaceDetected(null);
    setEmotion("—");
    setConfidence(null);
    setProbabilities({});
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const cropDetectedFace = (file: File, bbox: [number, number, number, number]) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const [x, y, w, h] = bbox;
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.drawImage(img, x, y, w, h, 0, 0, w, h);
          setCroppedFaceUrl(canvas.toDataURL("image/jpeg"));
        }
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  const analyzeImage = async () => {
    if (!selectedFile) {
      toast.warning("Please upload an image first.");
      return;
    }

    setIsAnalyzing(true);
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${BACKEND_URL}/predict-image`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Server error occurred during analysis.");
      }

      const data = await res.json();
      setFaceDetected(data.face_detected);

      if (data.face_detected) {
        setEmotion(data.emotion);
        setConfidence(data.confidence);
        setProbabilities(data.probabilities || {});
        cropDetectedFace(selectedFile, data.bounding_box);
        toast.success("Facial analysis complete!");
      } else {
        toast.warning("No face detected in the image.");
      }
    } catch (err: any) {
      console.error("Image analysis error:", err);
      toast.error(err.message || "Failed to analyze image. Ensure the backend is running.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setCroppedFaceUrl(null);
    setFaceDetected(null);
    setEmotion("—");
    setConfidence(null);
    setProbabilities({});
    onOpenChange(false);
  };

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
          {/* Left Column: Dropzone/Preview */}
          <div 
            className="flex flex-col rounded-2xl border-2 border-dashed border-border bg-secondary/40 p-8 items-center justify-center text-center min-h-[280px] relative overflow-hidden"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
          >
            {previewUrl ? (
              <div className="absolute inset-0 flex items-center justify-center bg-black/10">
                <img 
                  src={previewUrl} 
                  className="h-full w-full object-contain" 
                  alt="Uploaded Preview" 
                />
                <Button 
                  variant="secondary" 
                  size="sm" 
                  className="absolute bottom-4 right-4 rounded-xl shadow-soft"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Change Image
                </Button>
              </div>
            ) : (
              <>
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-background shadow-soft">
                  <UploadCloud className="h-6 w-6 text-primary" />
                </div>
                <div className="mt-4 text-sm font-medium">Drag & drop an image</div>
                <div className="mt-1 text-xs text-muted-foreground">PNG, JPG up to 10MB</div>
                <Button 
                  variant="outline" 
                  className="mt-5 rounded-xl"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Browse Files
                </Button>
              </>
            )}
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept="image/*"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileChange(e.target.files[0]);
                }
              }}
            />
          </div>

          {/* Right Column: Prediction Metrics */}
          <div className="space-y-3">
            <div className="rounded-2xl border border-border/70 bg-card p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">
                Detected Face
              </div>
              <div className="mt-3 aspect-square w-full max-h-[160px] rounded-xl bg-secondary/60 flex items-center justify-center overflow-hidden">
                {croppedFaceUrl ? (
                  <img 
                    src={croppedFaceUrl} 
                    className="h-full w-full object-cover" 
                    alt="Cropped detected face" 
                  />
                ) : (
                  <div className="text-center">
                    <ScanFace className="mx-auto h-8 w-8 text-muted-foreground/60" />
                    <p className="mt-2 text-xs text-muted-foreground">
                      {faceDetected === false ? "No face detected" : "Awaiting analysis"}
                    </p>
                  </div>
                )}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-border/70 bg-card p-4">
                <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Emotion
                </div>
                <div className="mt-1 text-lg font-semibold">{emotion}</div>
              </div>
              <div className="rounded-2xl border border-border/70 bg-card p-4">
                <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Confidence
                </div>
                <div className="mt-1 text-lg font-semibold">
                  {confidence !== null ? `${Math.round(confidence)}%` : "—"}
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-border/70 bg-card p-4">
              <div className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">
                Probability Chart
              </div>
              {Object.keys(probabilities).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(probabilities)
                    .sort((a, b) => b[1] - a[1]) // Show highest confidence first
                    .map(([emo, score]) => (
                      <div key={emo} className="flex items-center text-xs gap-2">
                        <span className="w-16 text-muted-foreground text-left">{emo}</span>
                        <div className="h-2 flex-1 rounded-full bg-secondary overflow-hidden">
                          <div 
                            className="h-full bg-primary rounded-full transition-all duration-500"
                            style={{ width: `${score}%` }}
                          />
                        </div>
                        <span className="w-8 text-right font-medium text-muted-foreground">
                          {Math.round(score)}%
                        </span>
                      </div>
                    ))}
                </div>
              ) : (
                <div className="h-24 rounded-xl bg-secondary/60 flex items-center justify-center text-xs text-muted-foreground">
                  Awaiting analysis (Standard Placeholder)
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-border/70 bg-secondary/40 px-6 py-4">
          <Button variant="outline" className="rounded-xl" onClick={handleClose}>
            Close
          </Button>
          <Button 
            className="rounded-xl flex items-center gap-2" 
            onClick={analyzeImage} 
            disabled={isAnalyzing || !selectedFile}
          >
            {isAnalyzing && <Loader2 className="h-4 w-4 animate-spin" />}
            Analyze
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
