# Project Structure

This document describes the organization of the codebase.

## Directory Structure

```
Codeology-Cinesis-Client-Project/
├── parser/                    # Parsing modules
│   ├── __init__.py           # Package exports
│   ├── utils.py              # Shared parsing utilities
│   ├── csv_parser.py         # CSV file parser
│   ├── excel_parser.py       # Excel file parser
│   ├── pdf_parser.py         # PDF file parser
│   ├── email_parser.py       # Email text parser
│   ├── unified_parser.py     # Unified parser interface
│   ├── index.py              # Legacy entry point (deprecated)
│   └── brokers.csv           # Sample data file
│
├── tests/                     # Test suite
│   ├── __init__.py
│   └── test_parser.py        # Parser tests
│
├── uploads/                   # Temporary file uploads (gitignored)
│
├── Core Modules
│   ├── schema.py             # Data models and schemas
│   ├── normalization.py      # Data cleaning and deduplication
│   ├── enrichment.py         # Market data enrichment
│   ├── database.py           # Database models and operations
│   ├── load_matching.py     # Load matching algorithm
│   ├── onboarding.py        # Complete onboarding workflow
│
├── API & Entry Points
│   ├── api.py                # REST API endpoints
│   ├── main.py               # CLI/API entry point
│   ├── demo.py               # Demo script
│
├── Configuration
│   ├── requirements.txt      # Python dependencies
│   ├── config.example.py    # Configuration template
│   └── .gitignore           # Git ignore rules
│
└── Documentation
    ├── README.md             # Main documentation
    ├── USER_GUIDE.md         # Comprehensive user guide
    ├── QUICK_REFERENCE.md    # Quick command reference
    ├── PROJECT_SUMMARY.md    # Project overview
    └── PROJECT_STRUCTURE.md  # This file
```

## Module Responsibilities

### Parser Module (`parser/`)
- **utils.py**: Shared utility functions (date parsing, trip parsing, rate extraction)
- **csv_parser.py**: Parses CSV files with broker/load data
- **excel_parser.py**: Parses Excel files (.xlsx, .xls)
- **pdf_parser.py**: Extracts data from PDF booking confirmations
- **email_parser.py**: Parses email text for booking information
- **unified_parser.py**: Single interface for all file types
- **index.py**: Legacy code (deprecated, kept for reference)

### Core Modules
- **schema.py**: Data models (Broker, Load, Lane, Rate, Address, CarrierProfile, EnrichedData)
- **normalization.py**: Data cleaning, deduplication, preference extraction
- **enrichment.py**: Market data enrichment and estimation
- **database.py**: SQLAlchemy models and database operations
- **load_matching.py**: Algorithm for matching loads to carriers
- **onboarding.py**: Complete onboarding workflow orchestration

### API & Entry Points
- **api.py**: Flask REST API with endpoints for onboarding and matching
- **main.py**: Command-line interface and API server launcher
- **demo.py**: Demonstration script showing complete workflow

## Code Organization Principles

1. **Single Responsibility**: Each module has a clear, single purpose
2. **DRY (Don't Repeat Yourself)**: Common functions in `parser/utils.py`
3. **Separation of Concerns**: Parsing, normalization, enrichment, and matching are separate
4. **Consistent Naming**: Modules use descriptive, consistent names
5. **Documentation**: All modules have docstrings and clear comments

## Import Structure

```
parser/
  ├── utils.py (shared utilities)
  ├── csv_parser.py (base parser)
  ├── excel_parser.py (extends csv_parser)
  ├── pdf_parser.py (standalone)
  ├── email_parser.py (extends csv_parser)
  └── unified_parser.py (orchestrates all parsers)

Core modules import from:
  - schema.py (data models)
  - parser.unified_parser (parsing)
  
API imports from:
  - onboarding.py (workflow)
  - database.py (persistence)
```

## File Naming Conventions

- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`

## Dependencies

- **External**: Listed in `requirements.txt`
- **Internal**: Clear dependency hierarchy (no circular dependencies)
- **Shared Code**: Common utilities in `parser/utils.py`

## Testing

- Tests in `tests/` directory
- Test files mirror module structure: `test_<module>.py`
- Run with: `pytest tests/`

## Documentation

- **README.md**: Overview and quick start
- **USER_GUIDE.md**: Comprehensive user documentation
- **QUICK_REFERENCE.md**: Command cheat sheet
- **PROJECT_SUMMARY.md**: Technical overview
- **PROJECT_STRUCTURE.md**: This file

