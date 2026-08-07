# CV Generator

A Python tool that generates professional CVs as PDF from structured JSON data.

## The Problem

Every job seeker in Chile (and everywhere) faces the same issue: you need a different CV for each application. Most people copy-paste between Word documents, lose track of versions, and end up with inconsistent formatting.

## The Solution: Master/Derivative Pattern

Instead of maintaining multiple CV files, this system uses **one master profile** containing your complete career history, and **lightweight derivative configs** that specify what to include, what to hide, and how to format each variant.

```
profiles/maria_gonzalez.json          ← Master: ALL your career data
        +
derivatives/maria_gonzalez/
    senior_retail.json                ← Config: emphasize sales experience
    administrativa_general.json       ← Config: emphasize admin experience
        ↓
engine/loader.py                      ← Merges + filters data
engine/pdf_builder.py                 ← Renders to PDF (ReportLab)
        ↓
output/maria_gonzalez/
    senior_retail.pdf                 ← Ready to send
    administrativa_general.pdf
```

### Key design decisions

- **Single source of truth:** Update the master once, all derivatives stay current
- **Declarative configs:** A derivative is just a JSON with include/exclude lists
- **Filtering by ID:** Each experience entry has an `id` — derivatives reference them explicitly
- **Layout + palette per derivative:** Each CV can have its own visual style

## Features

- **2 layouts:** Single-column (traditional) and two-column with sidebar (modern)
- **5 color palettes:** azul_acero, verde_tech, cyan_krgn, violeta_creativo, gris_profesional
- **Experience filtering:** Include or hide specific jobs per derivative
- **Skill highlighting:** Show only relevant skills for each application
- **Custom objectives:** Each derivative has its own job title and professional summary
- **Professional PDF output:** Segoe UI fonts, letter size, proper spacing

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# See available profiles
python generate.py

# See derivatives for a profile
python generate.py maria_gonzalez

# Generate a PDF
python generate.py maria_gonzalez senior_retail
```

Output PDFs are saved to `output/<profile>/<derivative>.pdf`.

## Creating Your Own Profile

1. **Create a master profile** in `profiles/your_name.json`. Use `profiles/maria_gonzalez.json` as reference.

2. **Create a derivative** in `derivatives/your_name/job_title.json`:

```json
{
  "_meta": {
    "type": "derivative",
    "persona_id": "your_name",
    "derivative_id": "job_title"
  },
  "config": {
    "objetivo_laboral": "Your Target Job Title",
    "perfil_profesional": "Your custom summary for this application...",
    "experiencias_incluir": ["job_id_1", "job_id_2"],
    "habilidades_destacar": ["Skill 1", "Skill 2"],
    "layout": "single_col",
    "paleta": "azul_acero"
  }
}
```

3. **Generate:**
```bash
python generate.py your_name job_title
```

## Architecture

```
cv-generator/
├── generate.py              ← CLI entry point
├── engine/
│   ├── loader.py            ← Data loading, filtering, merging
│   ├── pdf_builder.py       ← ReportLab PDF rendering (CVBuilder class)
│   └── styles.py            ← Palettes, fonts, sizes, page config
├── profiles/                ← Master profiles (one JSON per person)
│   └── maria_gonzalez.json  ← Example profile
├── derivatives/             ← Derivative configs (one folder per person)
│   └── maria_gonzalez/
│       ├── senior_retail.json
│       └── administrativa_general.json
├── output/                  ← Generated PDFs (gitignored)
└── requirements.txt
```

## Data Model

### Master Profile Schema

```json
{
  "persona": {
    "nombre_completo": "String",
    "contacto": { "telefono": "String", "email": "String" },
    "ubicacion": "String",
    "disponibilidad_base": "String"
  },
  "experiencia": [
    {
      "id": "unique_id",
      "empresa": "String",
      "cargo": "String",
      "duracion_texto": "Mar 2021 - Dic 2022",
      "responsabilidades": ["String"],
      "logros": ["String"],
      "habilidades": ["String"]
    }
  ],
  "educacion": [{ "titulo": "String", "institucion": "String", "periodo": "String" }],
  "habilidades": {
    "category_key": { "nombre": "String", "items": ["String"] }
  },
  "idiomas": [{ "idioma": "String", "nivel": "Nativo|Avanzado|Intermedio" }]
}
```

### Derivative Config Schema

| Field | Description |
|-------|-------------|
| `objetivo_laboral` | Job title for this application |
| `perfil_profesional` | Custom summary (full rewrite) |
| `experiencias_incluir` | List of experience IDs to show (takes priority) |
| `experiencias_ocultar` | List of experience IDs to hide |
| `habilidades_destacar` | List of skill items to show (filters from master) |
| `layout` | `single_col` or `two_col_sidebar` |
| `paleta` | `azul_acero`, `verde_tech`, `cyan_krgn`, `violeta_creativo`, `gris_profesional` |

## Requirements

- Python 3.10+
- ReportLab 4.0+
- Segoe UI fonts (Windows default; on Linux/Mac, modify font paths in `engine/styles.py`)

## Tech Highlights

- **ReportLab canvas API** for precise PDF layout control (not templates)
- **OOP design:** `CVBuilder` class encapsulates all rendering logic
- **Declarative configuration:** Derivatives are pure data, no code
- **Extensible:** Adding a new layout or palette is a matter of adding to `styles.py`
