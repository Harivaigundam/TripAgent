from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

def tavily_search(query):
    response = client.search(
        query=query,
        max_results=5
    )
    
    results=[]
    for i, r in enumerate(response["results"], 1):
        
        title = r.get("title", "unknown")
        url = r.get("url", "unknown")
        snippet = r.get("content", "unknown").strip()
        
        if len(snippet) > 200:
            snippet = snippet[:200].rsplit(" ", 1)[0] + "..."
            
        results.append(f"{i}. {title}\n URL: {url}\nSnippet: {snippet}\n")
        
    return "\n\n".join(results)
    