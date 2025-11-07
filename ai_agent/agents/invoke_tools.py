import requests
import json
import os
import re
from pydantic.v1 import BaseModel, Field
from langchain_core.tools import tool
from langchain_community.tools.pubmed.tool import PubmedQueryRun
from .tools import *
from .. import services
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def get_agent(agent_name: str):
    """
    Diagnostic loader: imports ai_agent.agents.all_agents and prints full traceback
    if anything goes wrong. Returns the requested agent object or None.
    """
    import importlib, traceback, sys, os
    try:
        all_agents = importlib.import_module("ai_agent.agents.all_agents")
    except Exception as e:
        # Print full traceback to stdout/stderr so server log captures it
        print("\n--- ❌ Failed to import ai_agent.agents.all_agents ---", file=sys.stderr)
        traceback.print_exc()
        # Also write to a file for convenience
        try:
            with open(os.path.join(os.getcwd(), "all_agents_import_error.log"), "w") as fh:
                fh.write("Failed to import ai_agent.agents.all_agents\n\n")
                import traceback as _tb
                _tb.print_exc(file=fh)
        except Exception:
            pass
        return None

    # Try to find the attribute on the module robustly
    # Print what attributes look like candidates
    candidates = [n for n in dir(all_agents) if n.endswith("_agent") or n.endswith("Agent")]
    print(f"--- ✅ ai_agent.agents.all_agents imported. Candidate attributes: {candidates}")

    # Map expected names to attributes (case-sensitive)
    mapping = {
        "internal_agent": getattr(all_agents, "internal_agent", None),
        "exim_agent": getattr(all_agents, "exim_agent", None),
        "clinical_trials_agent": getattr(all_agents, "clinical_trials_agent", None),
        "patent_agent": getattr(all_agents, "patent_agent", None),
        "web_agent": getattr(all_agents, "web_agent", None),
        "iqvia_agent": getattr(all_agents, "iqvia_agent", None),
        "report_agent": getattr(all_agents, "report_agent", None),
        "master_agent": getattr(all_agents, "master_agent", None),
    }
    agent = mapping.get(agent_name)
    if agent is None:
        print(f"--- ⚠️ Requested agent '{agent_name}' not found. Available keys: {list(mapping.keys())}; module candidates: {candidates}")
    else:
        print(f"--- ✅ Found agent for '{agent_name}': {agent}")
    return agent


# def get_agent(agent_name: str):
#     """
#     Lazily import ai_agent.agents.all_agents and return a specific agent instance.

#     Accepts common agent_name strings used across the project, e.g.:
#       - "internal_agent"
#       - "exim_agent"
#       - "clinical_trials_agent"
#       - "patent_agent"
#       - "web_intelligence_agent"
#       - "iqvia_agent"
#       - "report_agent"
#       - "master_agent"

#     Returns the agent object or None if not found / import error.
#     """
#     import importlib
#     try:
#         import importlib
#         # Import the all_agents module fresh (safe to cache if desired)
#         all_agents = importlib.import_module("ai_agent.agents.all_agents")

#         # Map requested names to attributes on the module
#         lookup = {
#             "internal_agent": getattr(all_agents, "internal_agent", None),
#             "exim_agent": getattr(all_agents, "exim_agent", None),
#             "clinical_trials_agent": getattr(all_agents, "clinical_trials_agent", None),
#             "patent_agent": getattr(all_agents, "patent_agent", None),
#             "web_intelligence_agent": getattr(all_agents, "web_intelligence_agent", None),
#             "iqvia_agent": getattr(all_agents, "iqvia_agent", None),
#             "report_agent": getattr(all_agents, "report_agent", None),
#             "master_agent": getattr(all_agents, "master_agent", None),
#         }

#         agent = lookup.get(agent_name)
#         if agent is None:
#             # Helpful debugging print so logs show what went wrong
#             print(f"--- ⚠️ Requested agent '{agent_name}' not found in ai_agent.agents.all_agents ---")
#         return agent

#     except Exception as e:
#         # If the import of all_agents fails (e.g., missing env / settings error),
#         # report it clearly so the log points to the real startup problem.
#         print(f"--- ❌ Error importing ai_agent.agents.all_agents: {type(e).__name__}: {e} ---")
#         return None


@tool
def invoke_exim_trade_agent(query: str) -> str:
    """
    Invokes the specialized EXIM Trends Agent for global pharmaceutical trade data.
    
    This agent provides comprehensive export-import (EXIM) trade intelligence
    for pharmaceutical Active Pharmaceutical Ingredients (APIs) and finished
    formulations. Use this tool for any queries about:
    
    **API Export Data:**
    - Export volumes (metric tons) and values (USD millions) by country
    - Market share of key API exporters (India, China, Germany)
    - Average API pricing per kilogram
    - Top destination markets for API exports
    - Year-over-year (YoY) growth trends
    
    **Formulation Import Data:**
    - Import volumes and values for finished pharmaceutical products
    - Import dependency percentages by country
    - Top source countries for formulation imports
    - Regional trade flow patterns
    
    **Trade Trends & Forecasts:**
    - Market dynamics (e.g., US-China trade tensions, quality concerns)
    - Emerging sourcing patterns and supply chain shifts
    - 3-year CAGR forecasts (2024-2026)
    - Impact of geopolitical factors on trade
    
    **Competitive Sourcing Intelligence:**
    - Price competitiveness analysis across geographies
    - Quality perception and regulatory compliance issues
    - Strategic sourcing opportunities
    
    Args:
        query (str): A natural language query about trade data for a specific molecule.
                     The agent will extract the molecule name and retrieve all
                     relevant EXIM data.
                     Examples: "What is the import-export data for metformin?"
                              "Which countries export the most pirfenidone?"
                              "What are the trade trends for atorvastatin?"
    
    Returns:
        str: A JSON string containing:
             - 'analysis': Natural language summary of trade flows and trends
             - 'raw_data': Full EXIM dataset including volumes, values, market shares,
                          top destinations/sources, and forecasts
    """
    print(f"\n--- 🌍 Invoking EXIM Trade Agent ---")
    agent = get_agent("exim_agent")
    exim_agent = agent
    print(f"Query: {query}")
    if exim_agent is None:
        print("--- ⚠️ EXIM Agent not initialized ---")
        return json.dumps({
            "analysis": "Error: The EXIM Trends Agent is not initialized.",
            "raw_data": {"error": "Agent not initialized"}
        })
    try:
        print("--- 🚀 Executing exim_agent.invoke() ---")
        result = exim_agent.invoke(query)
        print("--- ✅ EXIM Agent Execution Successful ---")
        return json.dumps(result)
    except Exception as e:
        print(f"--- ❌ Error during EXIM Agent execution: {e} ---")
        return json.dumps({
            "analysis": f"Error during EXIM Trends Agent invocation: {e}",
            "raw_data": {"error": str(e)}
        })


@tool
def iqvia_insights(query: str) -> str:
    """
    Invokes the specialized IQVIA Insights Agent for pharmaceutical market intelligence.
    
    This agent provides comprehensive market data based on IQVIA's proprietary
    global pharmaceutical intelligence. IQVIA is the world's leading provider
    of healthcare market data, tracking prescriptions, sales, and market trends
    across all major markets. Use this tool for any queries about:
    
    **Market Size & Growth:**
    - Global and regional market size (USD billions)
    - Compound Annual Growth Rate (CAGR) forecasts
    - Therapy area market valuations
    - Disease-specific market segments
    
    **Competitive Landscape:**
    - Market share analysis by company
    - Top-selling drugs and brands by indication
    - Competitor positioning and strategic focus
    - Emerging players and disruptors
    
    **Therapy Area Intelligence:**
    - Respiratory diseases (COPD, asthma, IPF, bronchiectasis)
    - Cardiovascular diseases (heart failure, hypertension, AF)
    - Diabetes and metabolic disorders (T2D, obesity, NASH)
    - Oncology (lung, breast, multiple myeloma)
    - Neurology (Alzheimer's, Parkinson's, MS)
    - Immunology (RA, psoriasis, IBD)
    
    **Disease Landscape Data:**
    - Patient prevalence, diagnosis rates, and treatment rates
    - Unmet medical needs and treatment gaps
    - Clinical pipeline and emerging therapies
    - Payer and reimbursement trends
    
    **Regional Market Insights:**
    - United States, Europe (EU5), China, Japan, India
    - Regulatory and pricing dynamics by geography
    - Market access and HTA (Health Technology Assessment) hurdles
    
    Args:
        query (str): A natural language query about market data for a specific
                     therapy area or disease.
                     Examples: "What is the market size for respiratory diseases?"
                              "Tell me about the oncology competitive landscape"
                              "What is the CAGR for diabetes drugs?"
    
    Returns:
        str: A JSON string containing:
             - 'analysis': Natural language synthesis of market intelligence
             - 'raw_data': Full IQVIA dataset including market size, CAGR,
                          competitor shares, disease breakdowns, and regional data
    """
    print(f"\n--- 📊 Invoking IQVIA Insights Agent ---")
    iqvia_agent = get_agent("iqvia_agent")
    if iqvia_agent is None:
        return "--- ⚠️ IQVIA Agent not initialized ---"
    print(f"Query: {query}")
    if iqvia_agent is None:
        print("--- ⚠️ IQVIA Agent not initialized ---")
        return json.dumps({
            "analysis": "Error: The IQVIA Insights Agent is not initialized.",
            "raw_data": {"error": "Agent not initialized"}
        })
    try:
        print("--- 🚀 Executing iqvia_agent.invoke() ---")
        result = iqvia_agent.invoke(query)
        print("--- ✅ IQVIA Agent Execution Successful ---")
        return json.dumps(result)
    except Exception as e:
        print(f"--- ❌ Error during IQVIA Insights Agent execution: {e} ---")
        return json.dumps({
            "analysis": f"Error during IQVIA Insights Agent invocation: {e}",
            "raw_data": {"error": str(e)}
        })


@tool
def invoke_patent_landscape_agent(query: str) -> str:
    
    """
    Invokes the specialized Patent Landscape Agent for intellectual property analysis.
    
    This agent provides comprehensive patent intelligence and Freedom-to-Operate
    (FTO) analysis for pharmaceutical molecules. Use this tool for any queries about:
    
    **Patent Status & Expiry:**
    - Composition of Matter (COM) patent status and expiry dates
    - Method of Use (MOU) patent timelines for specific indications
    - Formulation patent coverage and exclusivity periods
    - Patent term extensions (PTE) and pediatric exclusivity
    
    **Freedom-to-Operate (FTO) Analysis:**
    - Risk assessment for generic entry (low, medium, high, or blocked)
    - Active patent barriers and litigation status
    - Paragraph IV (P-IV) challenge opportunities
    - Non-infringing design-around strategies
    
    **Intellectual Property Strategy:**
    - White space opportunities for new indications or formulations
    - Patent cliff timelines and generic entry windows
    - Orange Book listings and patent estate analysis
    - Biosimilar and 505(b)(2) pathway opportunities
    
    **Competitive Patent Landscape:**
    - Innovator patent strategies and patent thickets
    - Third-party blocking patents
    - Patent family analysis across geographies
    """
    print(f"\n--- 🧾 Invoking Patent Landscape Agent ---")
    patent_agent = get_agent("patent_agent")
    print(f"Query: {query}")
    if patent_agent is None:
        print("--- ⚠️ Patent Agent not initialized ---")
        return json.dumps({
            "analysis": "Error: The Patent Landscape Agent is not initialized.",
            "raw_data": {"error": "Agent not initialized"}
        })
    try:
        print("--- 🚀 Executing patent_agent.invoke() ---")
        result = patent_agent.invoke(query)
        print("--- ✅ Patent Agent Execution Successful ---")
        return json.dumps(result)
    except Exception as e:
        print(f"--- ❌ Error during Patent Landscape Agent execution: {e} ---")
        return json.dumps({
            "analysis": f"Error during Patent Landscape Agent invocation: {e}",
            "raw_data": {"error": str(e)}
        })


@tool
def invoke_clinical_trials_agent(query: str) -> str:
    
    """
    Invokes the specialized Clinical Trials Agent for pharmaceutical R&D pipeline data.
    Provides details on clinical trial counts, phases, sponsors, and emerging indications.
    """
    print(f"\n--- 🧪 Invoking Clinical Trials Agent ---")
    clinical_trials_agent = get_agent("clinical_trials_agent")
    if clinical_trials_agent is None:
        return "--- ⚠️ Clinical Trials Agent not initialized ---"
    print(f"Query: {query}")
    if clinical_trials_agent is None:
        print("--- ⚠️ Clinical Trials Agent not initialized ---")
        return json.dumps({
            "analysis": "Error: The Clinical Trials Agent is not initialized.",
            "raw_data": {"error": "Agent not initialized"}
        })
    try:
        print("--- 🚀 Executing clinical_trials_agent.invoke() ---")
        result = clinical_trials_agent.invoke(query)
        print("--- ✅ Clinical Trials Agent Execution Successful ---")
        return json.dumps(result)
    except Exception as e:
        print(f"--- ❌ Error during Clinical Trials Agent execution: {e} ---")
        return json.dumps({
            "analysis": f"Error during Clinical Trials Agent invocation: {e}",
            "raw_data": {"error": str(e)}
        })


@tool
def invoke_internal_knowledge_agent(query: str) -> str:
    
    """
    Invokes the specialized Internal Knowledge Agent to access proprietary company data.
    Provides strategic, competitive, regulatory, and operational intelligence.
    """
    print(f"\n--- 🏢 Invoking Internal Knowledge Agent ---")
    agent = get_agent("internal_agent")
    if agent is None:
        return "--- ⚠️ Internal Knowledge Agent not initialized ---"
    internal_agent = agent
    print(f"Query: {query}")
    if internal_agent is None:
        print("--- ⚠️ Internal Knowledge Agent not initialized ---")
        return json.dumps({
            "analysis": "Error: The Internal Knowledge Agent is not initialized.",
            "raw_data": {"error": "Agent not initialized"}
        })
    try:
        print("--- 🚀 Executing internal_agent.invoke() ---")
        result = internal_agent.invoke(query)
        print("--- ✅ Internal Knowledge Agent Execution Successful ---")
        return json.dumps(result)
    except Exception as e:
        print(f"--- ❌ Error during Internal Knowledge Agent execution: {e} ---")
        return json.dumps({
            "analysis": f"Error during Internal Knowledge Agent invocation: {e}",
            "raw_data": {"error": str(e)}
        })


@tool
def invoke_web_intelligence_agent(query: str) -> str:
    """
    Invokes the specialized Web Intelligence Agent for internet and literature searches.
    Combines SerpAPI web search and PubMed access for integrated public intelligence.
    """
    print(f"\n--- 🌐 Invoking Web Intelligence Agent ---")
    web_agent = get_agent("web_agent")
    print(f"Query: {query}")
    if web_agent is None:
        print("--- ⚠️ Web Intelligence Agent not initialized ---")
        return json.dumps({
            "analysis": "Error: Web Intelligence Agent is not initialized.",
            "raw_data": {"error": "Agent not initialized"}
        })
    try:
        print("--- 🚀 Executing web_agent.invoke() ---")
        result = web_agent.invoke(query)
        print("--- ✅ Web Intelligence Agent Execution Successful ---")
        return json.dumps(result)
    except Exception as e:
        print(f"--- ❌ Error during Web Intelligence Agent execution: {e} ---")
        return json.dumps({
            "analysis": f"Error during Web Intelligence Agent invocation: {e}",
            "raw_data": {"error": str(e)}
        })


# -----------------------------------------------------------------
# Master Tool Registry
# -----------------------------------------------------------------
print("\n--- 🧩 Registering Master Tool Suite ---")

master_tools = [
    iqvia_insights,
    invoke_web_intelligence_agent,
    invoke_exim_trade_agent,
    invoke_patent_landscape_agent,
    invoke_clinical_trials_agent,
    invoke_internal_knowledge_agent
]
print(f"--- ✅ Registered {len(master_tools)} Master Tools ---")

tool_executor = {
    "web_search": web_search,
    "pubmed_search": pubmed_search,
    "iqvia_insights": iqvia_insights,
    "invoke_web_intelligence_agent": invoke_web_intelligence_agent,
    "invoke_exim_trade_agent": invoke_exim_trade_agent,
    "invoke_patent_landscape_agent": invoke_patent_landscape_agent,
    "invoke_clinical_trials_agent": invoke_clinical_trials_agent,
    "invoke_internal_knowledge_agent": invoke_internal_knowledge_agent
}
print(f"--- ✅ Tool Executor Mapping Created ({len(tool_executor)} entries) ---\n")

print("✅ Tool Registry Initialized")
print(f"   - Total Tools: {len(TOOL_REGISTRY)}")