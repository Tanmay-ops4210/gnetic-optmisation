/**
 * Centralized API configuration.
 * Local development: http://127.0.0.1:8000
 * Production Vercel: https://gnetic-optmisation-fsak.vercel.app
 */
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || "https://gnetic-optmisation-fsak.vercel.app";

// Strip trailing slash if present to avoid duplicate slashes in request paths
const API_BASE_URL = (typeof rawBaseUrl === "string" ? rawBaseUrl : "").replace(/\/+$/, "");

export default API_BASE_URL;
