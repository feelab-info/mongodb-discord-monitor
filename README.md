# MongoDB Discord Checker
A monitoring script that checks MongoDB for recent data and sends alerts to Discord when data is missing.

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate`
3. Install requirements: `pip install -r requirements.txt`
4. Copy `config.ini.example` to `config.ini` and fill in your details
5. Run the script: `python check_mongodb.py`
