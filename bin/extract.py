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

    os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'

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

    if args.pageids or args.wikispaces:
        # Replace the ConfluenceLoader with our own customzed loader
        from lib.document_loaders.confluence_loader import ConfluenceLoader
        loader = ConfluenceLoader()
        loader.pageids = args.pageids if args.pageids else []
        loader.spaces = args.wikispaces if args.wikispaces else []
        loader.savedir = args.save if args.save else None
        documents = loader.load()
        print(f"Document count before filtering: {len(documents)}")

        ### Remove documents that has 'deprecated' in the title
        filtered_documents = [d for d in documents if re.search('(?i)deprecated', d.metadata.get('title', ''))]
        documents = [d for d in documents if not re.search('(?i)deprecated', d.metadata.get('title', ''))]
        
        # print out the title of filtered_documents for debugging
        print("========================================================")
        print("Filtered documents:")
        for i, d in enumerate(filtered_documents):
            print(f"{i+1}. {d.metadata.get('title', 'No Title')} (ID: {d.metadata.get('id', 'No ID')})")
        print("========================================================")
        print(f"Document count: {len(documents)}")
        print(f"Filtered Document count: {len(filtered_documents)}")

    elif args.pdf:
        loader = PyPDFLoader(args.pdf)
        documents = loader.load()
        # Add page numbers to metadata
        for i, doc in enumerate(documents):
            if args.source is None:
                doc.metadata['source'] = f"{args.pdf}:page{i+1}"
            else:
                doc.metadata['source'] = f"{args.source}:page{i+1}"

    elif args.txtdir:
        documents = []
        for root, dirs, files in os.walk(args.txtdir):
            for filename in files:
                filepath = os.path.join(root, filename)
                documents.extend(TextLoader(filepath).load())

    elif args.txt:
        filepath = os.path.abspath(args.txt)
        documents = TextLoader(filepath).load()
        for doc in documents:
            if args.source is None:
                doc.metadata['source'] = f"{filepath}"
            else:
                doc.metadata['source'] = f"{args.source}"

    elif args.msftx:
        from lib.document_loaders.msftx_loader import MsftxLoader
        loader = MsftxLoader()
        loader.msftxfile = args.msftx
        loader.savedir = args.save if args.save else None
        documents = loader.load()
        if args.source is not None:
            for doc in documents:
                doc.metadata['source'] = args.source

    ###########################################################################################
    ### Preprocessing for text_splitting operation
    ###########################################################################################
    ### if it is a pdf file that is provided, and the chunking method is not none
    ### then we need to concatenate all the documents into 1 single doc before we split it,
    ### because by default, the PyPDFLoader() splits the pdf into 1 Document() per page.
    pagebreak = False
    if args.pdf and args.method != 'none':
        pagebreak = ':::pagebreak{}:::'
        singledoc = Document(page_content='', metadata={'source': args.pdf})
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
        #embeddings = HuggingFaceEmbeddings(model_name=args.emb_model)
        embeddings = gu.load_openai_embedding_model()
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

    ### if there is `pagebreak` in the doc, then we need to
    ### - insert the page number into the `source`
    ### - remove the pagebreak from the text
    if pagebreak:
        matchstr = pagebreak.format('\d+')
        pagenum = 1
        for doc in chunked_docs:

            ### Get the page number from the `pagebreak` text
            m = re.search(matchstr, doc.page_content)
            if m:
                pagenum = re.search('\d+', m.group()).group()

            ### Remove the pagebreak text from the doc
            doc.page_content = re.sub(matchstr, '', doc.page_content)

            if 'source' in doc.metadata:
                ### If the source is already set, append the page number
                if args.source is None:
                    doc.metadata['source'] = f"{doc.metadata['source']}:page{pagenum}"
                else:
                    doc.metadata['source'] = f"{args.source}:page{pagenum}"


    print("========================== Chunked Docs ==========================")
    #print(documents)
    #pprint(chunked_docs)
    print(f"Document count: {len(chunked_docs)}")
    print("==================================================================")


    ###############################################
    ### Save the FAISS (RAG) db
    print("========================================")
    if not args.disable_faissdb:

        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings

        #embeddings = HuggingFaceEmbeddings(model_name=emb_model, model_kwargs={'trust_remote_code': True})
        #embeddings = HuggingFaceEmbeddings(model_name=args.emb_model)
        embeddings = gu.load_openai_embedding_model()

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
    parser.add_argument('-cs', '--chunksize', type=int, default=settings['chunksize'], help='Size of each chunk')
    parser.add_argument('-co', '--chunkoverlap', type=int, default=settings['chunkoverlap'], help='Overlap between chunks')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-w', '--wikispaces', nargs='*', default=None, help='Wikispace(s) to extract')
    group.add_argument('-p', '--pageids', nargs='*', default=None, help='''Page IDs to extract. Eg: --pageids 123 +456 -777.
If the page ID starts with a + (eg: +123), all children pages including itself will be extracted.
If the page ID starts with a - (eg: -123), it will be excluded.
If the page ID is just a number (eg: 123), only that page itself will be extracted.
    ''')
    group.add_argument('--pdf', default=None, help='fullpath to pdf file.')
    group.add_argument('--txtdir', default=None, help='the fullpath the the directory that contains all the *.txt files.')
    group.add_argument('--txt', default=None, help='the text or MD file.')
    group.add_argument('--msftx', default=None, help='fullpath to msftx file. Currently only supports .docx and .pptx')


    parser.add_argument('-m', '--method', default='recursive', choices=['recursive', 'semantic', 'markdown', 'none'], help='Method to split text.')
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-s', '--save', default=None, help='The FAISS db name(fullpath) to save to.')
    parser.add_argument('-e', '--emb_model', default=settings['emb_model'], help='Embedding model')

    parser.add_argument('--disable_faissdb', action='store_true', default=False, help='Disable FAISS db creation')
    parser.add_argument('--disable_regexdb', action='store_true', default=False, help='Disable regex db creation')
    parser.add_argument('--source', default=None, help='Override the metadata with this given Source path. If not provided, will use the default source path.')
    args = parser.parse_args()
    
    sys.exit(main(args))
