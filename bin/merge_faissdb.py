#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
Confirm Working with :-
- venv: 3.10.11_sles12_cuda
- host: asccf06294100.sc.altera.com

'''
import os
import sys
import logging
import warnings
import argparse
import importlib.util
from pprint import pprint, pformat

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
import lib.regex_db

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

def main(args):

    LOGGER = logging.getLogger(__name__)
    level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.debug(args)

    emb_model = gu.load_default_settings()['emb_model']
    LOGGER.info(f'emb_model: {emb_model}')
    #emb_obj = gu.load_embedding_model(emb_model)
    emb_obj = gu.load_openai_embedding_model()
    vectorstore = gu.load_faiss_dbs(args.input_dbs, emb_obj)
    vectorstore.save_local(args.output_dbs)
    LOGGER.info(f'Output Faiss-db saved to: {args.output_dbs}')

    ### Merging regex db
    rows = gu.load_regex_dbs(args.input_dbs)
    dbname = os.path.join(args.output_dbs, 'regex.db')
    db = lib.regex_db.RegexDB(dbname)
    db.create_table()
    for row in rows:
        db.insert_row(row[1], row[2])
    db.disconnect()
    LOGGER.info(f'Output regex.db saved to: {args.output_dbs}')


if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='merge_faissdb.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    
    parser.add_argument('-i', '--input_dbs', default=None, nargs='+', help='FAISS dbs that will be merged')
    parser.add_argument('-o', '--output_dbs', default=None, help='Output FAISS db')

    args = parser.parse_args()

    main(args)

