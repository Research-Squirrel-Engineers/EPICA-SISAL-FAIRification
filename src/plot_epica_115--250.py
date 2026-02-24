# Datei: plot_all_epica.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter, FixedLocator

# Arbeitsverzeichnis auf Ordner des Skripts setzen
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Output-Ordner erstellen
OUTPUT_DIR = "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Gemeinsame Plot-Einstellungen
FIGURE_SIZE = (10, 30)
DPI = 100
AGE_MIN = 115000
AGE_MAX = 250000
LINE_COLOR = "black"
LINE_WIDTH = 1
GRID_COLOR = "#cccccc"
GRID_WIDTH = 1
MAJOR_TICK_INTERVAL = 10000
MINOR_TICK_INTERVAL = 2000
FONT_SIZE_LABEL = 30  # X- und Y-Achsen-Labels
FONT_SIZE_TICK = 26  # Tick-Beschriftungen
TITLE_FONTSIZE = 30  # Überschrift "EPICA"
LABEL_PAD = 12

# Konfiguration für alle Datensätze
datasets = [
    {
        "file": "EPICA_Dome_C_ch4.csv",
        "column": "ch4",
        "age_transform": lambda age: age * 1000 + 50,
        "xlabel": r"$\mathbf{CH}_{\mathbf{4}}\ \mathbf{[ppbv]}$",
        "output_prefix": "ch4",
        "x_padding": 0.05,  # 5% Puffer
        "x_ticks": [300, 600, 900],  # Manuelle Ticks
    },
    {
        "file": "EPICA_Dome_C_d18O.csv",
        "column": "d18o",
        "age_transform": lambda age: age * 1000 + 50,
        "xlabel": r"$\boldsymbol{\delta}^{\mathbf{18}}\mathbf{O}\ \mathbf{[‰]}$",
        "output_prefix": "d18o",
        "x_padding": 0.02,
        "x_ticks": [-0.5, 0, 0.5, 1.0, 1.5],
    },
    {
        "file": "EPICA_Dome_C_dd.csv",
        "column": "dd",
        "age_transform": lambda age: age,  # keine Transformation
        "xlabel": r"$\boldsymbol{\delta}\mathbf{D}\ \mathbf{[per\ mil]}$",
        "output_prefix": "dd",
        "x_padding": 0.02,
        "x_ticks": [-450, -400, -350],
    },
    {
        "file": "EPICA_Dome_C_do2n2.csv",
        "column": "do2n2",
        "age_transform": lambda age: age * 1000 + 50,
        "xlabel": r"$\mathbf{\boldsymbol{\delta}}(\mathbf{O}_{\mathbf{2}}/\mathbf{N}_{\mathbf{2}})\ \mathbf{[‰]}$",
        "output_prefix": "do2n2",
        "x_padding": 0.05,
        "x_ticks": [-20, -10, 0],
    },
    {
        "file": "EPICA_Dome_C_dust.csv",
        "column": "dust",
        "age_transform": lambda age: age * 1000 - 8,
        "xlabel": r"$\mathbf{Dust\ conc}\ \mathbf{[\mu g/kg]}$",
        "output_prefix": "dust",
        "x_padding": 0.05,
        "x_ticks": [0, 250, 500, 750, 1000],
    },
]


def load_and_process_data(filename, column_name, age_transform):
    """
    Lädt und verarbeitet eine CSV-Datei.

    Parameters:
    -----------
    filename : str
        Name der CSV-Datei
    column_name : str
        Name der Datenspalte (z.B. 'ch4', 'd18o')
    age_transform : callable
        Funktion zur Transformation der Age-Werte

    Returns:
    --------
    DataFrame mit Spalten ['Age', column_name]
    """
    df = pd.read_csv(filename, sep=";", engine="python", encoding="utf-8-sig")
    df.columns = df.columns.str.strip().str.lower()

    # Prüfen ob erforderliche Spalten vorhanden sind
    required_cols = {"depth", "age", column_name}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"Erwarte Spalten {required_cols} in {filename} — gefunden: {list(df.columns)}"
        )

    # Numerisch konvertieren
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[column_name] = pd.to_numeric(df[column_name], errors="coerce")
    df = df.dropna(subset=["age", column_name])

    # Age transformieren
    df["Age"] = age_transform(df["age"])

    # Nach Age sortieren
    df = df.sort_values("Age")

    return df[["Age", column_name]]


def create_plot(df, column_name, xlabel, output_prefix, x_padding=0.05, x_ticks=None):
    """
    Erstellt einen standardisierten Plot.

    Parameters:
    -----------
    df : DataFrame
        Daten mit Spalten ['Age', column_name]
    column_name : str
        Name der zu plottenden Spalte
    xlabel : str
        Label für die x-Achse (mit LaTeX-Formatierung)
    output_prefix : str
        Präfix für Output-Dateien
    x_padding : float
        Relativer Puffer für x-Achse (z.B. 0.05 = 5%)
    x_ticks : list, optional
        Manuelle X-Achsen-Ticks. Falls None, werden automatisch Ticks generiert.
    """
    fig = plt.figure(figsize=FIGURE_SIZE, dpi=DPI)
    ax = fig.add_subplot(111)

    # Plot
    ax.plot(df[column_name], df["Age"], linewidth=LINE_WIDTH, color=LINE_COLOR)

    # Y-Achse (Age)
    ax.set_ylim(AGE_MAX, AGE_MIN)
    ax.margins(y=0)

    # X-Achse oben platzieren
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")

    # X-Achse: automatisch mit Puffer, nur für Daten in der Age-Range
    df_filtered = df[(df["Age"] >= AGE_MIN) & (df["Age"] <= AGE_MAX)]
    xmin = df_filtered[column_name].min()
    xmax = df_filtered[column_name].max()
    x_range = xmax - xmin

    # X-Achsen-Ticks: manuell oder automatisch
    if x_ticks is not None:
        # Verwende manuelle Ticks
        ax.xaxis.set_major_locator(FixedLocator(x_ticks))
        # X-Limits basierend auf manuellen Ticks
        tick_min, tick_max = min(x_ticks), max(x_ticks)
        span = tick_max - tick_min
        pad = span * 0.05 if span > 0 else 0.5
        ax.set_xlim(tick_min - pad, tick_max + pad)
    else:
        # Automatische Limits mit Puffer
        ax.set_xlim(xmin - x_range * x_padding, xmax + x_range * x_padding)

    # X-Achsen-Format (1 Dezimalstelle)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.1f}"))

    # Y-Raster
    ax.yaxis.set_major_locator(MultipleLocator(MAJOR_TICK_INTERVAL))
    ax.yaxis.set_minor_locator(MultipleLocator(MINOR_TICK_INTERVAL))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x/1000)}"))
    ax.grid(axis="y", which="major", color=GRID_COLOR, linewidth=GRID_WIDTH)

    # Minor-Ticks
    ax.tick_params(axis="y", which="minor", length=4, width=0.8)

    # Achsenbeschriftungen
    ax.set_xlabel(xlabel, fontsize=FONT_SIZE_LABEL, labelpad=LABEL_PAD)
    ax.set_ylabel(
        "Age [kyr b2k]", fontsize=FONT_SIZE_LABEL, labelpad=LABEL_PAD, fontweight="bold"
    )

    # Überschrift "EPICA"
    ax.text(
        0.5,
        1.045,
        "EPICA",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=TITLE_FONTSIZE,
        fontweight="bold",
    )

    # Tick-Label-Größe
    ax.tick_params(axis="x", labelsize=FONT_SIZE_TICK)
    ax.tick_params(axis="y", labelsize=FONT_SIZE_TICK)

    # Export
    jpg_file = os.path.join(
        OUTPUT_DIR, f"{output_prefix}_vs_Age_Epica_{AGE_MIN}_{AGE_MAX}.jpg"
    )
    svg_file = os.path.join(
        OUTPUT_DIR, f"{output_prefix}_vs_Age_Epica_{AGE_MIN}_{AGE_MAX}.svg"
    )

    plt.savefig(jpg_file, bbox_inches="tight")
    plt.savefig(svg_file, bbox_inches="tight")
    plt.close()

    print(f"✓ Saved: {jpg_file} and {svg_file}")


def main():
    """Hauptfunktion: Verarbeitet alle Datensätze."""
    print("=" * 60)
    print("EPICA Dome C - Plot Generator")
    print("=" * 60)

    for i, config in enumerate(datasets, 1):
        print(f"\n[{i}/{len(datasets)}] Processing {config['file']}...")

        try:
            # Daten laden und verarbeiten
            df = load_and_process_data(
                config["file"], config["column"], config["age_transform"]
            )

            print(f"    Loaded {len(df)} data points")
            print(
                f"    Age range: {df['Age'].min():.0f} - {df['Age'].max():.0f} yr b2k"
            )
            print(
                f"    Data range (full): {df[config['column']].min():.2f} - {df[config['column']].max():.2f}"
            )

            # Gefilterte Daten für die Plot-Range
            df_filtered = df[(df["Age"] >= AGE_MIN) & (df["Age"] <= AGE_MAX)]
            if not df_filtered.empty:
                print(
                    f"    Data range ({AGE_MIN}-{AGE_MAX}): {df_filtered[config['column']].min():.2f} - {df_filtered[config['column']].max():.2f}"
                )

            # Plot erstellen
            create_plot(
                df,
                config["column"],
                config["xlabel"],
                config["output_prefix"],
                config["x_padding"],
                config.get("x_ticks", None),  # Manuelle Ticks (optional)
            )

        except Exception as e:
            print(f"    ERROR: {e}")
            continue

    print("\n" + "=" * 60)
    print("All plots generated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
