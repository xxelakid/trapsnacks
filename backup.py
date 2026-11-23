# backup.py
# Copies the database to the "backups" folder with today's date (Security requirement 5).
# Run it with:  python backup.py   (or schedule it once a day with Windows Task Scheduler)

import os
import shutil
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, 'instance', 'trapsnacks.db')
FOLDER = os.path.join(HERE, 'backups')

os.makedirs(FOLDER, exist_ok=True)
target = os.path.join(FOLDER, f"trapsnacks-{datetime.now():%Y-%m-%d-%H%M}.db")
shutil.copy2(SOURCE, target)
print('Backup saved to', target)
