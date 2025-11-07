"""
AI Agent Tools Module

This module defines all the tools that the Master Agent can use,
including wrappers for specialized sub-agents.
"""

import json
import requests
from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field
from langchain_community.tools import PubmedQueryRun
from langchain_community.utilities import SerpAPIWrapper
import os

class EximToolInput(BaseModel):
    """Input schema for the EXIM Trade API tool."""
    molecule_name: str = Field(
        ..., 
        description="The specific molecule or API to query, e.g., 'metformin', 'ibuprofen'."
    )

class IqviaToolInput(BaseModel):
    """Input schema for the IQVIA API tool."""
    therapy_area: str = Field(
        ..., 
        description="The specific therapy area to query, e.g., 'respiratory', 'oncology', or 'cardiology'."
    )

class PatentToolInput(BaseModel):
    """Input schema for the Patent Landscape API tool."""
    molecule_name: str = Field(
        ..., 
        description="The specific molecule or drug to query, e.g., 'semaglutide', 'sitagliptin'."
    )

class ClinicalTrialsToolInput(BaseModel):
    """Input schema for the Clinical Trials API tool."""
    molecule_name: str = Field(
        ..., 
        description="The specific molecule or drug to query, e.g., 'pirfenidone', 'semaglutide'."
    )

class KnowledgeToolInput(BaseModel):
    """Input schema for the Internal Knowledge Base API tool."""
    doc_id: str = Field(
        ..., 
        description="The specific document ID to retrieve, e.g., 'STRAT-2024-001' or 'FIELD-2024-Q3'."
    )

@tool(args_schema=EximToolInput)
def get_exim_trade_data(molecule_name: str) -> str:
    """
    Queries the internal EXIM Trade API for a specific molecule.
    Returns a JSON string containing export/import volumes, values,
    key markets, and trade trends.
    """
    # --- IMPORTANT ---
    # This URL must match your Django server's URL
    BASE_URL = "http://127.0.0.1:8000/api/exim-trade/" 
    
    params = {"molecule": molecule_name.lower()}
    
    print(f"--- 🔧 Tool Call: get_exim_trade_data(molecule_name='{molecule_name}') ---")
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        # Raise an exception for bad responses (4xx or 5xx)
        response.raise_for_status() 
        
        # Return the raw JSON text for the agent to process
        return response.text 

    except requests.exceptions.HTTPError as http_err:
        # Handle API-level errors (e.g., 404 Not Found)
        try:
            error_data = http_err.response.json()
            return f"API Error: {http_err.response.status_code} - {json.dumps(error_data)}"
        except json.JSONDecodeError:
            return f"API Error: {http_err.response.status_code} - {http_err.response.text}"
            
    except requests.exceptions.RequestException as e:
        # Handle network/connection errors
        print(f"--- ❌ Tool Error: {e} ---")
        return f"Network Error: Failed to connect to API. {str(e)}"
    
@tool(args_schema=IqviaToolInput)
def get_iqvia_market_data(therapy_area: str) -> str:
    """
    Queries the internal IQVIA Market Intelligence API for a specific therapy area.
    Returns a JSON string containing market size, CAGR, and competitor data.
    """
    # --- IMPORTANT ---
    # Update this URL to match your Django server's address
    BASE_URL = "http://127.0.0.1:8000/api/iqvia/" 
    
    params = {"area": therapy_area.lower()}
    
    print(f"--- 🔧 Tool Call: get_iqvia_market_data(therapy_area='{therapy_area}') ---")
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        # This will raise an exception for 4xx or 5xx errors
        response.raise_for_status() 
        
        # Return the raw JSON text for the agent to process
        return response.text 

    except requests.exceptions.HTTPError as http_err:
        # Handle API-level errors (e.g., 404 Not Found, 400 Bad Request)
        try:
            # Try to return the error JSON from the API
            error_data = http_err.response.json()
            return f"API Error: {http_err.response.status_code} - {json.dumps(error_data)}"
        except json.JSONDecodeError:
            # If the error response isn't JSON
            return f"API Error: {http_err.response.status_code} - {http_err.response.text}"
            
    except requests.exceptions.RequestException as e:
        # Handle network/connection errors
        print(f"--- ❌ Tool Error: {e} ---")
        return f"Network Error: Failed to connect to API. {str(e)}"
    except Exception as e:
        print(f"--- ⚠️ Unexpected Error in get_iqvia_market_data: {e} ---")
        return f"An unexpected error occurred: {str(e)}"
    
@tool(args_schema=PatentToolInput)
def get_patent_landscape_data(molecule_name: str) -> str:
    """
    Queries the internal Patent Landscape API for a specific molecule.
    Returns a JSON string containing patent status, FTO, active patents,
    expiry timelines, and white-space opportunities.
    """
    # --- IMPORTANT ---
    # This URL must match your Django server's URL
    BASE_URL = "http://127.0.0.1:8000/api/patents/" 
    
    params = {"molecule": molecule_name.lower()}
    
    print(f"--- 🔧 Tool Call: get_patent_landscape_data(molecule_name='{molecule_name}') ---")
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status() 
        print(f"--- ✅ Successful Response for '{molecule_name}' ---")
        return response.text 
    except requests.exceptions.HTTPError as http_err:
        print(f"--- ⚠️ HTTP Error while querying {molecule_name}: {http_err} ---")
        try:
            error_data = http_err.response.json()
            print(f"--- 🧾 Error Data: {error_data} ---")
            return f"API Error: {http_err.response.status_code} - {json.dumps(error_data)}"
        except json.JSONDecodeError:
            print(f"--- ❌ Non-JSON API Error Response: {http_err.response.text} ---")
            return f"API Error: {http_err.response.status_code} - {http_err.response.text}"
    except requests.exceptions.RequestException as e:
        print(f"--- ❌ Network Error while fetching {molecule_name}: {e} ---")
        return f"Network Error: Failed to connect to API. {str(e)}"
    except Exception as e:
        print(f"--- ⚠️ Unexpected Error in get_patent_landscape_data: {e} ---")
        return f"An unexpected error occurred: {str(e)}"
    
@tool(args_schema=ClinicalTrialsToolInput)
def get_clinical_trials_data(molecule_name: str) -> str:
    """
    Queries the internal Clinical Trials API for a specific molecule.
    Returns a JSON string containing total/active trial counts,
    details of ongoing trials, sponsor breakdowns, and indication distributions.
    """
    # --- IMPORTANT ---
    # This URL must match your Django server's URL
    BASE_URL = "http://127.0.0.1:8000/api/clinical-trials/" 
    
    params = {"molecule": molecule_name.lower()}
    
    print(f"--- 🔧 Tool Call: get_clinical_trials_data(molecule_name='{molecule_name}') ---")
    
    try:
        print(f"--- 🌐 Sending GET request to {BASE_URL} with params {params} ---")
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        print(f"--- ✅ Successful Response for '{molecule_name}' (Status {response.status_code}) ---")
        return response.text
    except requests.exceptions.HTTPError as http_err:
        print(f"--- ⚠️ HTTP Error while querying {molecule_name}: {http_err} ---")
        try:
            error_data = http_err.response.json()
            print(f"--- 🧾 Error Data: {error_data} ---")
            return f"API Error: {http_err.response.status_code} - {json.dumps(error_data)}"
        except json.JSONDecodeError:
            print(f"--- ❌ Non-JSON API Error Response: {http_err.response.text[:300]} ---")
            return f"API Error: {http_err.response.status_code} - {http_err.response.text}"
    except requests.exceptions.RequestException as e:
        print(f"--- ❌ Network Error while fetching {molecule_name}: {e} ---")
        return f"Network Error: Failed to connect to API. {str(e)}"
    except Exception as e:
        print(f"--- ⚠️ Unexpected Error in get_clinical_trials_data: {e} ---")
        return f"Unexpected error: {str(e)}"
    
@tool(args_schema=KnowledgeToolInput)
def get_internal_document_data(doc_id: str) -> str:
    """
    Queries the internal Knowledge Base API for a specific document ID.
    Returns a JSON string containing the document's metadata and content.
    """
    BASE_URL = "http://127.0.0.1:8000/api/knowledge-base/" 
    params = {"doc_id": doc_id}

    print(f"--- 🔧 Tool Call: get_internal_document_data(doc_id='{doc_id}') ---")
    
    try:
        print(f"--- 🌐 Sending GET request to {BASE_URL} with params {params} ---")
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        print(f"--- ✅ Successful Response for '{doc_id}' (Status {response.status_code}) ---")
        return response.text
    except requests.exceptions.HTTPError as http_err:
        print(f"--- ⚠️ HTTP Error while querying '{doc_id}': {http_err} ---")
        try:
            error_data = http_err.response.json()
            print(f"--- 🧾 Error Data: {error_data} ---")
            return f"API Error: {http_err.response.status_code} - {json.dumps(error_data)}"
        except json.JSONDecodeError:
            print(f"--- ❌ Non-JSON API Error Response: {http_err.response.text[:300]} ---")
            return f"API Error: {http_err.response.status_code} - {http_err.response.text}"
    except requests.exceptions.RequestException as e:
        print(f"--- ❌ Network Error while fetching document '{doc_id}': {e} ---")
        return f"Network Error: Failed to connect to API. {str(e)}"
    except Exception as e:
        print(f"--- ⚠️ Unexpected Error in get_internal_document_data: {e} ---")
        return f"Unexpected error: {str(e)}"

pubmed_api = PubmedQueryRun()
search = SerpAPIWrapper(serpapi_api_key=os.getenv("SERPAPI_API_KEY"))


@tool
def pubmed_search(query: str) -> str:
    """
    Searches PubMed for biomedical literature and scientific studies.
    Returns a formatted string of article summaries and metadata.
    """
    print(f"--- 🔍 Tool Invoked: pubmed_search(query='{query}') ---")
    try:
        print("--- 🌐 Connecting to PubMed API ---")
        result = pubmed_api.invoke(query)
        print(f"--- ✅ PubMed Search Successful (Query='{query}') ---")
        return result
    except Exception as e:
        print(f"--- ❌ Error during PubMed search: {e} ---")
        return f"Error during PubMed search: {e}"
@tool
def web_search(query: str) -> str:
    """
    Perform a real web search using SerpAPI.
    Use this to find current news, research, or guidelines from the web.
    """
    print(f"--- 🛠️ EXECUTING (REAL): web_search(query='{query}') ---")
    return search.run(query)


# @tool
# def web_search(query: str) -> str:
#     """
#     Performs a SerpAPI-powered web search for general information,
#     news, and reports. Returns formatted snippets with URLs.
#     """
#     print(f"--- 🌎 Tool Invoked: web_search(query='{query}') ---")
#     try:
#         print("--- ⚙️ Executing SerpAPI simulated web search ---")
#         # Placeholder for actual API logic
#         return (
#             f"SerpAPI results for '{query}': Paracetamol (acetaminophen) remains "
#             f"widely used for fever and pain relief. Global use stable, safety confirmed "
#             f"in 2024 review (≤4g/day)."
#         )
#     except Exception as e:
#         print(f"--- ❌ Error during web search: {e} ---")
#         return f"Error during web search: {e}"
# @tool
# def web_search(query: str) -> str:
#     """
#     Perform a real web search using SerpAPI. Use this to find current news,
#     articles, guidelines, or patient perspectives from the internet.
#     """
#     print(f"--- 🛠️ EXECUTING (REAL): web_search(query='{query}') ---")
#     # No try/except block here. Let the invoke method handle it.
#     return search.run(query)
# pubmed_api = PubmedQueryRun()
# search_api = SerpAPIWrapper()

TOOL_REGISTRY = {
    "get_exim_trade_data": get_exim_trade_data,
    "get_iqvia_market_data": get_iqvia_market_data,
    "get_patent_landscape_data": get_patent_landscape_data,
    "get_clinical_trials_data": get_clinical_trials_data,
    "get_internal_document_data": get_internal_document_data,
    "pubmed_search": pubmed_search,
    "web_search": web_search,
}

