# User Guide: Carrier Data Processing System

Welcome! This guide will help you get started with processing your carrier booking data and generating load matches.

## What Does This System Do?

This system helps you:
1. **Parse** your booking data from CSV, Excel, or PDF files
2. **Clean** and organize the data (remove duplicates, standardize formats)
3. **Enrich** missing information using market estimates
4. **Match** new loads to your carrier based on your historical booking patterns

## Quick Start (5 Minutes)

### Step 1: Install Dependencies

Open your terminal and navigate to the project folder, then run:

```bash
pip install -r requirements.txt
```

**Troubleshooting:**
- If you get permission errors, try: `pip install --user -r requirements.txt`
- If using Python 3, make sure you use `pip3` instead of `pip`

### Step 2: Prepare Your Data File

You need a CSV, Excel, or PDF file with your booking data. The CSV format should have columns like:
- Broker/Company name
- MC number
- Load ID
- Origin and Destination
- Dates
- Rates (optional)

**Example CSV format:**
```csv
Name,Broker,MC#,Phone Number,Email,Address,Date,Load #,State,Trip,Notes,Load Board
John Doe,ABC Logistics,123456,555-1234,john@abc.com,123 Main St,10/28/24,LOAD001,FL,Miami FL to Tampa FL,Rate: $1500,
```

### Step 3: Run the Demo (Test with Sample Data)

First, let's test with the included sample data:

```bash
python demo.py
```

This will:
- Parse the sample `brokers.csv` file
- Show you how the system processes data
- Display statistics and preferences extracted

**Expected Output:**
```
✓ Parsed 337 brokers
✓ Parsed 286 loads
✓ Parsed 298 lanes
✓ Deduplicated 169 brokers
✓ Enriched 278 lanes
```

### Step 4: Process Your Own Data

Once the demo works, process your own file:

**Option A: Using Command Line (CLI)**
```bash
python main.py --mode cli --files path/to/your/file.csv --carrier-name "Your Carrier Name" --carrier-mc "YOUR_MC_NUMBER"
```

**Example:**
```bash
python main.py --mode cli --files my_bookings.csv --carrier-name "ABC Transport" --carrier-mc "123456"
```

**Option B: Using the API (Web Interface)**

1. Start the API server:
```bash
python main.py --mode api --port 5001
```

2. In another terminal, upload your file:
```bash
curl -X POST http://localhost:5001/api/v1/onboard \
  -F "files=@my_bookings.csv" \
  -F "carrier_name=ABC Transport" \
  -F "carrier_mc=123456"
```

## Detailed Usage Examples

### Example 1: Process a Single CSV File

```bash
python main.py --mode cli --files bookings_2024.csv --carrier-name "My Trucking Company" --carrier-mc "789012"
```

**What happens:**
- System reads your CSV file
- Extracts brokers, loads, and lanes
- Removes duplicates
- Enriches missing data
- Saves to database
- Shows you a summary

### Example 2: Process Multiple Files

```bash
python main.py --mode cli --files january.csv february.csv march.xlsx --carrier-name "My Company" --carrier-mc "789012"
```

The system will combine all files into one carrier profile.

### Example 3: Process PDF Booking Confirmations

```bash
python main.py --mode cli --files booking_confirmation.pdf --carrier-name "My Company" --carrier-mc "789012"
```

The system will extract data from PDF booking confirmations.

### Example 4: Using Python Code Directly

Create a file called `my_script.py`:

```python
from parser.unified_parser import UnifiedParser
from normalization import DataNormalizer
from enrichment import EnrichmentEngine
from database import Database
from onboarding import OnboardingFlow

# Initialize
database = Database()
onboarding = OnboardingFlow(database)

# Process your file
results = onboarding.process_upload(
    ['path/to/your/file.csv'],
    carrier_name="My Carrier",
    carrier_mc="123456"
)

# Print results
print(f"Carrier ID: {results['carrier_id']}")
print(f"Brokers found: {results['stats']['final_brokers']}")
print(f"Loads found: {results['stats']['final_loads']}")
print(f"Lanes found: {results['stats']['final_lanes']}")

# Check for errors
if results['errors']:
    print("Errors:", results['errors'])
if results['warnings']:
    print("Warnings:", results['warnings'])
```

Run it:
```bash
python my_script.py
```

## Understanding Your Results

After processing, you'll see:

### Statistics
- **Brokers**: Number of unique brokers found
- **Loads**: Number of booking records
- **Lanes**: Number of unique origin-destination pairs
- **Deduplicated**: How many duplicates were removed

### Preferences Extracted
- **Preferred Lanes**: Your most frequently used routes
- **Preferred Brokers**: Brokers you work with most often
- **Preferred Equipment**: Equipment types you typically use

### Carrier ID
- A unique identifier for your carrier profile
- Use this to get matches and check status later

## Getting Load Matches

Once your data is processed, you can get load recommendations:

### Using the API

1. Start the API server (if not already running):
```bash
python main.py --mode api --port 5001
```

2. Get matches for your carrier:
```bash
curl -X POST http://localhost:5001/api/v1/carrier/YOUR_CARRIER_ID/matches \
  -H "Content-Type: application/json" \
  -d '{
    "loads": [
      {
        "load_id": "NEW_LOAD_001",
        "origin": "Miami, FL",
        "destination": "Tampa, FL",
        "broker_mc": "123456"
      }
    ],
    "limit": 10
  }'
```

### Using Python Code

```python
from load_matching import LoadMatchingEngine
from schema import Load, Lane, Broker, Rate, DataSource

# Load your carrier profile (from database)
# ... (code to load profile)

# Create matching engine
matching_engine = LoadMatchingEngine(carrier_profile)

# Define available loads
available_loads = [
    Load(
        load_id="NEW_001",
        broker=Broker(mc_id="123456", company_name="ABC Logistics"),
        lane=Lane(origin_city_state="Miami, FL", destination_city_state="Tampa, FL"),
        rate=Rate(rate_amount=1500.0),
        source=DataSource.MANUAL
    )
]

# Get matches
matches = matching_engine.match_loads(available_loads, limit=10)

# Print results
for match in matches:
    print(f"Load {match.load.load_id}: Score {match.score:.2f}")
    print(f"  Reasons: {', '.join(match.match_reasons)}")
```

## File Format Requirements

### CSV Format

Your CSV should have these columns (column names can vary):

**Required:**
- Broker/Company name
- Load ID or reference number
- Origin location
- Destination location

**Optional but helpful:**
- MC number
- Dates (pickup, delivery, booking)
- Rate/Amount
- Equipment type
- Phone/Email

**Example:**
```csv
Broker,MC#,Load #,Origin,Destination,Date,Rate
ABC Logistics,123456,LOAD001,Miami FL,Tampa FL,10/28/24,$1500
XYZ Transport,789012,LOAD002,Orlando FL,Jacksonville FL,10/29/24,$1200
```

### Excel Format

Same columns as CSV, but in Excel (.xlsx or .xls format). You can have multiple sheets - the system will process all of them.

### PDF Format

PDFs should be booking confirmations or rate confirmations. The system will extract:
- Broker information
- Load ID
- Origin/Destination
- Dates
- Rates

## Testing Your Setup

### Test 1: Basic Import Test
```bash
python -c "from parser.unified_parser import UnifiedParser; print('✓ Imports working')"
```

### Test 2: Parse Sample File
```bash
python demo.py
```

### Test 3: Process Your File
```bash
python main.py --mode cli --files your_file.csv --carrier-name "Test" --carrier-mc "000000"
```

### Test 4: API Health Check
```bash
# Start API
python main.py --mode api --port 5001

# In another terminal
curl http://localhost:5001/health
```

## Common Issues and Solutions

### Issue: "Module not found" error

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Port 5000 already in use"

**Solution:** Use a different port:
```bash
python main.py --mode api --port 5001
```

### Issue: "No data parsed" or "0 brokers found"

**Possible causes:**
1. Column names don't match expected format
2. File encoding issue (try saving as UTF-8)
3. Empty file or wrong file format

**Solution:**
- Check your CSV has headers
- Verify column names match expected format
- Try with the sample `brokers.csv` first to confirm setup works

### Issue: "Database error" or "UNIQUE constraint failed"

**Solution:** Delete the database file and try again:
```bash
rm carrier_data.db
python demo.py
```

### Issue: PDF parsing not working

**Solution:** Make sure pdfplumber is installed:
```bash
pip install pdfplumber
```

## Understanding the Output

### What Gets Created

1. **Database** (`carrier_data.db`): SQLite database with all your data
2. **Carrier Profile**: Your complete profile with preferences
3. **Enriched Data**: Market estimates for missing information

### What the Scores Mean

When you get load matches, scores range from 0.0 to 1.0:
- **0.8-1.0**: Excellent match (past broker, exact lane match)
- **0.5-0.8**: Good match (similar lane, preferred equipment)
- **0.3-0.5**: Fair match (some preferences match)
- **Below 0.3**: Weak match (base score for new carriers)

### Match Reasons

The system explains why each load matches:
- "Past broker match" - You've worked with this broker before
- "Exact lane match" - You've done this exact route
- "Preferred lane" - This is one of your top routes
- "Preferred equipment" - You typically use this equipment type

## Next Steps

1. **Process your data**: Start with one file to test
2. **Review results**: Check the statistics and preferences
3. **Get matches**: Try matching some available loads
4. **Iterate**: Process more files to improve matching accuracy

## Getting Help

If you encounter issues:

1. **Check the logs**: Look for error messages in the terminal
2. **Verify file format**: Make sure your CSV matches the expected format
3. **Test with sample data**: Run `python demo.py` to confirm setup
4. **Check dependencies**: Run `pip install -r requirements.txt` again

## Example Workflow

Here's a complete example workflow:

```bash
# 1. Install dependencies (one time)
pip install -r requirements.txt

# 2. Test with sample data
python demo.py

# 3. Process your own data
python main.py --mode cli --files my_bookings.csv --carrier-name "My Company" --carrier-mc "123456"

# 4. Start API server
python main.py --mode api --port 5001

# 5. Check your carrier status (use carrier_id from step 3)
curl http://localhost:5001/api/v1/carrier/YOUR_CARRIER_ID/status

# 6. Get load matches
curl -X POST http://localhost:5001/api/v1/carrier/YOUR_CARRIER_ID/matches \
  -H "Content-Type: application/json" \
  -d '{"loads": [...], "limit": 10}'
```

## Tips for Best Results

1. **More data = Better matches**: Process multiple months of data
2. **Complete information**: Include rates, dates, and equipment when possible
3. **Consistent formatting**: Use consistent city/state format (e.g., "Miami, FL")
4. **Regular updates**: Process new bookings regularly to keep preferences current

## What Data is Stored?

The system stores:
- Broker information (names, MC numbers, contacts)
- Load history (routes, dates, rates)
- Lane patterns (origin-destination pairs)
- Your preferences (extracted automatically)

**Privacy**: All data is stored locally in the `carrier_data.db` file on your computer.

---

**Ready to get started?** Run `python demo.py` to see it in action!

