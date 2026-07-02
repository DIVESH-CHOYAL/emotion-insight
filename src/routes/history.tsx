import { createFileRoute } from "@tanstack/react-router";
import { Search, Filter, Download } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "History — EmotionSense AI" },
      {
        name: "description",
        content: "Review past emotion detection sessions and image analyses.",
      },
      { property: "og:title", content: "History — EmotionSense AI" },
      { property: "og:description", content: "Scan history and past analyses." },
    ],
  }),
  component: HistoryPage,
});

function HistoryPage() {
  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">History</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Every detection session and uploaded analysis, in one place.
          </p>
        </div>
      </div>

      <div className="rounded-3xl border border-border/70 bg-card shadow-soft overflow-hidden">
        <div className="flex flex-wrap items-center gap-3 border-b border-border/70 p-4">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search scans"
              className="h-10 rounded-xl border-border/70 bg-secondary/50 pl-9 shadow-none"
            />
          </div>
          <Button variant="outline" className="rounded-xl h-10">
            <Filter className="h-4 w-4" /> Filter
          </Button>
          <Button variant="outline" className="rounded-xl h-10">
            <Download className="h-4 w-4" /> Export
          </Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Date</TableHead>
              <TableHead>Method</TableHead>
              <TableHead>Emotion</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell colSpan={5} className="h-40 text-center text-sm text-muted-foreground">
                No history yet. Start a live session or upload an image to see results here.
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
