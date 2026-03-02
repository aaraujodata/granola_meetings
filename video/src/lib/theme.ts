export const colors = {
  // Backgrounds
  pageBg: "#f9fafb", // gray-50
  cardBg: "#ffffff", // white
  terminalBg: "#111827", // gray-900

  // Text
  textPrimary: "#111827", // gray-900
  textSecondary: "#6b7280", // gray-500
  textTertiary: "#9ca3af", // gray-400

  // Borders
  border: "#e5e7eb", // gray-200
  borderHover: "#93c5fd", // blue-300

  // Accent / Primary
  primary: "#2563eb", // blue-600
  primaryDark: "#1d4ed8", // blue-700
  primaryLight: "#dbeafe", // blue-100
  primaryText: "#1e40af", // blue-800

  // Status
  successBg: "#dcfce7", // green-100
  successText: "#166534", // green-800
  warningBg: "#fef9c3", // yellow-100
  warningText: "#854d0e", // yellow-800
  errorBg: "#fef2f2", // red-50
  errorText: "#b91c1c", // red-700

  // Terminal log levels
  logInfo: "#4ade80", // green-400
  logWarn: "#facc15", // yellow-400
  logError: "#f87171", // red-400

  // Search highlights
  highlight: "#fef08a", // yellow-200

  // Badges
  badgeActiveBg: "#dbeafe", // blue-100
  badgeActiveText: "#1d4ed8", // blue-700
  badgeInactiveBg: "#f3f4f6", // gray-100
  badgeInactiveText: "#9ca3af", // gray-400
} as const;

export const fonts = {
  sans: "Inter",
  mono: "JetBrains Mono",
} as const;
