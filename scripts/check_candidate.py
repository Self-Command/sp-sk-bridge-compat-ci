"""Check immutable source identity and ZIP bytes before any model call."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

directory=Path(sys.argv[1])
index=json.loads((directory/'candidate-index.json').read_text())
archive=directory/index['zip_name']
assert index['source_sha']==sys.argv[2], 'Candidate SHA mismatch'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==index['zip_sha256'], 'Candidate ZIP digest mismatch'
with zipfile.ZipFile(archive) as z:
    assert 'version: "1.4.0"' in z.read('extension.yml').decode()
    assert 'commands/speckit.speckit-superpowers-bridge.converge.md' in z.namelist()
print(json.dumps(index))
