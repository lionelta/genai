#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
"""ask_adm_toolfile.py

Minimal toolfile exposing only the get_preserved_models tool (extracted from
ask_gk_toolfile.py) for use by ask_adm.py. The structure matches the existing
project's expectations: each tool is represented by a *_dict variable containing
its JSON schema, accompanied by the implementation function. A global
'all_tools' list is automatically assembled from *_dict globals.
"""
import os
import sys
import subprocess
import logging
import json

LOGGER = logging.getLogger(__name__)

# Allow relative imports for project libs if needed
rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)

# -----------------------------------------------------------------------------
# get_preserved_models
# -----------------------------------------------------------------------------
get_preserved_models_dict = {
    'type': 'function',
    'function': {
        'name': 'get_preserved_models',
        'description': 'Return a unified list of preserved models (dropbox + syncpoint + waiver) with optional filters.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filter_domain': {
                    'type': 'string',
                    'description': 'Only include models whose domain matches (substring, case-insensitive).',
                },
                'filter_milestone': {
                    'type': 'string',
                    'description': 'Only include models whose milestone matches (substring, case-insensitive).',
                },
                'filter_name': {
                    'type': 'string',
                    'description': 'Only include models whose name contains this substring (case-insensitive).',
                },
                'source': {
                    'type': 'string',
                    'description': 'Limit to a specific source: dropbox | syncpoint | waiver | both (default both; both == all sources).',
                },
                'limit': {
                    'type': 'string',
                    'description': 'Maximum number of models to return (after filtering). Provide a numeric string (e.g. "25").',
                }
            },
        },
    }
}

def get_preserved_models(filter_domain: str = None,
                         filter_milestone: str = None,
                         filter_name: str = None,
                         source: str = 'both',
                         limit: str = None):
    """Fetch and return preserved models with optional filtering.

    Returns a JSON string so downstream LLMs can easily consume / display it.
    """
    cmd = [
        '/p/cth/cad/dmx/wplim_dev/cmx/bin/adm', 'preserve', '--report',
        '--include-syncpoint', '--include-dropbox', '--json'
    ]
    try:
        raw = subprocess.check_output(cmd, text=True)
    except Exception as e:
        return json.dumps({'error': f'Failed running preserve command: {e}'})

    try:
        data = json.loads(raw)
    except Exception as e:
        return json.dumps({'error': f'Failed parsing JSON output: {e}'})

    dropbox_models = data.get('dropbox', {}).get('models', {})  # name -> {domain, milestone}
    syncpoint_models = data.get('syncpoint', {}).get('models', {})  # name -> tag string
    waiver_file = data.get('waiver_file')
    waivers_list = data.get('waivers', []) or []  # list of model names waived
    if not isinstance(waivers_list, list):
        waivers_list = []
    waivers_set = set(waivers_list)

    unified = {}
    # Incorporate dropbox first
    for name, meta in dropbox_models.items():
        unified[name] = {
            'name': name,
            'domain': meta.get('domain'),
            'milestone': meta.get('milestone'),
            'syncpoint_tag': None,
            'sources': ['dropbox'],  # waiver modeled as an additional source label 'waiver'
        }
    # Merge syncpoint
    for name, tag in syncpoint_models.items():
        if not name:
            continue  # skip empty key if present
        entry = unified.get(name)
        if entry is None:
            entry = {
                'name': name,
                'domain': None,
                'milestone': None,
                'syncpoint_tag': None,
                'sources': ['syncpoint'],
            }
            unified[name] = entry
        if tag:
            entry['syncpoint_tag'] = tag
        if 'syncpoint' not in entry['sources']:
            entry['sources'].append('syncpoint')

    # Add waiver as a distinct source if applicable
    for wname in waivers_set:
        entry = unified.get(wname)
        if entry is None:
            unified[wname] = {
                'name': wname,
                'domain': None,
                'milestone': None,
                'syncpoint_tag': None,
                'sources': ['waiver'],
            }
        else:
            if 'waiver' not in entry['sources']:
                entry['sources'].append('waiver')

    # Apply filters
    def _match(val, pattern):
        if pattern is None:
            return True
        if val is None:
            return False
        return pattern.lower() in str(val).lower()

    src_filter = (source or 'both').lower()
    filtered = []
    for m in unified.values():
        if src_filter != 'both':
            if src_filter == 'dropbox' and 'dropbox' not in m['sources']:
                continue
            if src_filter == 'syncpoint' and 'syncpoint' not in m['sources']:
                continue
            if src_filter == 'waiver' and 'waiver' not in m['sources']:
                continue
        if not _match(m.get('domain'), filter_domain):
            continue
        if not _match(m.get('milestone'), filter_milestone):
            continue
        if not _match(m.get('name'), filter_name):
            continue
        filtered.append(m)

    filtered.sort(key=lambda x: x['name'])

    if limit is not None:
        try:
            l = int(limit)
            if l >= 0:
                filtered = filtered[:l]
        except ValueError:
            pass

    returned_waived_models = sum(1 for m in filtered if 'waiver' in m.get('sources', []))

    result = {
        'summary': {
            'dropbox_models': len(dropbox_models),
            'syncpoint_models': len(syncpoint_models),
            'unified_models': len(unified),
            'returned_models': len(filtered),
            'total_waived_models': data.get('total_waived_models', len(waivers_set)),
            'returned_waived_models': returned_waived_models,
            'waiver_file': waiver_file,
            'filters': {
                'filter_domain': filter_domain,
                'filter_milestone': filter_milestone,
                'filter_name': filter_name,
                'source': src_filter,
                'limit': limit,
            }
        },
        'models': filtered,
        'waivers': waivers_list,
    }
    try:
        return json.dumps(result, indent=2)
    except Exception:
        return json.dumps({'error': 'Serialization failure'})

# -----------------------------------------------------------------------------
# Automatic tool registry
# -----------------------------------------------------------------------------
all_tools = [v for k, v in globals().items() if isinstance(v, dict) and k.endswith('_dict')]

def print_all_tools():
    print('=================================================')
    for tool in all_tools:
        print(f"Tool name: {tool['function']['name']}")
        print(f"Tool description: {tool['function']['description']}")
        print(f"Tool parameters: {tool['function']['parameters']}")
        print('=================================================')
