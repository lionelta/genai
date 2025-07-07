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
import genai_utils as gu


gu.proxyon()

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

def main(args):

    if args.debug:
        pprint(args)
   
    if args.chunksize > 15000:
        raise ValueError("Chunksize cannot be more than 15000")

    LOGGER = logging.getLogger(__name__)
    level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)

    ###############################################
    ### Extract wiki documents
    from langchain_community.document_loaders import ConfluenceLoader, confluence, PyPDFLoader, TextLoader
    from langchain_core.documents import Document

    api_token = open(os.path.join(rootdir, '.wiki_api_token'), 'r').read().strip()

    url = 'https://altera-corp.atlassian.net/wiki'
    keep_markdown = False
    
    if args.method == 'markdown':
        keep_markdown = True

    if args.pageids or args.wikispace:
        loader = ConfluenceLoader(
                url=url, 
                username='yoke.liang.lionel.tan@altera.com', 
                api_key=api_token,
                space_key=args.wikispace,
                #page_ids=['94735727', '94741250', '74294134'],
                #page_ids=['94735506'],
                page_ids=args.pageids,
                content_format=confluence.ContentFormat.VIEW,
                keep_markdown_format=keep_markdown,
                limit=50,
        )
        documents = loader.load()

    elif args.pdf:
        loader = PyPDFLoader(args.pdf)
        documents = loader.load()
   
    elif args.txtdir:
        documents = []
        for root, dirs, files in os.walk(args.txtdir):
            for filename in files:
                filepath = os.path.join(root, filename)
                documents.extend(TextLoader(filepath).load())


    ###########################################################################################
    ### Preprocessing for text_splitting operation
    ###########################################################################################
    ### if it is a pdf file that is provided, and the chunking method is not none
    ### then we need to concatenate all the documents into 1 single doc before we split it,
    ### because by default, the PyPDFLoader() splits the pdf into 1 Document() per page.
    if args.pdf and args.method != 'none':
        singledoc = Document(page_content='', metadata={'source': args.pdf})
        for d in documents:
            singledoc.page_content = singledoc.page_content + d.page_content
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

    print("========================== Chunked Docs ==========================")
    print(documents)
    pprint(chunked_docs)
    print(f"Document count: {len(chunked_docs)}")
    print("==================================================================")

    ###############################################
    ### Create a FAISS vector db
    #from langchain.vectorstores import FAISS
    #from langchain.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings

    #embeddings = HuggingFaceEmbeddings(model_name=emb_model, model_kwargs={'trust_remote_code': True})
    embeddings = HuggingFaceEmbeddings(model_name=args.emb_model)
    db = FAISS.from_documents(chunked_docs, embeddings)


    ###############################################
    ### Save the FAISS (RAG) db
    print("========================================")
    if args.save is not None:
        db.save_local(args.save)
        LOGGER.info(f"FAISS db saved to {args.save}")

    LOGGER.info("===== DONE =====")
    return db


if __name__ == '__main__':
    settings = gu.load_default_settings()

    parser = argparse.ArgumentParser(prog='extract.py', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-cs', '--chunksize', type=int, default=settings['chunksize'], help='Size of each chunk')
    parser.add_argument('-co', '--chunkoverlap', type=int, default=settings['chunkoverlap'], help='Overlap between chunks')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-w', '--wikispace', default=None, help='Wikispace to extract')
    group.add_argument('-p', '--pageids', nargs='*', default=None, help='Page IDs to extract. Eg: --pageids 123 456 777')
    group.add_argument('--pdf', default=None, help='fullpath to pdf file.')
    group.add_argument('--txtdir', default=None, help='the fullpath the the directory that contains all the *.txt files.')

    parser.add_argument('-m', '--method', default='recursive', choices=['recursive', 'semantic', 'markdown', 'none'], help='Method to split text.')
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-s', '--save', default=None, help='The FAISS db name(fullpath) to save to.')
    parser.add_argument('-e', '--emb_model', default=settings['emb_model'], help='Embedding model')
    args = parser.parse_args()
    
    sys.exit(main(args))
