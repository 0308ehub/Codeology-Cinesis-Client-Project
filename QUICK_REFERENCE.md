# Quick Reference Card

## Installation (One-Time Setup)

```bash
pip install -r requirements.txt
```

## Common Tasks

### Test the System
```bash
python demo.py
```

### Process Your CSV File
```bash
python main.py --mode cli --files your_file.csv --carrier-name "Your Company" --carrier-mc "123456"
```

### Process Multiple Files
```bash
python main.py --mode cli --files file1.csv file2.xlsx file3.pdf --carrier-name "Your Company"
```

### Start API Server
```bash
python main.py --mode api --port 5001
```

### Upload File via API
```bash
curl -X POST http://localhost:5001/api/v1/onboard \
  -F "files=@your_file.csv" \
  -F "carrier_name=Your Company" \
  -F "carrier_mc=123456"
```

### Check API Health
```bash
curl http://localhost:5001/health
```

### Get Carrier Status
```bash
curl http://localhost:5001/api/v1/carrier/CARRIER_ID/status
```

## File Format

Your CSV should have columns like:
- Broker/Company name
- MC number
- Load ID
- Origin (e.g., "Miami, FL")
- Destination (e.g., "Tampa, FL")
- Date
- Rate (optional)

## Expected Output

After processing, you'll see:
- Number of brokers, loads, and lanes found
- Deduplication statistics
- Enriched data count
- Preferred lanes and brokers extracted
- Carrier ID (save this for later!)

## Troubleshooting

**Port 5000 in use?** Use port 5001:
```bash
python main.py --mode api --port 5001
```

**Import errors?** Reinstall dependencies:
```bash
pip install -r requirements.txt
```

**Database errors?** Delete and recreate:
```bash
rm carrier_data.db
python demo.py
```

## Need More Help?

See [USER_GUIDE.md](USER_GUIDE.md) for detailed instructions and examples.

