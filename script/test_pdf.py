#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
This script demonstrates how to use the RAG model for question answering.
The source of the tutorial is from:
    https://huggingface.co/learn/cookbook/en/rag_zephyr_langchain

Need to re-install this to workaround running in non CUDA environment:
    >pip install --force-reinstall 'https://github.com/bitsandbytes-foundation/bitsandbytes/releases/download/continuous-release_multi-backend-refactor/bitsandbytes-0.44.1.dev0-py3-none-manylinux_2_24_x86_64.whl'
'''
import os
import sys
import logging
import warnings
import re
from pprint import pprint, pformat
import argparse

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)

import lib.genai_utils as gu
import lib.regex_db


gu.proxyon()

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

def main(args):

    if args.debug:
        pprint(args)
   

    LOGGER = logging.getLogger(__name__)
    level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)

    ###############################################
    ### Extract wiki documents
    from langchain_community.document_loaders import ConfluenceLoader, confluence, PyPDFLoader, TextLoader
    from langchain_core.documents import Document

    pdffile = "/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/ShortStories.pdf"
    loader = PyPDFLoader(pdffile)
    documents = loader.load()
    # Add page numbers to metadata
    for i, doc in enumerate(documents):
        doc.metadata["source"] = f"{pdffile}:page{i+1}"
    print(f"Documents length: {len(documents)}")
    '''
    for d in documents[42:55]:
        print(f"Character count: {len(d.page_content)} , Token count: {len(d.page_content)/4}")
        pprint(d)
        print('===============================')
    '''

    ###########################################################################################
    ### Preprocessing for text_splitting operation
    ###########################################################################################
    ### if it is a pdf file that is provided, and the chunking method is not none
    ### then we need to concatenate all the documents into 1 single doc before we split it,
    ### because by default, the PyPDFLoader() splits the pdf into 1 Document() per page.
    args.pdf = True
    args.txtdir = None
    args.method = 'recursive'
    args.chunksize = 500
    args.chunkoverlap = 200
    pagebreak = False
    if args.pdf and args.method != 'none':
        pagebreak = ':::pagebreak{}:::'
        singledoc = Document(page_content='', metadata={'source': pdffile})
        pagenum = 0
        for d in documents:
            pagenum += 1
            singledoc.page_content = singledoc.page_content + d.page_content + pagebreak.format(pagenum)
        documents = [singledoc]


    ### if it is a directory of txtfiles that is provided, and the chunking method is not none
    ### then we need to concatenate all the documents into 1 single doc before we split it,
    ### because by default, each file is being generated into 1 Document().
    if args.txtdir and args.method != 'none':
        singledoc = Document(page_content='', metadata={'source': args.txtdir})
        for d in documents:
            singledoc.page_content = singledoc.page_content + d.page_content
        documents = [singledoc]

    

    ###############################################
    ### Split documents into chunks
    ### For details on more customization, kindly refer to the langchain documentation 
    ### - https://python.langchain.com/v0.1/docs/modules/data_connection/document_transformers/
    if args.method == 'recursive':
        chunk_size = args.chunksize
        chunk_overlap = args.chunkoverlap
        if not chunk_size and not chunk_overlap:
            chunked_docs = documents
        else:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=True)
            chunked_docs = splitter.split_documents(documents)
    
    elif args.method == 'semantic':
        from langchain_experimental.text_splitter import SemanticChunker
        from langchain_community.embeddings import HuggingFaceEmbeddings
        #embeddings = HuggingFaceEmbeddings(model_name=emb_model, model_kwargs={'trust_remote_code': True})
        embeddings = HuggingFaceEmbeddings(model_name=args.emb_model)
        splitter = SemanticChunker(embeddings)
        chunked_docs = splitter.create_documents([documents[0].page_content])

    elif args.method == 'markdown':
        from langchain.text_splitter import MarkdownHeaderTextSplitter
        headers_to_split_on = [
            ('#', 'Header 1'),
            ('##', 'Header 2'),
            ('###', 'Header 3'),
            ('####', 'Header 4'),
        ]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
        chunked_docs = []
        for doc in documents:
            chunked_docs.extend(splitter.split_text(doc.page_content))
   
    else:
        # args.method = None
        chunked_docs = documents


    ### If there is `pagebreak` in the docs, then we need to 
    ### - insert the page number in the `source`
    ### - and remove the `pagebreak` text
    if pagebreak:
        matchstr = pagebreak.format('\d+')
        pagenum = 1
        for doc in chunked_docs:

            ### get the page number from the `pagebreak` text
            m = re.search(matchstr, doc.page_content)
            if m:
                pagenum = re.search('\d+', m.group()).group()

            ### Remove the `pagebreak` text from the page content
            doc.page_content = re.sub(matchstr, '', doc.page_content)
            
            if 'source' in doc.metadata:
                doc.metadata['source'] += f":page{pagenum}"
                print(doc.metadata['source'])

    pprint(chunked_docs)
    sys.exit()


    ###############################################
    ### Save the FAISS (RAG) db
    print("========================================")
    if not args.disable_faissdb:

        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings

        #embeddings = HuggingFaceEmbeddings(model_name=emb_model, model_kwargs={'trust_remote_code': True})
        embeddings = HuggingFaceEmbeddings(model_name=args.emb_model)
        db = FAISS.from_documents(chunked_docs, embeddings)
        faissdb = db
       
        if args.save:
            db.save_local(args.save)
            LOGGER.info(f"FAISS db saved to {args.save}")

    ###############################################
    ### Save regex.db 
    if args.save and not args.disable_regexdb:
        os.system(f"mkdir -p {args.save}")
        dbname = os.path.join(args.save, 'regex.db')
        db = lib.regex_db.RegexDB(dbname)
        db.create_table()

        for doc in chunked_docs:
            text_chunk = doc.page_content
            source = doc.metadata.get('source', 'unknown')
            db.insert_row(text_chunk, source)
        
        db.disconnect()

        print(f"Chunk stored successfully.")


    LOGGER.info("===== DONE =====")
    return faissdb


if __name__ == '__main__':
    settings = gu.load_default_settings()

    parser = argparse.ArgumentParser(prog='extract.py', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    sys.exit(main(args))
