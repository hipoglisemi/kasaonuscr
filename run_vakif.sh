
#!/bin/bash
cd /Users/hipoglisemi/Desktop/kartavantaj-scraper || exit
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
python src/scrapers/vakifbank.py
