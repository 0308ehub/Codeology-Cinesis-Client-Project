# Carrier Data Processing & Load Matching System

A comprehensive system for processing carrier booking data, normalizing records, enriching with freight market data, and generating intelligent load matches.

## Quick Start for New Users

**New to this system?** Start here:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test with sample data:**
   ```bash
   python demo.py
   ```

3. **Process your own data:**
   ```bash
   python main.py --mode cli --files your_file.csv --carrier-name "Your Company" --carrier-mc "YOUR_MC"
   ```

**📖 For detailed step-by-step instructions, see [USER_GUIDE.md](USER_GUIDE.md)**

## Features

### 1. Multi-Format Parsing
- **CSV**: Parse broker and load data from CSV files
- **Excel**: Support for .xlsx and .xls files with multiple sheets
- **PDF**: Extract booking confirmations from PDF documents
- **Email**: Text extraction from email booking confirmations (planned)

### 2. Data Normalization
- Deduplication of brokers, loads, and lanes
- Address standardization and geocoding
- Rate calculation and validation
- Preference extraction from historical data

### 3. Freight Market Enrichment
- Fill missing rates using market benchmarks
- Lane-level distance and transit time estimates
- Integration with external sources (DAT, Truckstop, FMCSA)
- Confidence scoring for enriched data

### 4. Load Matching Algorithm
- Past booking history ranking
- Preferred lane matching
- Broker relationship scoring
- Equipment type preferences
- Rate quality assessment

### 5. MVP Onboarding Flow
- Complete workflow: upload → parse → normalize → enrich → match
- Support for sparse data (works with incomplete booking history)
- Database persistence
- Status tracking

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
cd /Users/alanwei/Desktop/Codeology-Cinesis-Client-Project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install spaCy language model:
```bash
python -m spacy download en_core_web_sm
```

## Usage

### For New Users

** See [USER_GUIDE.md](USER_GUIDE.md) for a complete guide with examples!**

### Quick Examples

**Process a single file:**
```bash
python main.py --mode cli --files your_data.csv --carrier-name "My Company" --carrier-mc "123456"
```

**Process multiple files:**
```bash
python main.py --mode cli --files file1.csv file2.xlsx file3.pdf
```

**Start API server:**
```bash
python main.py --mode api --port 5001
```

### CLI Mode (Advanced)

Process files directly from command line:

```bash
python main.py --mode cli --files parser/brokers.csv --carrier-name "Demo Carrier" --carrier-mc "123456"
```

Process multiple files:
```bash
python main.py --mode cli --files file1.csv file2.xlsx file3.pdf
```

### API Mode

Start the API server:
```bash
python main.py --mode api --port 5000
```

Or use the API directly:
```bash
python api.py
```

### API Endpoints

#### Health Check
```
GET /health
```

#### Onboard Carrier
```
POST /api/v1/onboard
Content-Type: multipart/form-data

Parameters:
- files: List of files (CSV, Excel, PDF)
- carrier_name: Optional carrier name
- carrier_mc: Optional carrier MC number
```

#### Get Carrier Status
```
GET /api/v1/carrier/<carrier_id>/status
```

#### Get Load Matches
```
POST /api/v1/carrier/<carrier_id>/matches
Content-Type: application/json

Body:
{
  "loads": [...],
  "limit": 10
}
```

#### Get Carrier Profile
```
GET /api/v1/carrier/<carrier_id>/profile
```

### Using the Parser Directly

```python
from parser.unified_parser import UnifiedParser
from normalization import DataNormalizer
from enrichment import EnrichmentEngine
from database import Database

# Parse file
parser = UnifiedParser()
profile = parser.parse_file('brokers.csv')

# Normalize
normalizer = DataNormalizer()
profile = normalizer.normalize_profile(profile)

# Enrich
database = Database()
enrichment = EnrichmentEngine(database)
enriched_lanes = enrichment.enrich_lanes(profile.lanes)
```

## Project Structure

```
.
├── parser/
│   ├── index.py          # Original broker parser (backward compatible)
│   ├── csv_parser.py     # Enhanced CSV parser
│   ├── excel_parser.py   # Excel file parser
│   ├── pdf_parser.py     # PDF parser
│   └── unified_parser.py # Unified parser interface
├── schema.py             # Data models and schemas
├── normalization.py      # Data normalization and cleaning
├── enrichment.py         # Freight market enrichment
├── database.py           # Database models and operations
├── load_matching.py      # Load matching algorithm
├── onboarding.py        # Complete onboarding flow
├── api.py                # REST API endpoints
├── main.py               # Main entry point
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Data Models

### Broker
- Company information
- MC number
- Contact details
- Address

### Load
- Load ID
- Broker relationship
- Lane (origin/destination)
- Rate information
- Equipment type
- Dates (pickup, delivery, booking)

### Lane
- Origin and destination addresses
- Distance (miles)
- Transit time
- Source information

### Rate
- Rate amount
- Rate per mile
- Currency
- Source (raw or enriched)

### Carrier Profile
- Historical brokers
- Historical loads
- Preferred lanes
- Preferred brokers
- Preferred equipment types

## Milestones Completed

✅ **Milestone 1** - Schema Definition
- Complete schema for brokers, loads, lanes, rates, addresses
- Data source tracking
- Enrichment source tracking

✅ **Milestone 2** - CSV/Excel Parsing
- CSV parser with broker and load extraction
- Excel parser with multi-sheet support
- Unified parser interface

✅ **Milestone 3** - Data Normalization
- Deduplication rules
- Address normalization
- Missing field identification
- Preference extraction

✅ **Milestone 4** - Database Integration
- SQLAlchemy models
- SQLite and PostgreSQL support
- Raw + enriched field storage
- Source tagging

✅ **Milestone 5** - Algorithm Enhancement
- Past booking ranking
- Preferred lane matching
- Broker relationship scoring
- Rate quality assessment

✅ **Milestone 6** - Enrichment Framework
- Lane-level benchmarks
- Rate estimation
- Distance calculation
- Confidence scoring

✅ **Milestone 7** - End-to-End Flow
- Complete onboarding workflow
- API endpoints
- Status tracking

✅ **Milestone 8** - PDF Parsing
- PDF text extraction
- Booking confirmation parsing
- Regex-based data extraction

## Testing

Run tests (when test files are created):
```bash
pytest tests/
```

## Configuration

### Database

Set database URL via environment variable:
```bash
export DATABASE_URL=postgresql://user:password@localhost/carrier_data
```

Default: SQLite (`carrier_data.db`)

### API Configuration

Edit `api.py` to configure:
- Upload folder
- Max file size
- Allowed file types

## Development

### Adding New Parsers

1. Create parser class in `parser/` directory
2. Implement `parse_file()` method
3. Register in `unified_parser.py`

### Adding Enrichment Sources

1. Add source to `EnrichmentSource` enum in `schema.py`
2. Implement method in `EnrichmentEngine`
3. Update database model if needed

## Future Enhancements

- Email parsing with NLP
- Real-time DAT/Truckstop API integration
- Geocoding service integration
- Advanced matching algorithms
- Machine learning for rate prediction
- Web UI for onboarding
- Batch processing for large datasets

## License

[Add license information]

## Support

[Add support contact information]

