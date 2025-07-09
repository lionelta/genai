#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''
Documentation:
    https://github.com/ollama/ollama/blob/main/docs/api.md

Usage:
    
    from lib.agents.sql_coding_agent import CodingAgent
    a = CodingAgent()

    ### Override default settings, if needed
    a.kwargs['model'] = 'qwen2.5'
    a.kwargs['options']['top_p'] = 1.0
    a.kwargs['stream'] = False

    ### Provide required input
    a.cnffile = <path to sql cnf file>
    a.tables = [<list of sql tables>]
    a.kwargs['messages'] = [{'role': 'user', 'content': <user query>}]
    res = a.run()
    
    ### if you want to execute the sql command
    rawsqlcmd = res.message['content']
    output = a.execute_sql(rawsqlcmd)

Example of sql cnf file:
=========================
[client]
host=ascyv0123.sc.altera.com
port=3306
user=user_ro
password=pswrd_ro
database=syncpoint

'''
import os
import sys
import ollama
import logging
from pprint import pprint, pformat
import subprocess

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
from lib.agents.base_agent import BaseAgent



class SqlCodingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
     
        self.sqlexe = 'mysql'

        ### input that requires to be passed to the agent
        self.cnffile = None
        self.tables = []

        ### llm settings for this agent
        self.kwargs['stream'] = False
        self.kwargs['options']['num_ctx'] = 11111
        self.kwargs['options']['temperature'] = 0.3
        self.kwargs['options']['top_p'] = 0.3
        self.systemprompt = '''You are an expert in mysql. Help me to write a mysql query. I will provide you with the create table statement and the query I want to write. You will help me to write the query.  Do not give me any explanation or any other information. Just response with the SQL command directly. Do not format the SQL command using markdown or triple backticks. Do not put any newline character. Return it as plain text.   

        {table_schemas}   
        '''
        self.table_schemas = ''

    def execute_sql(self, sql_command):
        cmd = self.get_sql_command(sql_command)
        self.logger.debug(f'Executing SQL command: {cmd}')
        output = subprocess.getoutput(cmd)
        return output

    def run(self):
        kwargs = self.kwargs.copy()
        self.table_schemas = self.get_create_table_statements()
        kwargs['messages'].insert(0, {'role': 'system', 'content': self.systemprompt.format(table_schemas=self.table_schemas)})
        self.logger.debug(pformat(kwargs))
        res = self.chat_factory.chat(kwargs)
        return res

    def get_create_table_statements(self):
        ret = ''
        for table in self.tables:
            sqlcmd = f'show create table {table}'
            cmd = self.get_sql_command(sqlcmd) + ' | tail -n1'
            output = subprocess.getoutput(cmd)
            ret += f"\n\n**Create Table Statement: {table}**: {output}\n\n  "
        return ret
    
    def get_sql_command(self, sql_command):
        cmd = "{} --defaults-file={} -se {}".format(self.sqlexe, self.cnffile, gu.quotify(sql_command))
        return cmd 

if __name__ == '__main__':
    ### To run: 
    ###     >env OLLAMA_HOST=asccf06294100.sc.altera.com:11434 ./sql_coding_agent.py
    logging.basicConfig(level=logging.DEBUG)
    a = SqlCodingAgent()
    a.cnffile = os.path.join(rootdir, 'sql_cnf_files', 'syncpoint.cnf')
    a.tables = ['syncpoint_syncpoint', 'syncpoint_release']
    a.kwargs['stream'] = False
    a.kwargs['messages'] = [
        {'role': 'user', 'content': sys.argv[1]} # 'write a query to get the latest release for each syncpoint',
    ] 
    a.kwargs['stream'] = False
    res = a.run()
    pprint(res)
    print(res.message['content'])

    cmd = a.get_sql_command(res.message['content'])
    print(cmd)
    os.system(cmd)
