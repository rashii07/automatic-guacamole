"""
AI Research Agent MVP
A simplified research tool that performs web searches, extracts content, and generates summaries with citations.
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from typing import List, Dict, Tuple
import os
from urllib.parse import urlparse
import time

class ResearchAgent:
    """Core research agent that handles search, extraction, and summarization."""
    
    def __init__(self, search_api_key: str = None, openai_api_key: str = None):
        """
        Initialize the research agent with API keys.
        
        Args:
            search_api_key: API key for search service (SerpAPI or similar)
            openai_api_key: API key for OpenAI
        """
        self.search_api_key = search_api_key or os.getenv('SEARCH_API_KEY')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    def search_web(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Perform a web search and return top results.
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            List of search results with title and URL
        """
        # For MVP, using a mock search or free API
        # Replace with actual SerpAPI or similar service
        
        # Example using SerpAPI (requires API key)
        if self.search_api_key:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.search_api_key,
                "num": num_results
            }
            
            try:
                response = requests.get(url, params=params)
                data = response.json()
                
                results = []
                for item in data.get("organic_results", [])[:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
                return results
            except Exception as e:
                st.error(f"Search API error: {e}")
                return []
        
        # Fallback mock data for demo purposes
        return [
            {
                "title": f"Sample Result {i+1} for: {query}",
                "url": f"https://example{i+1}.com/article",
                "snippet": f"This is a sample snippet about {query}..."
            }
            for i in range(min(3, num_results))
        ]
    
    def extract_content(self, url: str) -> Tuple[str, str]:
        """
        Extract main text content from a URL.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Tuple of (title, content)
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.text.strip() if title else urlparse(url).netloc
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Extract main content - try common content containers
            content = ""
            content_tags = soup.find_all(['article', 'main', 'div'], class_=['content', 'article-body', 'post-content'])
            
            if content_tags:
                content = ' '.join([tag.get_text(strip=True, separator=' ') for tag in content_tags])
            else:
                # Fallback to paragraphs
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs[:20]])  # Limit to first 20 paragraphs
            
            # Clean up content
            content = ' '.join(content.split())  # Remove extra whitespace
            content = content[:3000]  # Limit content length for MVP
            
            return title_text, content
            
        except Exception as e:
            return urlparse(url).netloc, f"Error extracting content: {str(e)}"
    
    def generate_summary(self, sources: List[Dict[str, str]], query: str) -> str:
        """
        Generate a summary using LLM based on extracted content.
        
        Args:
            sources: List of dictionaries with 'title', 'url', and 'content'
            query: Original research query
            
        Returns:
            Generated summary with inline citations
        """
        if not sources:
            return "No content available to summarize."
        
        # Prepare content for LLM
        combined_content = "\n\n".join([
            f"Source {i+1} ({source['title']}):\n{source['content'][:1000]}"
            for i, source in enumerate(sources)
        ])
        
        prompt = f"""Based on the following sources about "{query}", create a concise summary.
        Include inline citations using [Source N] format where N is the source number.
        
        Sources:
        {combined_content}
        
        Summary (with citations):"""
        
        # Use OpenAI API if available
        if self.openai_api_key:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a research assistant that creates concise, well-cited summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                st.error(f"OpenAI API error: {e}")
        
        # Fallback summary for demo
        summary = f"Based on the search for '{query}', here are the key findings:\n\n"
        for i, source in enumerate(sources):
            summary += f"• {source['title']} discusses aspects related to {query} [Source {i+1}]\n"
        summary += f"\nThese sources provide various perspectives on {query}."
        
        return summary
    
    def research(self, query: str) -> Dict:
        """
        Complete research pipeline: search, extract, summarize.
        
        Args:
            query: Research query
            
        Returns:
            Dictionary with summary and sources
        """
        # Step 1: Search
        search_results = self.search_web(query, num_results=3)
        
        if not search_results:
            return {
                "summary": "No search results found.",
                "sources": []
            }
        
        # Step 2: Extract content
        sources = []
        for result in search_results:
            title, content = self.extract_content(result['url'])
            sources.append({
                "title": title or result['title'],
                "url": result['url'],
                "content": content
            })
            time.sleep(0.5)  # Be respectful to servers
        
        # Step 3: Generate summary
        summary = self.generate_summary(sources, query)
        
        return {
            "summary": summary,
            "sources": sources
        }

def main():
    """Streamlit UI for the Research Agent MVP."""
    
    st.set_page_config(page_title="AI Research Agent MVP", page_icon="🔍")
    
    st.title("🔍 AI Research Agent MVP")
    st.markdown("Enter a research topic to get an AI-generated summary with sources.")
    
    # Sidebar for API keys (optional)
    with st.sidebar:
        st.header("Configuration")
        st.markdown("Optional: Add API keys for enhanced functionality")
        
        search_api = st.text_input("Search API Key (SerpAPI)", type="password", 
                                   help="Get from serpapi.com")
        openai_api = st.text_input("OpenAI API Key", type="password",
                                   help="Get from platform.openai.com")
        
        st.markdown("---")
        st.markdown("**Note:** The MVP works with mock data if no API keys are provided.")
    
    # Initialize agent
    agent = ResearchAgent(search_api_key=search_api, openai_api_key=openai_api)
    
    # Main interface
    query = st.text_input("Enter your research query:", 
                         placeholder="e.g., 'latest developments in quantum computing'")
    
    if st.button("Research", type="primary"):
        if query:
            with st.spinner("🔍 Searching the web..."):
                results = agent.research(query)
            
            # Display summary
            st.header("📊 Summary")
            st.markdown(results["summary"])
            
            # Display sources
            st.header("📚 Sources")
            for i, source in enumerate(results["sources"], 1):
                with st.expander(f"Source {i}: {source['title']}"):
                    st.markdown(f"**URL:** {source['url']}")
                    st.markdown(f"**Extract:** {source['content'][:500]}...")
        else:
            st.warning("Please enter a research query.")
    
    # Footer
    st.markdown("---")
    st.markdown("**MVP Features:** Web search • Content extraction • AI summarization • Source citations")

if __name__ == "__main__":
    main()