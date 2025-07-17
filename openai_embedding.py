#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import sys
import os
import subprocess
from pprint import pprint
import logging

sys.path.insert(0, '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main')
import lib.genai_utils as gu

logging.basicConfig(level=logging.DEBUG)

#os.environ['AZURE_OPENAI_API_KEY'] = subprocess.getoutput('/p/psg/da/infra/admin/setuid/goak')
from langchain_openai import AzureOpenAIEmbeddings
import httpx

os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
embeddings = gu.load_openai_embedding_model()
text = 'my name is lionel tan'
v = embeddings.embed_query(text)
pprint(v)
sys.exit()
from langchain_community.vectorstores import FAISS

### Load the first db
db = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/dmx_km_be/default/'
db = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/psgcth2tfm/default/'
vectorstore = FAISS.load_local(db, embeddings, allow_dangerous_deserialization=True)

r = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
prompt = 'how to set a flow to non gating'
docs = r.invoke(prompt)

from pprint import pprint
for d in docs:
    print(d.metadata)
    print(d.page_content)
    print('----------------------------------------------------------')


