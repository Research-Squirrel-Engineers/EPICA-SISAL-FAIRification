#!/usr/bin/env python3
"""
main.py — Orchestrator for EPICA + SISAL Palaeoclimate Data Processing

Executes the complete pipeline:
  1. EPICA Dome C (ice core) — Plots + RDF/TTL
  2. SISAL (speleothems) — Plots + RDF/TTL
  3. Combined FeatureCollection for all sites
  4. Mermaid diagrams

Usage:
    python main.py                      # everything
    python main.py --epica-only         # EPICA only
    python main.py --sisal-only         # SISAL only
    python main.py --no-plots           # RDF only, no plots
    python main.py --no-rdf             # plots only, no RDF
"""

__author__ = "Florian Thiery"
__version__ = "1.0.0"

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════════

# Paths relative to main.py (located in project root)
SCRIPT_DIR = Path(__file__).parent.absolute()

# Scripts are in subdirectories
EPICA_SCRIPT = SCRIPT_DIR / "EPICA" / "plot_epica_from_tab.py"
SISAL_SCRIPT = SCRIPT_DIR / "SISAL" / "plot_sisal_from_csv.py"

# Ontology utilities in ontology/ directory
ONTOLOGY_DIR = SCRIPT_DIR / "ontology"

# Output directories (already exist)
EPICA_OUTPUT_DIR = SCRIPT_DIR / "EPICA"
SISAL_OUTPUT_DIR = SCRIPT_DIR / "SISAL"

# Subdirectories
EPICA_PLOTS_DIR = EPICA_OUTPUT_DIR / "plots"
EPICA_RDF_DIR = EPICA_OUTPUT_DIR / "rdf"
EPICA_REPORT_DIR = EPICA_OUTPUT_DIR / "report"

SISAL_PLOTS_DIR = SISAL_OUTPUT_DIR / "plots"
SISAL_RDF_DIR = SISAL_OUTPUT_DIR / "rdf"
SISAL_REPORT_DIR = SISAL_OUTPUT_DIR / "report"


# ══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════════════


def print_header(text: str, char: str = "=", width: int = 80):
    """Prints a formatted header."""
    print()
    print(char * width)
    print(text.center(width))
    print(char * width)
    print()


def print_section(text: str):
    """Prints a section header."""
    print()
    print("─" * 80)
    print(f"  {text}")
    print("─" * 80)


def check_file_exists(filepath: Path, description: str) -> bool:
    """Checks if a file exists and prints warning."""
    if not filepath.exists():
        print(f"  ⚠  {description} not found: {filepath}")
        return False
    print(f"  ✓ {description} found: {filepath.name}")
    return True


def check_directory_exists(dirpath: Path, description: str) -> bool:
    """Checks if a directory exists."""
    if not dirpath.exists():
        print(f"  ⚠  {description} not found: {dirpath}")
        return False
    print(f"  ✓ {description} found: {dirpath.name}/")
    return True


def run_script(script_path: Path, description: str, skip: bool = False) -> bool:
    """Executes a Python script."""
    if skip:
        print(f"  ⊘ {description} skipped (--skip option)")
        return True

    if not script_path.exists():
        print(f"  ✗ {description} not found: {script_path}")
        return False

    print(f"\n  ▶ Starting {description} ...")
    print(f"    Path: {script_path}")

    # Execute script (imports and runs main())
    try:
        # Add script directory and ontology/ to Python path
        script_parent = str(script_path.parent)
        ontology_path = str(ONTOLOGY_DIR)

        if script_parent not in sys.path:
            sys.path.insert(0, script_parent)
        if ontology_path not in sys.path:
            sys.path.insert(0, ontology_path)

        # Import script as module
        import importlib.util

        spec = importlib.util.spec_from_file_location("script_module", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Call main() if available
        if hasattr(module, "main"):
            module.main()
        else:
            print(f"  ⚠  {script_path.name} has no main() function")
            return False

        print(f"  ✓ {description} completed successfully")
        return True

    except Exception as e:
        print(f"  ✗ Error in {description}:")
        print(f"    {type(e).__name__}: {e}")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            import traceback

            traceback.print_exc()
        return False


def print_summary(epica_success: bool, sisal_success: bool, start_time: datetime):
    """Prints a summary at the end."""
    duration = (datetime.now() - start_time).total_seconds()

    print_header("Summary", char="=")

    print("Status:")
    print(f"  EPICA: {'✓ Successful' if epica_success else '✗ Failed'}")
    print(f"  SISAL: {'✓ Successful' if sisal_success else '✗ Failed'}")
    print(f"\nTotal duration: {duration:.1f} seconds")

    print("\nGenerated files:")

    # EPICA files
    if EPICA_RDF_DIR.exists():
        ttl_files = list(EPICA_RDF_DIR.glob("*.ttl"))
        mermaid_files = list(EPICA_RDF_DIR.glob("*.mermaid"))
        if ttl_files:
            print(f"\n  EPICA RDF/TTL ({len(ttl_files)} files):")
            for f in sorted(ttl_files):
                size_kb = f.stat().st_size / 1024
                print(f"    • {f.name:<45} ({size_kb:>8.1f} KB)")
        if mermaid_files:
            print(f"\n  EPICA Mermaid ({len(mermaid_files)} files):")
            for f in sorted(mermaid_files):
                print(f"    • {f.name}")

    if EPICA_PLOTS_DIR.exists():
        plot_files = list(EPICA_PLOTS_DIR.glob("*.png"))
        if plot_files:
            print(f"\n  EPICA Plots ({len(plot_files)} files):")
            for f in sorted(plot_files)[:5]:
                size_kb = f.stat().st_size / 1024
                print(f"    • {f.name:<45} ({size_kb:>8.1f} KB)")
            if len(plot_files) > 5:
                print(f"    ... and {len(plot_files) - 5} more")

    # SISAL files
    if SISAL_RDF_DIR.exists():
        ttl_files = list(SISAL_RDF_DIR.glob("*.ttl"))
        mermaid_files = list(SISAL_RDF_DIR.glob("*.mermaid"))
        if ttl_files:
            print(f"\n  SISAL RDF/TTL ({len(ttl_files)} files):")
            for f in sorted(ttl_files):
                size_kb = f.stat().st_size / 1024
                print(f"    • {f.name:<45} ({size_kb:>8.1f} KB)")
        if mermaid_files:
            print(f"\n  SISAL Mermaid ({len(mermaid_files)} files):")
            for f in sorted(mermaid_files):
                print(f"    • {f.name}")

    if SISAL_PLOTS_DIR.exists():
        plot_files = list(SISAL_PLOTS_DIR.glob("*.png"))
        if plot_files:
            print(f"\n  SISAL Plots ({len(plot_files)} files):")
            for f in sorted(plot_files)[:5]:
                size_kb = f.stat().st_size / 1024
                print(f"    • {f.name:<45} ({size_kb:>8.1f} KB)")
            if len(plot_files) > 5:
                print(f"    ... and {len(plot_files) - 5} more")

    print()


# ══════════════════════════════════════════════════════════════════════════════
# Main Pipeline
# ══════════════════════════════════════════════════════════════════════════════


def main():
    """Main function — orchestrates EPICA + SISAL pipeline."""

    # ── Argument Parsing ──────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="EPICA + SISAL Palaeoclimate Data Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Execute everything
  python main.py --epica-only       # EPICA only
  python main.py --sisal-only       # SISAL only
  python main.py --no-plots         # Generate RDF only
  python main.py --no-rdf           # Generate plots only
        """,
    )
    parser.add_argument(
        "--epica-only", action="store_true", help="Execute EPICA only (skip SISAL)"
    )
    parser.add_argument(
        "--sisal-only", action="store_true", help="Execute SISAL only (skip EPICA)"
    )
    parser.add_argument(
        "--no-plots", action="store_true", help="Do not generate plots (RDF/TTL only)"
    )
    parser.add_argument(
        "--no-rdf", action="store_true", help="Do not generate RDF (plots only)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")

    args = parser.parse_args()

    # Record start time
    start_time = datetime.now()

    # ── Header ────────────────────────────────────────────────────────────────
    print_header("EPICA + SISAL Pipeline", char="═")
    print(f"  Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Directory: {SCRIPT_DIR}")
    print()

    # ── Check Directories ─────────────────────────────────────────────────────
    print_section("1. Preparation")
    print("\n  Directory structure:")

    epica_dir_ok = check_directory_exists(EPICA_OUTPUT_DIR, "EPICA directory")
    sisal_dir_ok = check_directory_exists(SISAL_OUTPUT_DIR, "SISAL directory")
    ontology_ok = check_directory_exists(ONTOLOGY_DIR, "Ontology directory")

    # ── Check Scripts ─────────────────────────────────────────────────────────
    print("\n  Scripts:")
    epica_exists = check_file_exists(EPICA_SCRIPT, "EPICA script")
    sisal_exists = check_file_exists(SISAL_SCRIPT, "SISAL script")

    if not epica_exists and not sisal_exists:
        print("\n  ✗ ERROR: No scripts found!")
        print("    Make sure scripts are in the correct locations:")
        print(f"    - {EPICA_SCRIPT}")
        print(f"    - {SISAL_SCRIPT}")
        sys.exit(1)

    # ── Execute EPICA ─────────────────────────────────────────────────────────
    epica_success = False
    if not args.sisal_only and epica_exists:
        print_section("2. EPICA Dome C (Ice Core)")
        epica_success = run_script(EPICA_SCRIPT, "EPICA Dome C Processing", skip=False)

    # ── Execute SISAL ─────────────────────────────────────────────────────────
    sisal_success = False
    if not args.epica_only and sisal_exists:
        print_section("3. SISAL (Speleothems)")
        sisal_success = run_script(SISAL_SCRIPT, "SISAL Processing", skip=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    print_summary(epica_success, sisal_success, start_time)

    # ── Exit Code ─────────────────────────────────────────────────────────────
    if (not args.epica_only and not epica_success) or (
        not args.sisal_only and not sisal_success
    ):
        print("⚠  Some steps failed — see errors above.")
        sys.exit(1)
    else:
        print("✓ Pipeline completed successfully!")
        sys.exit(0)


# ══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()


# ══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()


# ══════════════════════════════════════════════════════════════════════════════
# Helper-Funktionen
# ══════════════════════════════════════════════════════════════════════════════


def print_header(text: str, char: str = "=", width: int = 80):
    """Gibt einen formatierten Header aus."""
    print()
    print(char * width)
    print(text.center(width))
    print(char * width)
    print()


def print_section(text: str):
    """Gibt einen Abschnitts-Header aus."""
    print()
    print("─" * 80)
    print(f"  {text}")
    print("─" * 80)


def check_file_exists(filepath: Path, description: str) -> bool:
    """Prüft ob eine Datei existiert und gibt Warnung aus."""
    if not filepath.exists():
        print(f"  ⚠  {description} nicht gefunden: {filepath}")
        return False
    print(f"  ✓ {description} gefunden: {filepath}")
    return True


def run_script(script_path: Path, description: str, skip: bool = False) -> bool:
    """Führt ein Python-Script aus."""
    if skip:
        print(f"  ⊘ {description} übersprungen (--skip Option)")
        return True

    if not script_path.exists():
        print(f"  ✗ {description} nicht gefunden: {script_path}")
        return False

    print(f"\n  ▶ Starte {description} ...")
    print(f"    Pfad: {script_path}")

    # Script ausführen (importiert und führt main() aus)
    try:
        # Script-Verzeichnis zum Python-Path hinzufügen
        if str(script_path.parent) not in sys.path:
            sys.path.insert(0, str(script_path.parent))

        # Script als Modul importieren
        import importlib.util

        spec = importlib.util.spec_from_file_location("script_module", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # main() aufrufen falls vorhanden
        if hasattr(module, "main"):
            module.main()
        else:
            print(f"  ⚠  {script_path.name} hat keine main() Funktion")
            return False

        print(f"  ✓ {description} erfolgreich abgeschlossen")
        return True

    except Exception as e:
        print(f"  ✗ Fehler bei {description}:")
        print(f"    {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def print_summary(epica_success: bool, sisal_success: bool, start_time: datetime):
    """Gibt eine Zusammenfassung am Ende aus."""
    duration = (datetime.now() - start_time).total_seconds()

    print_header("Zusammenfassung", char="=")

    print("Status:")
    print(f"  EPICA: {'✓ Erfolgreich' if epica_success else '✗ Fehlgeschlagen'}")
    print(f"  SISAL: {'✓ Erfolgreich' if sisal_success else '✗ Fehlgeschlagen'}")
    print(f"\nGesamtdauer: {duration:.1f} Sekunden")

    print("\nGenerierte Dateien:")

    # TTL-Dateien zählen
    ttl_files = list(RDF_DIR.glob("*.ttl"))
    if ttl_files:
        print(f"\n  RDF/TTL ({len(ttl_files)} Dateien):")
        for f in sorted(ttl_files):
            size_kb = f.stat().st_size / 1024
            print(f"    • {f.name:<45} ({size_kb:>8.1f} KB)")

    # Plot-Dateien zählen
    plot_files = list(PLOTS_DIR.glob("*.png"))
    if plot_files:
        print(f"\n  Plots ({len(plot_files)} Dateien):")
        # Nur erste 10 zeigen wenn zu viele
        for f in sorted(plot_files)[:10]:
            size_kb = f.stat().st_size / 1024
            print(f"    • {f.name:<45} ({size_kb:>8.1f} KB)")
        if len(plot_files) > 10:
            print(f"    ... und {len(plot_files) - 10} weitere")

    # Mermaid-Dateien
    mermaid_files = list(RDF_DIR.glob("*.mermaid"))
    if mermaid_files:
        print(f"\n  Mermaid Diagramme ({len(mermaid_files)} Dateien):")
        for f in sorted(mermaid_files):
            print(f"    • {f.name}")

    print()


# ══════════════════════════════════════════════════════════════════════════════
# Haupt-Pipeline
# ══════════════════════════════════════════════════════════════════════════════


def main():
    """Haupt-Funktion — orchestriert EPICA + SISAL Pipeline."""

    # ── Argument Parsing ──────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="EPICA + SISAL Paläoklima-Datenverarbeitung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py                    # Alles ausführen
  python main.py --epica-only       # Nur EPICA
  python main.py --sisal-only       # Nur SISAL
  python main.py --no-plots         # Nur RDF generieren
  python main.py --no-rdf           # Nur Plots generieren
        """,
    )
    parser.add_argument(
        "--epica-only",
        action="store_true",
        help="Nur EPICA ausführen (SISAL überspringen)",
    )
    parser.add_argument(
        "--sisal-only",
        action="store_true",
        help="Nur SISAL ausführen (EPICA überspringen)",
    )
    parser.add_argument(
        "--no-plots", action="store_true", help="Keine Plots generieren (nur RDF/TTL)"
    )
    parser.add_argument(
        "--no-rdf", action="store_true", help="Kein RDF generieren (nur Plots)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Detaillierte Ausgabe"
    )

    args = parser.parse_args()

    # Start-Zeit merken
    start_time = datetime.now()

    # ── Header ────────────────────────────────────────────────────────────────
    print_header("EPICA + SISAL Pipeline", char="═")
    print(f"  Zeitpunkt: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Verzeichnis: {SCRIPT_DIR}")
    print()

    # ── Verzeichnisse erstellen ───────────────────────────────────────────────
    print_section("1. Vorbereitung")
    create_output_dirs()

    # ── Scripts prüfen ────────────────────────────────────────────────────────
    print("\n  Scripts:")
    epica_exists = check_file_exists(EPICA_SCRIPT, "EPICA Script")
    sisal_exists = check_file_exists(SISAL_SCRIPT, "SISAL Script")

    if not epica_exists and not sisal_exists:
        print("\n  ✗ FEHLER: Keine Scripts gefunden!")
        print(
            "    Stelle sicher dass plot_epica_from_tab.py und plot_sisal_from_csv.py"
        )
        print(f"    im gleichen Verzeichnis wie main.py liegen: {SCRIPT_DIR}")
        sys.exit(1)

    # ── EPICA ausführen ───────────────────────────────────────────────────────
    epica_success = False
    if not args.sisal_only and epica_exists:
        print_section("2. EPICA Dome C (Eisbohrkern)")
        epica_success = run_script(
            EPICA_SCRIPT, "EPICA Dome C Verarbeitung", skip=False
        )

    # ── SISAL ausführen ───────────────────────────────────────────────────────
    sisal_success = False
    if not args.epica_only and sisal_exists:
        print_section("3. SISAL (Speläotheme)")
        sisal_success = run_script(SISAL_SCRIPT, "SISAL Verarbeitung", skip=False)

    # ── Zusammenfassung ───────────────────────────────────────────────────────
    print_summary(epica_success, sisal_success, start_time)

    # ── Exit Code ─────────────────────────────────────────────────────────────
    if (not args.epica_only and not epica_success) or (
        not args.sisal_only and not sisal_success
    ):
        print("⚠  Einige Schritte sind fehlgeschlagen — siehe Fehler oben.")
        sys.exit(1)
    else:
        print("✓ Pipeline erfolgreich abgeschlossen!")
        sys.exit(0)


# ══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
