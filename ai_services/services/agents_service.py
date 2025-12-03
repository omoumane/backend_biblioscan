"""Agent service for resolving OCR text to book titles using LangGraph"""
import os
import sys
import json
from typing import TypedDict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Lazy import for requests
def _import_requests():
    """Lazy import for requests"""
    try:
        import requests
        return requests
    except ImportError as e:
        raise ImportError(f"requests is not installed. Please install it with: pip install requests") from e

# Lazy imports - only import when needed
def _import_langgraph():
    """Lazy import for langgraph"""
    try:
        from langgraph.graph import StateGraph, START, END
        return StateGraph, START, END
    except ImportError as e:
        raise ImportError(f"langgraph is not installed. Please install it with: pip install langgraph") from e

def _import_langchain_openai():
    """Lazy import for langchain_openai"""
    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI
    except ImportError as e:
        raise ImportError(f"langchain-openai is not installed. Please install it with: pip install langchain-openai") from e

def _import_langchain_ollama():
    """Lazy import for langchain_ollama"""
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama
    except ImportError as e:
        raise ImportError(f"langchain-ollama is not installed. Please install it with: pip install langchain-ollama") from e

def _import_langchain_messages():
    """Lazy import for langchain messages"""
    try:
        from langchain_core.messages import HumanMessage
        return HumanMessage
    except ImportError as e:
        raise ImportError(f"langchain-core is not installed. Please install it with: pip install langchain-core") from e


class AgentState(TypedDict):
    """State schema for the book title resolution agent"""
    ocr_text: str  # Input OCR text from OCR service
    resolved_title: str  # Resolved book title
    confidence: float  # Confidence score for the resolution
    reasoning: str  # Reasoning for the resolution
    google_books_found: bool  # Whether the book was found in Google Books
    google_books_info: dict  # Google Books API response information (None if not found)
    google_books_verification: str  # Verification message from Google Books agent


class BookTitleResolverAgent:
    """Agent that resolves OCR text to book titles using LangGraph"""
    
    def __init__(self, llm_provider: str = "openai", model_name: str = None):
        """
        Initialize the agent with an LLM
        
        Args:
            llm_provider: Either "openai" or "ollama"
            model_name: Model name (e.g., "gpt-4", "llama3.2")
        """
        self.llm = self._initialize_llm(llm_provider, model_name)
        self.graph = self._build_graph()
        print(f"✅ BookTitleResolverAgent initialized with {llm_provider}")
    
    def _initialize_llm(self, provider: str, model_name: str):
        """Initialize the LLM based on provider"""
        if provider == "openai":
            # Try to get API key from environment or config
            api_key = os.getenv("OPENAI_API_KEY", getattr(config, "OPENAI_API_KEY", None))
            if not api_key:
                print("⚠️  Warning: OPENAI_API_KEY not found. Using Ollama as fallback.")
                provider = "ollama"
            else:
                # Set environment variable if not already set (for ChatOpenAI to pick up)
                if not os.getenv("OPENAI_API_KEY"):
                    os.environ["OPENAI_API_KEY"] = api_key
                # Use OpenAI with the API key
                ChatOpenAI = _import_langchain_openai()
                model = model_name or "gpt-4o-mini"
                return ChatOpenAI(model=model, temperature=0.7, api_key=api_key)
        
        if provider == "ollama":
            # Default to llama3.2 if no model specified
            ChatOllama = _import_langchain_ollama()
            model = model_name or "llama3.2"
            return ChatOllama(model=model, temperature=0.7)
    
    def _resolve_book_title(self, state: AgentState) -> AgentState:
        """
        Node function that resolves OCR text to a book title
        
        This is the main agent node that processes the OCR text and attempts
        to resolve it to a known book title.
        """
        ocr_text = state.get("ocr_text", "")
        
        if not ocr_text or not ocr_text.strip():
            return {
                "resolved_title": "",
                "confidence": 0.0,
                "reasoning": "No OCR text provided"
            }
        
        # Create a prompt for the LLM to resolve the book title
        prompt = f"""You are a book title resolution expert. Your task is to analyze OCR text extracted from a book spine and resolve it to the most likely book title.

OCR Text: "{ocr_text}"

Instructions:
1. Analyze the OCR text carefully. It may contain errors, missing characters, or formatting issues.
2. Try to identify the actual book title from the OCR text.
3. If you can confidently identify the book title, return it in the format: "Title: [book title]"
4. If the text is unclear or you cannot identify a specific book, return: "Title: [best guess or original text]"
5. Provide a brief reasoning for your resolution.
6. The title should be on the same language of the ocr text

Respond in the following format:
Title: [resolved book title]
Reasoning: [your reasoning]
Confidence: [0.0-1.0]"""
        
        try:
            # Call the LLM
            HumanMessage = _import_langchain_messages()
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            # Parse the response
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract title and reasoning from response
            resolved_title = ""
            reasoning = ""
            confidence = 0.5  # Default confidence
            
            # Simple parsing - look for "Title:" and "Reasoning:" markers
            lines = response_text.split('\n')
            for line in lines:
                if line.strip().startswith('Title:'):
                    resolved_title = line.split('Title:', 1)[1].strip()
                elif line.strip().startswith('Reasoning:'):
                    reasoning = line.split('Reasoning:', 1)[1].strip()
                elif line.strip().startswith('Confidence:'):
                    try:
                        conf_str = line.split('Confidence:', 1)[1].strip()
                        confidence = float(conf_str)
                    except ValueError:
                        pass
            
            # If parsing failed, use the whole response as title
            if not resolved_title:
                resolved_title = response_text.strip()
                reasoning = "Could not parse structured response"
            
            # If still no title, use original OCR text
            if not resolved_title:
                resolved_title = ocr_text
                reasoning = "Could not resolve title, using original OCR text"
                confidence = 0.3
            
            return {
                "resolved_title": resolved_title,
                "confidence": confidence,
                "reasoning": reasoning or "Title resolved from OCR text"
            }
        
        except Exception as e:
            # Fallback to original text if LLM call fails
            print(f"⚠️  Error in LLM call: {e}")
            return {
                "resolved_title": ocr_text,
                "confidence": 0.2,
                "reasoning": f"LLM error: {str(e)}. Using original OCR text."
            }
    
    def _search_google_books(self, state: AgentState) -> AgentState:
        """
        Node function that searches Google Books API for the resolved title
        
        This agent verifies if the resolved book title exists in Google Books,
        which adds confidence to the title resolution.
        """
        resolved_title = state.get("resolved_title", "")
        
        if not resolved_title or not resolved_title.strip():
            return {
                "google_books_found": False,
                "google_books_info": None,
                "google_books_verification": "No title to search in Google Books"
            }
        
        try:
            requests = _import_requests()
            
            # Search Google Books API
            # The API is free and doesn't require authentication for basic searches
            base_url = "https://www.googleapis.com/books/v1/volumes"
            params = {
                "q": f'intitle:"{resolved_title}"',  # Search by title
                "maxResults": 5
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            total_items = data.get("totalItems", 0)
            items = data.get("items", [])
            
            if total_items > 0 and len(items) > 0:
                # Book found! Extract relevant information
                best_match = items[0]  # Take the first result as best match
                volume_info = best_match.get("volumeInfo", {})
                
                # Extract key information
                found_title = volume_info.get("title", "")
                authors = volume_info.get("authors", [])
                published_date = volume_info.get("publishedDate", "")
                description = volume_info.get("description", "")
                page_count = volume_info.get("pageCount", 0)
                categories = volume_info.get("categories", [])
                average_rating = volume_info.get("averageRating", 0)
                ratings_count = volume_info.get("ratingsCount", 0)
                image_links = volume_info.get("imageLinks", {})
                preview_link = volume_info.get("previewLink", "")
                info_link = volume_info.get("infoLink", "")
                
                # Build verification message
                verification_parts = [f"✅ Book found in Google Books!"]
                verification_parts.append(f"Title: {found_title}")
                if authors:
                    verification_parts.append(f"Author(s): {', '.join(authors)}")
                if published_date:
                    verification_parts.append(f"Published: {published_date}")
                if categories:
                    verification_parts.append(f"Categories: {', '.join(categories[:3])}")
                if average_rating > 0:
                    verification_parts.append(f"Rating: {average_rating}/5 ({ratings_count} ratings)")
                
                verification_message = "\n".join(verification_parts)
                
                # Store detailed info
                google_books_info = {
                    "title": found_title,
                    "authors": authors,
                    "published_date": published_date,
                    "description": description[:500] if description else "",  # Truncate long descriptions
                    "page_count": page_count,
                    "categories": categories,
                    "average_rating": average_rating,
                    "ratings_count": ratings_count,
                    "image_links": image_links,
                    "preview_link": preview_link,
                    "info_link": info_link,
                    "total_matches": total_items
                }
                
                # Update confidence based on Google Books verification
                # If found, increase confidence
                current_confidence = state.get("confidence", 0.5)
                updated_confidence = min(1.0, current_confidence + 0.2)  # Boost confidence by 0.2
                
                # Update reasoning to include Google Books verification
                original_reasoning = state.get("reasoning", "")
                updated_reasoning = f"{original_reasoning}\n\n[Google Books Verification] {verification_message}"
                
                return {
                    "google_books_found": True,
                    "google_books_info": google_books_info,
                    "google_books_verification": verification_message,
                    "confidence": updated_confidence,
                    "reasoning": updated_reasoning
                }
            else:
                # Book not found in Google Books
                verification_message = f"⚠️ Book title '{resolved_title}' not found in Google Books. This may indicate:\n- The title is incorrect\n- The book is very rare or not digitized\n- The title needs further refinement"
                
                return {
                    "google_books_found": False,
                    "google_books_info": None,
                    "google_books_verification": verification_message
                }
        
        except Exception as e:
            # Error searching Google Books - don't fail the whole process
            print(f"⚠️  Error searching Google Books: {e}")
            verification_message = f"Could not verify in Google Books: {str(e)}"
            
            return {
                "google_books_found": False,
                "google_books_info": None,
                "google_books_verification": verification_message
            }
    
    def _build_graph(self):
        """Build the LangGraph StateGraph for the agent"""
        # Lazy import
        StateGraph, START, END = _import_langgraph()
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add the resolution node (first agent)
        workflow.add_node("resolve_title", self._resolve_book_title)
        
        # Add the Google Books verification node (second agent)
        workflow.add_node("search_google_books", self._search_google_books)
        
        # Define the flow: START -> resolve_title -> search_google_books -> END
        workflow.add_edge(START, "resolve_title")
        workflow.add_edge("resolve_title", "search_google_books")
        workflow.add_edge("search_google_books", END)
        
        # Compile the graph
        return workflow.compile()
    
    def resolve(self, ocr_text: str) -> dict:
        """
        Main method to resolve OCR text to a book title
        
        Args:
            ocr_text: The OCR text extracted from the book spine
            
        Returns:
            Dictionary containing:
                - resolved_title: The resolved book title
                - confidence: Confidence score (0.0-1.0)
                - reasoning: Reasoning for the resolution
        """
        # Prepare initial state
        initial_state: AgentState = {
            "ocr_text": ocr_text,
            "resolved_title": "",
            "confidence": 0.0,
            "reasoning": "",
            "google_books_found": False,
            "google_books_info": None,
            "google_books_verification": ""
        }
        
        # Invoke the graph
        result = self.graph.invoke(initial_state)
        
        # Return the result with Google Books information
        return {
            "resolved_title": result.get("resolved_title", ""),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", ""),
            "google_books_found": result.get("google_books_found", False),
            "google_books_info": result.get("google_books_info"),
            "google_books_verification": result.get("google_books_verification", "")
        }


# Global agent instance (lazy initialization)
_agent_instance = None


def get_agent(llm_provider: str = None, model_name: str = None) -> BookTitleResolverAgent:
    """
    Get or create the global agent instance
    
    Args:
        llm_provider: LLM provider ("openai" or "ollama"). If None, uses config.LLM_PROVIDER
        model_name: Optional model name override. If None, uses config.LLM_MODEL
        
    Returns:
        BookTitleResolverAgent instance
    """
    global _agent_instance
    # Use config defaults if not provided
    if llm_provider is None:
        llm_provider = config.LLM_PROVIDER
    if model_name is None:
        model_name = config.LLM_MODEL
    
    # Create new instance if doesn't exist or if provider/model changed
    if _agent_instance is None:
        _agent_instance = BookTitleResolverAgent(llm_provider=llm_provider, model_name=model_name)
    return _agent_instance


def resolve_book_title(ocr_text: str, llm_provider: str = None, model_name: str = None) -> dict:
    """
    Convenience function to resolve OCR text to a book title
    
    Args:
        ocr_text: The OCR text extracted from the book spine
        llm_provider: LLM provider ("openai" or "ollama"). If None, uses config.LLM_PROVIDER
        model_name: Optional model name override. If None, uses config.LLM_MODEL
        
    Returns:
        Dictionary with resolved_title, confidence, reasoning, google_books_found,
        google_books_info, and google_books_verification
    """
    # Use config defaults if not provided
    if llm_provider is None:
        llm_provider = config.LLM_PROVIDER
    if model_name is None:
        model_name = config.LLM_MODEL
    
    agent = get_agent(llm_provider=llm_provider, model_name=model_name)
    return agent.resolve(ocr_text)
