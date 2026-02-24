# Datei: plot_epica_from_tab.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter, FixedLocator

# Arbeitsverzeichnis auf Ordner des Skripts setzen
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Output-Ordner erstellen
OUTPUT_DIR = "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# Gemeinsame Plot-Einstellungen
# ──────────────────────────────────────────────
FIGURE_SIZE = (10, 30)
DPI = 100
LINE_COLOR = "black"
LINE_WIDTH = 1
GRID_COLOR = "#cccccc"
GRID_WIDTH = 1

# Y-Achsen-Ticks (Tiefe in m)
DEPTH_MAJOR_TICK_INTERVAL = 500   # alle 500 m ein dicker Tick
DEPTH_MINOR_TICK_INTERVAL = 100   # alle 100 m ein kleiner Tick

# Y-Achsen-Ticks (Age in ka BP)
AGE_MAJOR_TICK_INTERVAL = 100     # alle 100 ka ein dicker Tick
AGE_MINOR_TICK_INTERVAL = 20      # alle 20 ka ein kleiner Tick

FONT_SIZE_LABEL = 30
FONT_SIZE_TICK  = 26
TITLE_FONTSIZE  = 30
LABEL_PAD       = 12


# ──────────────────────────────────────────────
# TAB-Dateien einlesen
# ──────────────────────────────────────────────

def skip_header_lines(filepath):
    """Gibt die Anzahl der Kommentar-/Headerzeilen zurück (alles vor der Daten-Headerzeile)."""
    with open(filepath, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.startswith("/*") or line.startswith(" ") or line.strip() == "":
                continue
            # Erste echte Headerzeile (Spaltenname-Zeile) → danach kommen Daten
            return i
    return 0


def load_ch4_tab(filepath):
    """
    Liest EDC_CH4.tab ein.
    Spalten (Tab-getrennt):
        0: Depth ice/snow [m]
        1: Depth ref [m]
        2: Gas age [ka BP]  (EDC1 timescale)
        3: Gas age [ka BP]  (EDC2 timescale)  ← wir nehmen EDC2 (konsistent mit altem CSV)
        4: CH4 [ppbv]
        5: CH4 std dev [±]
    """
    # Alle Zeilen nach dem /* ... */ Block überspringen
    rows = []
    header_passed = False
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            if line.startswith("*/"):
                header_passed = True
                continue
            if not header_passed:
                continue
            stripped = line.strip()
            if stripped == "":
                continue
            # Erste Zeile nach Block = Spaltenüberschriften → überspringen
            if stripped.startswith("Depth ice/snow"):
                continue
            rows.append(stripped.split("\t"))

    df = pd.DataFrame(rows)
    df.columns = ["depth_m", "depth_ref", "age_edc1_ka", "age_edc2_ka", "ch4", "ch4_std"]

    df["depth_m"]      = pd.to_numeric(df["depth_m"],      errors="coerce")
    df["age_edc2_ka"]  = pd.to_numeric(df["age_edc2_ka"],  errors="coerce")
    df["ch4"]          = pd.to_numeric(df["ch4"],           errors="coerce")

    df = df.dropna(subset=["depth_m", "ch4"])
    df = df.sort_values("depth_m").reset_index(drop=True)

    print(f"  CH4 geladen: {len(df)} Datenpunkte")
    print(f"  Tiefe: {df['depth_m'].min():.1f} – {df['depth_m'].max():.1f} m")
    print(f"  Age (EDC2, ka BP): {df['age_edc2_ka'].min():.1f} – {df['age_edc2_ka'].max():.1f}")
    print(f"  CH4: {df['ch4'].min():.1f} – {df['ch4'].max():.1f} ppbv")

    return df[["depth_m", "age_edc2_ka", "ch4"]]


def load_d18o_tab(filepath):
    """
    Liest EPICA_Dome_C_d18O.tab ein.
    Spalten (Tab-getrennt):
        0: Depth ice/snow [m]
        1: Gas age [ka BP]
        2: δ18O-O2 [‰]
    """
    rows = []
    header_passed = False
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            if line.startswith("*/"):
                header_passed = True
                continue
            if not header_passed:
                continue
            stripped = line.strip()
            if stripped == "":
                continue
            if stripped.startswith("Depth ice/snow"):
                continue
            rows.append(stripped.split("\t"))

    df = pd.DataFrame(rows)
    df.columns = ["depth_m", "age_ka", "d18o"]

    df["depth_m"] = pd.to_numeric(df["depth_m"], errors="coerce")
    df["age_ka"]  = pd.to_numeric(df["age_ka"],  errors="coerce")
    df["d18o"]    = pd.to_numeric(df["d18o"],     errors="coerce")

    df = df.dropna(subset=["depth_m", "d18o"])
    df = df.sort_values("depth_m").reset_index(drop=True)

    print(f"  d18O geladen: {len(df)} Datenpunkte")
    print(f"  Tiefe: {df['depth_m'].min():.1f} – {df['depth_m'].max():.1f} m")
    print(f"  Age (ka BP): {df['age_ka'].min():.1f} – {df['age_ka'].max():.1f}")
    print(f"  d18O: {df['d18o'].min():.4f} – {df['d18o'].max():.4f} ‰")

    return df[["depth_m", "age_ka", "d18o"]]


# ──────────────────────────────────────────────
# Plot-Funktion (generisch für beide Achsentypen)
# ──────────────────────────────────────────────

def create_plot(
    x_values,
    y_values,
    xlabel,
    ylabel,
    title_text,
    output_filename,
    y_major_interval,
    y_minor_interval,
    x_ticks=None,
    x_padding=0.05,
    invert_y=True,
):
    """
    Erstellt einen standardisierten EPICA-Plot.

    x_values      : pd.Series  – die auf der X-Achse dargestellte Messgröße
    y_values      : pd.Series  – die auf der Y-Achse dargestellte Tiefe/Zeit
    xlabel        : str        – X-Achsen-Label (LaTeX ok)
    ylabel        : str        – Y-Achsen-Label
    title_text    : str        – Titel über dem Plot
    output_filename: str       – vollständiger Pfad ohne Extension
    y_major_interval: float   – Haupttick-Abstand Y
    y_minor_interval: float   – Nebentick-Abstand Y
    x_ticks       : list|None – manuelle X-Ticks
    x_padding     : float     – relativer X-Puffer (falls keine manuellen Ticks)
    invert_y      : bool       – Y-Achse invertieren (Tiefe nimmt nach unten zu)
    """
    fig = plt.figure(figsize=FIGURE_SIZE, dpi=DPI)
    ax  = fig.add_subplot(111)

    ax.plot(x_values, y_values, linewidth=LINE_WIDTH, color=LINE_COLOR)

    # Y-Achse
    y_min, y_max = y_values.min(), y_values.max()
    if invert_y:
        ax.set_ylim(y_max, y_min)   # oben = klein (junges Eis), unten = groß (altes Eis)
    else:
        ax.set_ylim(y_min, y_max)
    ax.margins(y=0)

    ax.yaxis.set_major_locator(MultipleLocator(y_major_interval))
    ax.yaxis.set_minor_locator(MultipleLocator(y_minor_interval))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda val, pos: f"{int(val)}"))
    ax.grid(axis="y", which="major", color=GRID_COLOR, linewidth=GRID_WIDTH)
    ax.tick_params(axis="y", which="minor", length=4, width=0.8)

    # X-Achse oben
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")

    # X-Achsen-Grenzen
    x_min, x_max = x_values.min(), x_values.max()
    x_range = x_max - x_min

    if x_ticks is not None:
        ax.xaxis.set_major_locator(FixedLocator(x_ticks))
        t_min, t_max = min(x_ticks), max(x_ticks)
        span = t_max - t_min
        pad  = span * 0.05 if span > 0 else 0.5
        ax.set_xlim(t_min - pad, t_max + pad)
    else:
        ax.set_xlim(x_min - x_range * x_padding,
                    x_max + x_range * x_padding)

    ax.xaxis.set_major_formatter(FuncFormatter(lambda val, pos: f"{val:.1f}"))

    # Beschriftungen
    ax.set_xlabel(xlabel, fontsize=FONT_SIZE_LABEL, labelpad=LABEL_PAD)
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE_LABEL, labelpad=LABEL_PAD, fontweight="bold")

    # Titel
    ax.text(
        0.5, 1.045, title_text,
        transform=ax.transAxes,
        ha="center", va="bottom",
        fontsize=TITLE_FONTSIZE, fontweight="bold",
    )

    ax.tick_params(axis="x", labelsize=FONT_SIZE_TICK)
    ax.tick_params(axis="y", labelsize=FONT_SIZE_TICK)

    # Speichern
    jpg_path = output_filename + ".jpg"
    svg_path = output_filename + ".svg"
    plt.savefig(jpg_path, bbox_inches="tight")
    plt.savefig(svg_path, bbox_inches="tight")
    plt.close()

    print(f"  ✓ Gespeichert: {jpg_path}")
    print(f"  ✓ Gespeichert: {svg_path}")


# ──────────────────────────────────────────────
# Hauptprogramm
# ──────────────────────────────────────────────

def main():
    print("=" * 60)
    print("EPICA Dome C – Plot Generator (TAB-Dateien, komplett)")
    print("=" * 60)

    # ── Daten laden ──────────────────────────────
    print("\n[1/2] Lade CH4 Tab-Datei …")
    df_ch4 = load_ch4_tab("EDC_CH4.tab")

    print("\n[2/2] Lade d18O Tab-Datei …")
    df_d18o = load_d18o_tab("EPICA_Dome_C_d18O.tab")

    # ── Plot-Konfigurationen ──────────────────────
    # X-Ticks für CH4 (ppbv) und d18O (‰)
    CH4_TICKS  = [300, 400, 500, 600, 700, 800, 900]
    D18O_TICKS = [-0.5, 0.0, 0.5, 1.0]

    plots = [
        # ── Nach Tiefe (m) ──────────────────────────
        {
            "x"          : df_ch4["ch4"],
            "y"          : df_ch4["depth_m"],
            "xlabel"     : r"$\mathbf{CH}_{\mathbf{4}}\ \mathbf{[ppbv]}$",
            "ylabel"     : "Depth [m]",
            "title"      : "EPICA – CH₄",
            "filename"   : os.path.join(OUTPUT_DIR, "ch4_vs_depth_full"),
            "y_major"    : DEPTH_MAJOR_TICK_INTERVAL,
            "y_minor"    : DEPTH_MINOR_TICK_INTERVAL,
            "x_ticks"    : CH4_TICKS,
        },
        {
            "x"          : df_d18o["d18o"],
            "y"          : df_d18o["depth_m"],
            "xlabel"     : r"$\boldsymbol{\delta}^{\mathbf{18}}\mathbf{O}\ \mathbf{[‰]}$",
            "ylabel"     : "Depth [m]",
            "title"      : "EPICA – δ¹⁸O",
            "filename"   : os.path.join(OUTPUT_DIR, "d18o_vs_depth_full"),
            "y_major"    : DEPTH_MAJOR_TICK_INTERVAL,
            "y_minor"    : DEPTH_MINOR_TICK_INTERVAL,
            "x_ticks"    : D18O_TICKS,
        },
        # ── Nach Age (ka BP) ─────────────────────────
        {
            "x"          : df_ch4["ch4"],
            "y"          : df_ch4["age_edc2_ka"],
            "xlabel"     : r"$\mathbf{CH}_{\mathbf{4}}\ \mathbf{[ppbv]}$",
            "ylabel"     : "Age [ka BP]",
            "title"      : "EPICA – CH₄",
            "filename"   : os.path.join(OUTPUT_DIR, "ch4_vs_age_ka_full"),
            "y_major"    : AGE_MAJOR_TICK_INTERVAL,
            "y_minor"    : AGE_MINOR_TICK_INTERVAL,
            "x_ticks"    : CH4_TICKS,
        },
        {
            "x"          : df_d18o["d18o"],
            "y"          : df_d18o["age_ka"],
            "xlabel"     : r"$\boldsymbol{\delta}^{\mathbf{18}}\mathbf{O}\ \mathbf{[‰]}$",
            "ylabel"     : "Age [ka BP]",
            "title"      : "EPICA – δ¹⁸O",
            "filename"   : os.path.join(OUTPUT_DIR, "d18o_vs_age_ka_full"),
            "y_major"    : AGE_MAJOR_TICK_INTERVAL,
            "y_minor"    : AGE_MINOR_TICK_INTERVAL,
            "x_ticks"    : D18O_TICKS,
        },
    ]

    print("\n" + "─" * 60)
    print("Erstelle Plots …")
    print("─" * 60)

    for i, cfg in enumerate(plots, 1):
        print(f"\n[{i}/{len(plots)}] {cfg['title']} – Y: {cfg['ylabel']}")
        # Nur Zeilen mit gültigen Y-Werten (age kann NaN sein für einzelne Punkte)
        mask = cfg["y"].notna() & cfg["x"].notna()
        create_plot(
            x_values         = cfg["x"][mask],
            y_values         = cfg["y"][mask],
            xlabel           = cfg["xlabel"],
            ylabel           = cfg["ylabel"],
            title_text       = cfg["title"],
            output_filename  = cfg["filename"],
            y_major_interval = cfg["y_major"],
            y_minor_interval = cfg["y_minor"],
            x_ticks          = cfg.get("x_ticks"),
        )

    print("\n" + "=" * 60)
    print(f"Fertig! Alle {len(plots)} Plots wurden in '{OUTPUT_DIR}/' gespeichert.")
    print("=" * 60)


if __name__ == "__main__":
    main()
