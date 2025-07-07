#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import subprocess
import os
import sys
os.environ['OLLAMA_HOST'] = 'asccf06294100.sc.altera.com:11434'

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
from lib.agents.base_agent import BaseAgent
import lib.loading_animation


def get_diff_between_commits(repo_path, commit_hash_1, commit_hash_2):
    """
    Retrieves the diff between two Git commits.

    Args:
        repo_path (str): The path to the Git repository.
        commit_hash_1 (str): The hash of the first commit.
        commit_hash_2 (str): The hash of the second commit.

    Returns:
        str: The diff between the two commits, or None if an error occurs.
    """
    try:
        command = [
            "git",
            "--no-pager",
            "diff",
            "--unified=0",  # Keep context minimal for LLM
            commit_hash_1,
            commit_hash_2,
        ]
        process = subprocess.Popen(command, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=15)
        if process.returncode == 0:
            return stdout.decode("utf-8")
        else:
            print(f"Error getting diff: {stderr.decode('utf-8')}")
            return None
    except FileNotFoundError:
        print("Error: Git command not found. Please ensure Git is installed and in your PATH.")
        return None
    except subprocess.TimeoutExpired:
        print("Error: Git diff command timed out.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def generate_executive_summary(diff_text):
    """
    Generates an executive summary of the Git diff using an LLM.

    Args:
        diff_text (str): The text of the Git diff.
        openai_api_key (str): Your OpenAI API key.

    Returns:
        str: The executive summary of the changes, or None if an error occurs.
    """
    a = BaseAgent()
    prompt = f"""Please provide a concise executive summary of the following changes between two Git commits:

    ```
    {diff_text}
    ```

    Focus on the key changes, their potential impact, and the overall purpose of this set of commits. Keep the summary brief and easy for a non-technical stakeholder to understand."""
    a.kwargs['messages'] = [{"role": "user", "content": prompt}]
    a.kwargs['stream'] = False
    res = a.run()
    '''
    fullres = ''
    for chunk in res:
        print(chunk['message']['content'], end='', flush=True)
        fullres += chunk['message']['content']
    print
    '''
    return res.message['content']


if __name__ == "__main__":
    repo_path = '/nfs/site/disks/da_infra_1/users/yltan/git/baseline_tools/psg/applications.services.design-system.baseline-tools-psg.repo'
    commit_hash_1 = "HEAD^"  # Replace with the first commit hash
    commit_hash_2 = "HEAD"    # Replace with the second commit hash
    openai_api_key = True

    commit_hash_1 = '25.04.018'
    commit_hasn_2 = '25.04.022'

    diff = get_diff_between_commits(repo_path, commit_hash_1, commit_hash_2)

    if diff:
        ani = lib.loading_animation.LoadingAnimation()
        ani.run()
        summary = generate_executive_summary(diff)
        ani.stop()
        if summary:
            print(f"\n--- Executive Summary of Changes between {commit_hash_1} and {commit_hash_2} ---")
            print(summary)
        else:
            print("Failed to generate executive summary.")
    else:
        print("Failed to retrieve the diff between the commits.")






