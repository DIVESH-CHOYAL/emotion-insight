/**
 * EmotionSense AI — Backend API configuration
 * 
 * Set VITE_BACKEND_URL in your .env or environment to override.
 * Defaults to http://127.0.0.1:8000 for local development.
 */
export const BACKEND_URL =
  (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_BACKEND_URL) ||
  "http://127.0.0.1:8000";
