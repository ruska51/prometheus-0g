# Architecture

Layers are independent: `data -> physics -> models -> validation -> insights -> app` (CLAUDE.md section 5). The app never computes physics itself; it calls the `fif` package.

## Data layer (stage 3)

```mermaid
flowchart LR
    subgraph raw["data/raw (never modified, sha256 in data/catalog.yaml)"]
        R1["psi_records/*.json.gz<br/>24 PSI investigation records"]
        R2["psi_tables/*.csv<br/>22 Experimental Tables"]
        R3["ntrs/20150023456.pdf<br/>FLEX TP (not in git, fetched on demand)"]
        R0["psi_metadata/*.zip<br/>ISA-Tab (Ruslan's download)"]
    end
    F1["scripts/fetch_psi.py"] --> R1 & R2
    subgraph pkg["src/fif/data"]
        C["catalog.py<br/>registry + checksum verify"]
        P1["parsers/flex.py"]
        P2["parsers/cfig.py"]
        P3["parsers/psi_catalog.py"]
        CL["clean.py<br/>SI units, flags, targets,<br/>pre-ignition features, CV groups"]
        S["schema.py<br/>pandera checks"]
        FE["features.py<br/>pre / post-ignition split"]
    end
    R2 --> P1 & P2
    R1 --> P3
    P1 & P2 & P3 --> I["data/interim/*.csv<br/>(raw text kept)"]
    I --> CL --> S --> O["data/processed/*.csv<br/>+ transform_log.tsv<br/>+ quality_flags.tsv"]
    R3 --> V["scripts/verify_flex_vs_tp.py"] --> VO["docs/verification/flex_vs_tp.tsv"]
    O --> E["scripts/eda.py"] --> FG["docs/figures/*.png"]
    O --> NEXT["physics / models (stages 4-5)"]
```

| Module | Purpose | Inputs -> outputs |
|---|---|---|
| `fif.data.catalog` | read `data/catalog.yaml`, resolve raw paths, verify sha256 | YAML -> dicts |
| `fif.data.parsers.flex` | PSI-69 CSV -> interim, raw cell text kept | CSV -> DataFrame (274 rows) |
| `fif.data.parsers.cfig` | PSI-159 normal + inverse CSVs -> interim | 2 CSV -> DataFrame (333 rows) |
| `fif.data.parsers.psi_catalog` | 24 PSI records -> investigation catalog | JSON -> DataFrame (24 rows) |
| `fif.data.clean` | units to SI, quality flags, targets, derived pre-ignition features, CV groups; every step logged | interim -> processed |
| `fif.data.schema` | pandera schemas: types, physical bounds, flag consistency | processed -> validated |
| `fif.data.features` | lists of pre-ignition features vs post-ignition columns (leakage guard) | - |
| `fif.data.build` | the pipeline; tests pass a temporary output dir | raw -> interim + processed |

Commands (repository root):

```
.venv/Scripts/python scripts/fetch_psi.py         # re-download PSI records + tables (network)
.venv/Scripts/python scripts/build_data.py        # raw -> interim -> processed
.venv/Scripts/python scripts/verify_flex_vs_tp.py # FLEX CSV vs NASA/TP Table IX (downloads the PDF once)
.venv/Scripts/python scripts/eda.py               # figures in docs/figures
.venv/Scripts/python -m pytest -q
```

Every processed row carries provenance: `source_id`, `source_file`, `row_id`, `quality_flag`.

## Physics, models, validation, insights, app

_Stages 4-8._
