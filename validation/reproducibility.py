import hashlib, json
from pathlib import Path
from generator.generate import generate, OUT
def checksums():
 return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob("*.csv"))}
def run():
 generate("starter",20261022); first=checksums()
 generate("starter",20261022); second=checksums()
 result={"reproducible":first==second,"first":first,"second":second}
 print(json.dumps(result,indent=2)); return result
if __name__=="__main__": run()
