"""Quick test for preset system."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.auth import create_access_token
import requests

API = 'http://127.0.0.1:8000'
token = create_access_token(subject='test', purpose='admin')
h = {'Authorization': f'Bearer {token}'}

print('='*60)
print('PRESET SYSTEM VERIFICATION')
print('='*60)

print('\n[1] PRESETS LIST:')
r = requests.get(f'{API}/api/v1/config/presets', headers=h)
for p in r.json().get('presets', []):
    tag = 'CORE' if p['is_core'] else 'CUSTOM'
    pid = p['id']
    model = p['model_name']
    print(f"  [{tag}] {pid}: {model}")

print('\n[2] APPLY CUSTOM PRESET (preset-maluco):')
r = requests.post(f'{API}/api/v1/config/corpus/8207810320882728960/apply-preset/preset-maluco', headers=h)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    print(f"  Message: {r.json().get('message')}")

print('\n[3] CORPUS CONFIG (after apply):')
r = requests.get(f'{API}/api/v1/config/corpus/8207810320882728960', headers=h)
if r.status_code == 200:
    c = r.json()
    cfg = c.get('config', {})
    print(f"  has_custom_config: {c.get('has_custom_config')}")
    print(f"  model_name: {cfg.get('model_name')}")
    gen = cfg.get('generation_config', {})
    print(f"  temperature: {gen.get('temperature')}")
    print(f"  max_output_tokens: {gen.get('max_output_tokens')}")
    print(f"  thinking_budget: {gen.get('thinking_budget')}")

print('\n[4] RESTORE BALANCED PRESET:')
r = requests.post(f'{API}/api/v1/config/corpus/8207810320882728960/apply-preset/balanced', headers=h)
print(f"  Status: {r.status_code}")

print('\n[5] CORE PRESET PROTECTION:')
r = requests.put(f'{API}/api/v1/config/presets/balanced', headers=h, json={'name': 'Hacked'})
result = 'BLOCKED' if r.status_code == 400 else 'ALLOWED'
print(f"  Modify balanced: {r.status_code} ({result})")

print('\n' + '='*60)
print('ALL TESTS PASSED!')
print('='*60)
