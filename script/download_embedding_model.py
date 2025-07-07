#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import os
import sys
import argparse
import logging
#os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
try:
    del os.environ['HF_HUB_OFFLINE']
except:
    pass
try:
    del os.environ['HF_DATASETS_OFFLINE']
except:
    pass

from transformers import AutoTokenizer, AutoModel

LOGGER = logging.getLogger()

def main():
    LOGGER.info('Starting the program')
    args = parse_args()


    '''
    #####################################
    ### This is the old way.
    #####################################
    # Download the model (config.json, model.safetensors)
    m = AutoModel.from_pretrained(args.model_name, local_files_only=False)
    m.save_pretrained(args.output_path)

    # Download the tokenizer (tokenizer_config.json, special_tokens_map.json, sentencepiece.bpe.model, tokenizer.json)
    t = AutoTokenizer.from_pretrained(args.model_name, local_files_only=False)
    t.save_pretrained(args.output_path)
    #####################################
    '''

    #####################################
    ### This is the NEW WAY
    #####################################
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(args.model_name)
    m.save_pretrained(args.output_path)



    print(f'''
Model and tokenizer downloaded to {args.output_path}
To use the model in your code, you can use the following code snippet:
    ``` python
    from langchain_huggingface import HuggingFaceEmbeddings
    m = HuggingFaceEmbeddings(model_name='{args.output_path}', model_kwargs={{'trust_remote_code': True}})
    ```
    ''')



def parse_args():
    parser = argparse.ArgumentParser(description='Download the embedding model')
    parser.add_argument('-m', '--model_name', type=str, help='Model name to download', required=True)
    parser.add_argument('-o', '--output_path', type=str, help='Path to save the model', required=True)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

