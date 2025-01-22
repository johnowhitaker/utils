import json, os
import numpy as np
import google.generativeai as genai
from fasthtml.common import *

# Configure Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Load tools and embeddings from JSONL
def load_tools():
    all_tools = []
    with open('tools_w_embeddings.jsonl', 'r') as f:
        for line in f:
            all_tools.append(json.loads(line))
    return all_tools
all_tools = load_tools()

# Get all tool embeddings
tool_embeddings = np.array([tool['embedding'] for tool in all_tools])

# Key search function
def search(query, n=10):
    query_embedding = genai.embed_content(model="models/text-embedding-004", content=query)['embedding']
    query_norm = np.array(query_embedding) / np.linalg.norm(query_embedding)
    tool_norms = tool_embeddings / np.linalg.norm(tool_embeddings, axis=1)[:, np.newaxis]
    similarities = np.dot(tool_norms, query_norm)
    results = [(similarities[i], all_tools[i]) for i in np.argsort(similarities)[-n:][::-1]]  
    return results

ar = APIRouter()

@ar('/cts')
def get():
    return Titled(
        "Search 'Cool Tools Show' past recommendations",
        Input(type='search', name='q', placeholder='Search tools...', hx_post='/cts_search', hx_target='#results'),
        Div(id='results'))

@ar('/cts_search')
def post(q:str=''):
    'Return search results'
    if not q: return ''
    print(q)
    results = search(q)
    return Div(*(
        Article(
            H2(f"{r[1]['name']} ({r[0]:.2f})"),
            P(r[1]['description'] or 'No description available'),
            A(f'Show notes ({r[1]['show_url']})', href=r[1]['show_url'], target='_blank'),
            cls='result'
        ) for r in results if r[1]['name']
    ))