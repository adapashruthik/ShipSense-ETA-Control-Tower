import os, csv, sys
from pathlib import Path
from dotenv import load_dotenv
import pymysql

ROOT=Path(__file__).resolve().parents[1]; load_dotenv(ROOT/".env")
conn=pymysql.connect(host=os.getenv("MYSQL_HOST","127.0.0.1"),port=int(os.getenv("MYSQL_PORT",3306)),
 user=os.getenv("MYSQL_USER","root"),password=os.getenv("MYSQL_PASSWORD",""),database=os.getenv("MYSQL_DATABASE","shipsense"),
 charset="utf8mb4",autocommit=False)
ORDER=["carriers","facilities","service_levels","routes","weather_events","shipments","shipment_legs","tracking_events",
 "facility_queues","route_weather_impacts","delay_reasons","eta_estimates","shipment_delay_assessments","shipment_status_history","data_quality_issues",
 "carrier_calendars","facility_disruptions","route_change_history"]
def clean(v):
 if v=="": return None
 if v in ("0","1"): return int(v)
 return v
with conn.cursor() as cur:
 for table in ORDER:
  path=ROOT/"data"/"generated"/f"{table}.csv"
  if not path.exists(): continue
  with path.open(encoding="utf-8") as f:
   reader=csv.DictReader(f); cols=reader.fieldnames
   sql=f"INSERT IGNORE INTO {table} ({','.join('`'+c+'`' for c in cols)}) VALUES ({','.join(['%s']*len(cols))})"
   batch=[]
   for row in reader:
    batch.append(tuple(clean(row[c]) for c in cols))
    if len(batch)>=1000: cur.executemany(sql,batch); batch=[]
   if batch: cur.executemany(sql,batch)
  print(f"Loaded {table}")
conn.commit(); conn.close()
print("Database load complete.")
