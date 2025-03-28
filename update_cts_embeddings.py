import httpx
import json
import time
import os
from bs4 import BeautifulSoup
import google.generativeai as genai
import numpy as np

# Initialize the models
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
generation_model = genai.GenerativeModel("gemini-1.5-flash")

def tool_to_text(tool):
    """Combine tool name and description into a single text string"""
    name = tool['name']
    desc = tool['description'] if tool['description'] else ""
    # If description is just the name, don't repeat it
    if desc.lower() == name.lower():
        return name
    return f"{name}" + (f" - {desc}" if desc else "")

def embed_tool(tool):
    """Create an embedding for a tool using its name and description"""
    text = tool_to_text(tool)
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text)
    return result['embedding']

def get_show_links_from_page(page_url):
    with httpx.Client() as client:
        r = client.get(page_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        # Each show listing is in a div with class 'audio-comment'
        shows = soup.find_all('div', class_='audio-comment')
        show_links = []
        for show in shows:
            link_tag = show.find('a', href=True, class_='see-all')
            if link_tag:
                show_links.append(link_tag['href'])
        return show_links

def get_all_show_links(start_page=1, end_page=35):
    all_links = []
    for page in range(start_page, end_page+1):
        page_url = f"https://kk.org/cooltools/category/podcast-2/page/{page}/"
        if page == 1:
            page_url = 'https://kk.org/cooltools/category/podcast-2/'
        page_links = get_show_links_from_page(page_url)
        if not page_links:
            # If no links, we might have reached beyond available pages
            break
        all_links.extend(page_links)
    return all_links

def get_page_text(url):
    with httpx.Client() as client:
        r = client.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        # Get only content in body > section > div > div.col-9.content-area > div > div > div.content-body
        content = soup.find('div', class_='content-body')
        if not content:
            return ""
        
        texts = []
        for p in content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a']):
            texts.append(str(p))
        
        return "\n".join(texts)

def get_tools(url):
    text = get_page_text(url)
    
    prompt = """Extract tools mentioned in this podcast transcript. Return in JSON format.
    Use this schema:
    Tool = {{'name': str, 'link': str, 'description': str}}
    Return: list[Tool]

    Text:
    """+text
    
    result = generation_model.generate_content(prompt)
    try:
        # The response usually comes in a code block, so we'll need to parse it
        response_text = result.text
        json_str = response_text.split('```')[1] if '```' in response_text else response_text
        if json_str.startswith('json'):
            json_str = json_str[4:].strip()
        return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing response for {url}: {e}")
        return []

def update_tools_with_embeddings():
    # Load existing data
    existing_tools = []
    existing_urls = set()
    
    try:
        with open('tools_w_embeddings.jsonl', 'r') as f:
            for line in f:
                tool = json.loads(line.strip())
                existing_tools.append(tool)
                existing_urls.add(tool['show_url'])
        print(f"Loaded {len(existing_tools)} existing tools")
    except FileNotFoundError:
        print("No existing data file found. Creating a new one.")
    
    # Get all current show links
    all_show_links = get_all_show_links()
    print(f"Found {len(all_show_links)} total shows")
    
    # Find new shows
    new_show_links = [url for url in all_show_links if url not in existing_urls]
    print(f"Found {len(new_show_links)} new shows to process")
    
    # Process new shows
    new_tools = []
    for i, url in enumerate(new_show_links):
        print(f"Processing {i+1}/{len(new_show_links)}: {url}")
        try:
            tools = get_tools(url)
            print(f"  Found {len(tools)} tools")
            
            # Add show URL and embeddings to each tool
            for tool in tools:
                tool['show_url'] = url
                # Add embedding to the tool
                print(f"  Embedding tool: {tool['name']}")
                tool['embedding'] = embed_tool(tool)
                new_tools.append(tool)
                
                # Save each tool immediately to the file
                with open('tools_w_embeddings.jsonl', 'a') as f:
                    f.write(json.dumps(tool) + '\n')
                
                # Be nice to the embedding API
                time.sleep(0.5)
            
            # Be nice to the server and the generation API
            time.sleep(1)
        except Exception as e:
            print(f"  Error processing {url}: {e}")
    
    print(f"Added {len(new_tools)} new tools to the dataset")
    return new_tools

# Run the update function
if __name__ == "__main__":
    new_tools = update_tools_with_embeddings()
