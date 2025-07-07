import os
import json
if 'OLLAMA_HOST' not in os.environ:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'genai_default_settings.json'), 'r') as f:
        settings = json.load(f)
        ollama_host = settings.get('ollama_host', 'http://localhost:11434')
        os.environ['OLLAMA_HOST'] = ollama_host
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
