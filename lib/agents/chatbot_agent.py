#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''
Documentation:
    https://github.com/ollama/ollama/blob/main/docs/api.md
'''
import os
import sys
import ollama
import re
from pprint import pprint

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
from lib.agents.base_agent import BaseAgent
from lib.regex_db import RegexDB


class ChatbotAgent(BaseAgent):

    def __init__(self):
        super().__init__()

        self.regex_quote = r'<<<(.*?)>>>'

        self.systemprompt = """ You are a helpful and informative assistant. You will be provided with several chunks of information retrieved from various web pages.  These chunks are related to a user's query and are intended to provide context for your response.  **You MUST ONLY use the information provided in these chunks to answer the user's question.** Do not use any other knowledge or information.
Each chunk will be presented in the following format:
Source: https://en.wikipedia.org/wiki/Web_page  
Content: [Text content of the chunk]

The user's query will be provided after all the context chunks.

**Instructions:**

1. **Answer based on provided context:**  Answer the user's question using only the information provided in the context chunks.
2. **Cite sources:** If you use any information from a specific chunk in your answer, cite the source URL only at the very end of the response. Cite each source URL per line. (if there are multiple similar sources, you can cite them only once)
3. **Handle missing information:** If the provided context does not contain the answer to the user's question, respond with: "I'm sorry, but the provided information does not contain the answer to your question."  Do not attempt to answer based on your general knowledge.
4. **Be concise and relevant:**  Keep your answers concise and directly related to the user's question. Avoid unnecessary information or speculation.
5. **Maintain factual accuracy:** Ensure your response is factually accurate based on the provided context. Do not add or infer information that is not explicitly stated in the chunks.

**Context Chunks:**

[Chunk 1 - Example]
Source: https://www.example.com/article1
Content: The capital of France is Paris.  The population of Paris is approximately 2.1 million.

[Chunk 2 - Example]
Source: https://www.example.com/article2
Content:  Paris is located in the Île-de-France region.  It is known for its museums and historical landmarks.

[Chunk 3 - Example]
Source: https://www.example.com/article3
Content:  The Eiffel Tower is a famous landmark in Paris. It was built in 1889.

[Chunk 4 - Example]
Source: https://www.example.com/article4
Content:  The Louvre Museum is another popular attraction in Paris. It houses many famous works of art.

[Chunk 5 - Example]
Source: https://www.example.com/article5
Content:  France is a country in Western Europe. Its official language is French.

**User Query:** What is the population of Paris and where is it located?

**Example Response (using the above example context):**

The population of Paris is approximately 2.1 million. It is located in the Île-de-France region.

Source Of Information:  
1. https://www.example.com/article1  
2. https://www.example.com/article2  
"""

        ### Overriding default settings
        self.kwargs['stream'] = True
        self.kwargs['options']['num_ctx'] = 11111

        self.emb_model = self.default_settings['emb_model']
        self.retrieve_chunks = self.default_settings['retrieve_chunks']
        self.faiss_dbs = []
        self.responsemode = 'Direct'


    def load_rag_data(self):
        embeddings = self.genai_utils.load_embedding_model(self.emb_model)
        rag_content = ''
        rag_content_list = []

        ### Similarity Search RAG data
        if self.faiss_dbs:
            vectorstore = self.genai_utils.load_faiss_dbs(self.faiss_dbs, embeddings)
            retriever = vectorstore.as_retriever(search_type='similarity', search_kwargs={'k': self.retrieve_chunks})

            ### Get the last 3 conversation messages, and send to similarity searcha
            last3chats = self.kwargs['messages'][-3:]
            query = ' '.join([m['content'] for m in last3chats])
            query = self.remove_regex_texts_quotes(query)
            self.logger.debug("simsearch Query: %s", query)
            docs = retriever.invoke(query)
            count = 1
            for d in docs:
                if 'source' in d.metadata:
                    source = d.metadata['source']
                else:
                    source = 'N/A'
                if not self._is_rag_content_already_in_list(rag_content_list, d.page_content):
                    rag_content_list.append(d.page_content)
                    rag_content = self._add_rag_data(count, d.page_content, source, rag_content)
                    count += 1

        ### Regex Search RAG data
        regexs = self.extract_quoted_regex_texts(self.kwargs['messages'][-1]['content']) # only get from last message
        rows = self.genai_utils.load_regex_dbs(self.faiss_dbs)
        if rows and regexs:
            for regex in regexs:
                db = RegexDB()
                matchedrows = db.search(regex, return_count=3, rows=rows)
                for idx, content, source in matchedrows:
                    if not self._is_rag_content_already_in_list(rag_content_list, content):
                        rag_content_list.append(content)
                        rag_content = self._add_rag_data(count, content, source, rag_content)
                        count += 1

        return rag_content


    def _is_rag_content_already_in_list(self, rag_content_list, rag_content):
        for r in rag_content_list:
            if r == rag_content:
                return True
        return False

    def _add_rag_data(self, index, context, source, rag_content):
        return f'''{rag_content}   
[Chunk {index}]  
Source: {source}  
Content: {context}  

'''


    def run(self):
        """ Override default run() , because we need to insert rag data into chat """
        if self.faiss_dbs:
            rag_content = self.load_rag_data()
            self.kwargs['messages'][-1]['content'] = f"""{rag_content}  

**Question:** {self.kwargs['messages'][-1]['content']}
"""
        else:
            self.systemprompt = ''

        # Chain Of Thought
        if self.responsemode == 'CoT':
            self.responsemode_prompt = "Think step by step. Explain each intermediate step. Only when you are done with all your steps, provide the answer based on your intermediate steps."
        # Tree Of Thought
        elif self.responsemode == 'ToT':
            self.responsemode_prompt = 'Imagine three different experts are answering the question. All experts will write down 1 step of their thinking, then share it with the group. Then all experts will go on to the next step, etc. If any expert realises ther are wrong at any point then they leave. Provide the answer based on the steps taken by the experts.'
        else:
            self.responsemode_prompt = ''

        self.kwargs['messages'][-1]['content'] = f"""{self.kwargs['messages'][-1]['content']}      

        {self.responsemode_prompt}
        """
        
        return super().run()


    def extract_quoted_regex_texts(self, text):
        matches = re.findall(self.regex_quote, text)
        return matches


    def remove_regex_texts_quotes(self, text):
        ret = re.sub(self.regex_quote, '\\1', text) 
        return ret


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    a = ChatbotAgent()
    a.kwargs['messages'] = [
        {'role': 'user', 'content': 'how to set a flow to non-gating?'},
        {'role': 'assistant', 'content': '''To set a flow to non-gating, you can edit your `<dut>.design.cfg` file and add the following lines:
```
[<flow_name>__flow]
<task_name> = non-gating
```
Replace `<flow_name>` with the name of the flow you want to set to non-gating (e.g. `sgcdc`, `questa`, `fishtail`, `sgdft`) and `<task_name>` with the specific task within that flow (e.g. `sgcdc_compile`, `sgcdc_run`, `questa_compile`, `questa_elab`).

For example, to set the SGCDC flow to non-gating, you would add:
```
[sgcdc__flow]
sgcdc_compile = non-gating
sgcdc_run = non-gating
```'''},
        {'role': 'user', 'content': 'can you give an example of h2b_package flow?'}
    ]
    a.faiss_dbs = [
        '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/tdmainfra/default',
        '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/psgcth2tfm/default',
    ]
    res = a.run()

    if 'stream' in a.kwargs and a.kwargs['stream']:
        for chunk in res:
            print(chunk['message']['content'], end='', flush=True)
    else:
        pprint(res)
