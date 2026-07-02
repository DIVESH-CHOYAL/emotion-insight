import { createContext, useContext, useState, type ReactNode } from "react";

type ModalKind = "live" | "upload" | null;

type Ctx = {
  modal: ModalKind;
  openLive: () => void;
  openUpload: () => void;
  close: () => void;
};

const ModalCtx = createContext<Ctx | null>(null);

export function AppModalsProvider({ children }: { children: ReactNode }) {
  const [modal, setModal] = useState<ModalKind>(null);
  return (
    <ModalCtx.Provider
      value={{
        modal,
        openLive: () => setModal("live"),
        openUpload: () => setModal("upload"),
        close: () => setModal(null),
      }}
    >
      {children}
    </ModalCtx.Provider>
  );
}

export function useAppModals() {
  const c = useContext(ModalCtx);
  if (!c) throw new Error("useAppModals must be inside AppModalsProvider");
  return c;
}
