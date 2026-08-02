/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./**/*.html",
    "./**/*.py"
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "surface": "#faf8ff",
        "surface-dim": "#d9d9e2",
        "surface-bright": "#faf8ff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f3f3fc",
        "surface-container": "#ededf6",
        "surface-container-high": "#e7e7f1",
        "surface-container-highest": "#e1e2eb",
        "on-surface": "#191b22",
        "on-surface-variant": "#434653",
        "inverse-surface": "#2e3037",
        "inverse-on-surface": "#f0f0f9",
        "outline": "#737784",
        "outline-variant": "#c3c6d5",
        "surface-tint": "#1d59c1",
        "primary": "#003c90",
        "on-primary": "#ffffff",
        "primary-container": "#0f52ba",
        "on-primary-container": "#bcceff",
        "inverse-primary": "#b0c6ff",
        "secondary": "#505f76",
        "on-secondary": "#ffffff",
        "secondary-container": "#d0e1fb",
        "on-secondary-container": "#54647a",
        "tertiary": "#732900",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#993900",
        "on-tertiary-container": "#ffc0a7",
        "error": "#ba1a1a",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",
        "primary-fixed": "#d9e2ff",
        "primary-fixed-dim": "#b0c6ff",
        "on-primary-fixed": "#001945",
        "on-primary-fixed-variant": "#00419c",
        "secondary-fixed": "#d3e4fe",
        "secondary-fixed-dim": "#b7c8e1",
        "on-secondary-fixed": "#0b1c30",
        "on-secondary-fixed-variant": "#38485d",
        "tertiary-fixed": "#ffdbcd",
        "tertiary-fixed-dim": "#ffb596",
        "on-tertiary-fixed": "#360f00",
        "on-tertiary-fixed-variant": "#7d2d00",
        "background": "#faf8ff",
        "on-background": "#191b22",
        "surface-variant": "#e1e2eb"
      },
      borderRadius: {
        "sm": "0.25rem",
        "DEFAULT": "0.5rem",
        "md": "0.75rem",
        "lg": "1rem",
        "xl": "1.5rem",
        "full": "9999px"
      },
      spacing: {
        "base": "4px",
        "gutter": "24px",
        "margin-mobile": "16px",
        "margin-desktop": "40px",
        "row-height-md": "64px"
      },
      fontFamily: {
        "headline-lg": ["Inter", "sans-serif"],
        "headline-md": ["Inter", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "label-md": ["Inter", "sans-serif"],
        "data-tabular": ["Inter", "sans-serif"]
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries')
  ],
}
