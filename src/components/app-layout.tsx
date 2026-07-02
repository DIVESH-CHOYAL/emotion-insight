import type { ReactNode } from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { TopNav } from "@/components/top-nav";
import { AppModalsProvider, useAppModals } from "@/components/app-modals-context";
import { LiveDetectionModal } from "@/components/modals/live-detection-modal";
import { UploadImageModal } from "@/components/modals/upload-image-modal";

function Modals() {
  const { modal, close } = useAppModals();
  return (
    <>
      <LiveDetectionModal open={modal === "live"} onOpenChange={(o) => !o && close()} />
      <UploadImageModal open={modal === "upload"} onOpenChange={(o) => !o && close()} />
    </>
  );
}

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AppModalsProvider>
      <SidebarProvider>
        <div className="min-h-screen flex w-full bg-background">
          <AppSidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <header className="sticky top-0 z-30 h-16 flex items-center gap-3 border-b border-border/70 bg-background/80 backdrop-blur-md px-4 md:px-6">
              <SidebarTrigger className="rounded-xl" />
              <TopNav />
            </header>
            <main className="flex-1 px-4 md:px-8 py-8 md:py-10 animate-fade-in">
              {children}
            </main>
          </div>
        </div>
        <Modals />
      </SidebarProvider>
    </AppModalsProvider>
  );
}
