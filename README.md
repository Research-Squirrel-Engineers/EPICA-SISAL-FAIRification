# EPICA-SISAL-FAIRification

![Squilly Logo](logo.png)

# EPICA + SISAL Palaeoclimate Data Processing

Pipeline for generating plots, RDF/Linked Open Data, and visualisations from EPICA and SISAL palaeoclimate data.

## 📁 Structure

```
project/
├── main.py                       ← MAIN SCRIPT (run everything)
│
├── EPICA/                        ← EPICA Dome C (ice core)
│   ├── plot_epica_from_tab.py
│   ├── plots/                    ← PNG diagrams
│   │   └── epica_*.png
│   ├── rdf/                      ← RDF/TTL + Mermaid
│   │   ├── epica_ontology.ttl
│   │   ├── epica_dome_c.ttl
│   │   └── mermaid_*.mermaid
│   └── report/
│       └── report.txt
│
├── SISAL/                        ← SISAL (speleothems)
│   ├── plot_sisal_from_csv.py
│   ├── plots/                    ← PNG diagrams
│   │   └── sisal_*.png
│   ├── rdf/                      ← RDF/TTL + Mermaid
│   │   ├── sisal_ontology.ttl
│   │   ├── sisal_sites.ttl
│   │   ├── sisal_all_data.ttl
│   │   └── mermaid_*.mermaid
│   └── report/
│       └── report.txt
│
├── ontology/                     ← Shared ontology utilities
│   └── geo_lod_utils.py
│
├── data/                         ← Input data (Tab/CSV)
│   ├── EDC_CH4.tab
│   ├── EPICA_Dome_C_d18O.tab
│   ├── v_data_144_botuvera.csv
│   ├── v_data_145_corchia.csv
│   ├── v_data_146_cueva_de_las_brujas.csv
│   └── v_sites_all.csv           ← All 305 SISAL sites
│
├── src/
│   └── .gitignore
│
├── README.md
└── LICENSE
```

## 🚀 Usage

### Run everything (recommended)

```bash
python main.py
```

This executes:
1. ✓ EPICA Dome C — Plots + RDF
2. ✓ SISAL — Plots + RDF
3. ✓ Combined FeatureCollection
4. ✓ Mermaid diagrams

### EPICA only

```bash
python main.py --epica-only
```

### SISAL only

```bash
python main.py --sisal-only
```

### RDF only (no plots)

```bash
python main.py --no-plots
```

### Plots only (no RDF)

```bash
python main.py --no-rdf
```

## 📊 Output

### Plots (PNG)

**EPICA Dome C:**
- `epica_ch4_depth_*.png` — CH₄ by depth (m)
- `epica_ch4_age_*.png` — CH₄ by age (ka BP)
- `epica_d18o_depth_*.png` — δ¹⁸O by depth (m)
- `epica_d18o_age_*.png` — δ¹⁸O by age (ka BP)

Variants: `unsmoothed`, `smooth11`, `savgol11p2`

**SISAL:**
- `{site}_d18o_age_*.png` — δ¹⁸O by age
- `{site}_d13c_age_*.png` — δ¹³C by age

Sites: `botuvera`, `corchia`, `cueva_de_las_brujas`

### RDF/Linked Open Data (TTL)

**Core Ontology:**
- `geo_lod_core.ttl` — Shared base classes (PalaeoclimateObservation, SamplingLocation, etc.)

**EPICA:**
- `epica_ontology.ttl` — EPICA-specific classes (IceCoreObservation, DrillingSite, etc.)
- `epica_dome_c.ttl` — Data (1 site, ~1400 observations)

**SISAL:**
- `sisal_ontology.ttl` — SISAL-specific classes (SpeleothemObservation, Cave, etc.)
- `sisal_sites.ttl` — All 305 SISAL caves with geometries
- `sisal_{site}_data.ttl` — Observations per cave
- `sisal_all_data.ttl` — Combined file (sites + all observations)

**Combined:**
- `all_palaeoclimate_sites_collection.ttl` — geo:FeatureCollection with all 306 sites (1 EPICA + 305 SISAL)

### Mermaid Diagrams

- `mermaid_taxonomy.mermaid` — Class hierarchy (Core + EPICA + SISAL)
- `mermaid_instance_epica.mermaid` — EPICA named individuals
- `mermaid_instance_sisal.mermaid` — SISAL named individuals

## 🔍 SPARQL Queries

After export, you can load the TTL files into a triplestore and query them:

### All Sites

```sparql
PREFIX geolod: <http://w3id.org/geo-lod/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?site ?label ?wkt
WHERE {
  geolod:AllPalaeoclimateSites_Collection rdfs:member ?site .
  ?site rdfs:label ?label ;
        geo:hasGeometry/geo:asWKT ?wkt .
}
```

Result: 306 sites

### EPICA CH₄ Observations

```sparql
PREFIX geolod: <http://w3id.org/geo-lod/>
PREFIX sosa: <http://www.w3.org/ns/sosa/>

SELECT ?obs ?age ?value ?smoothed
WHERE {
  ?obs a geolod:CH4Observation ;
       geolod:ageKaBP ?age ;
       geolod:measuredValue ?value ;
       geolod:smoothedValue_rollingMedian ?smoothed .
}
ORDER BY ?age
```

### SISAL Sites with Sample Counts

```sparql
PREFIX geolod: <http://w3id.org/geo-lod/>

SELECT ?cave ?name ?d18o_count ?d13c_count
WHERE {
  ?cave a geolod:Cave ;
        rdfs:label ?name ;
        geolod:countD18OSamples ?d18o_count ;
        geolod:countD13CSamples ?d13c_count .
}
ORDER BY DESC(?d18o_count)
```

## 🛠️ Dependencies

```bash
pip install numpy pandas matplotlib scipy rdflib
```

**Optional (for Mermaid rendering):**
```bash
npm install -g @mermaid-js/mermaid-cli
```

## 📝 Ontology Overview

### Class Hierarchy

```
geolod:PalaeoclimateObservation
  ├── geolod:IceCoreObservation (EPICA)
  │     ├── geolod:CH4Observation
  │     └── geolod:Delta18OObservation
  └── geolod:SpeleothemObservation (SISAL)
        ├── geolod:Delta18OSpeleothemObservation
        └── geolod:Delta13CSpeleothemObservation

geolod:SamplingLocation
  ├── geolod:DrillingSite (EPICA)
  └── geolod:Cave (SISAL)

geolod:PalaeoclimateSample
  ├── geolod:IceCore (EPICA)
  └── geolod:Speleothem (SISAL)

geolod:Chronology
  ├── geolod:IceCoreChronology (EPICA — EDC2, AICC2023)
  └── geolod:UThChronology (SISAL)
```

### FeatureCollections (GeoSPARQL)

- `geolod:EPICA_DrillingSite_Collection` — 1 member
- `geolod:SISAL_Cave_Collection` — 305 members
- `geolod:AllPalaeoclimateSites_Collection` — 306 members (combined)

## 🌐 W3ID URIs

All resources use persistent W3ID.org URIs:

- Namespace: `http://w3id.org/geo-lod/`
- Example site: `http://w3id.org/geo-lod/EpicaDomeC_Site`
- Example observation: `http://w3id.org/geo-lod/Obs_CH4_epica_00001`

## 📖 Literature

**EPICA:**
- Lüthi et al. (2008): High-resolution carbon dioxide concentration record 650,000-800,000 years before present. Nature 453, 379-382.
- Loulergue et al. (2008): Orbital and millennial-scale features of atmospheric CH4 over the past 800,000 years. Nature 453, 383-386.

**SISAL:**
- Kaushal et al. (2024): SISALv3: a global speleothem stable isotope and trace element database. Earth System Science Data 16, 1933-1963. https://doi.org/10.5194/essd-16-1933-2024

**MIS Boundaries:**
- Lisiecki & Raymo (2005): A Plio-Pleistocene stack of 57 globally distributed benthic δ¹⁸O records. Paleoceanography 20, PA1003.

## 🐛 Troubleshooting

### Import Error: `ModuleNotFoundError: No module named 'geo_lod_utils'`

→ Make sure `geo_lod_utils.py` is in the `ontology/` directory:
```
project/
├── main.py
├── EPICA/
│   └── plot_epica_from_tab.py
├── SISAL/
│   └── plot_sisal_from_csv.py
└── ontology/
    └── geo_lod_utils.py  ← must be here!
```

The scripts automatically add `ontology/` to the Python path.

### No data found

→ Check if input files are in the `data/` folder:
```bash
ls data/*.tab data/*.csv
```

### RDF export not working

→ Install rdflib:
```bash
pip install rdflib
```

## 🤝 Author

**Florian Thiery**  
ORCID: https://orcid.org/0000-0002-3246-3531

## 📄 Licence

CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/