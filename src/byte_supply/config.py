"""Project-wide paths, palette and constants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "byte_supply_transactions.csv"
FIGURES_DIR = ROOT / "assets" / "figures"
REPORTS_DIR = ROOT / "reports"
DOCS_DIR = ROOT / "docs"

# Categorical palette — fixed order, colour-vision-deficiency validated.
PALETTE = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#6250d6",  # violet
    "#e34948",  # red
]
PRIMARY = PALETTE[0]
ACCENT = PALETTE[1]
MUTED = "#8a8984"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e6e5e0"
SURFACE = "#fcfcfb"

# Single-hue sequential ramp (light -> dark) for heatmaps.
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

MEGA_SALE_DAYS = ["09-09", "10-10", "11-11", "12-12"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
