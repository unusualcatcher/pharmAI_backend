import json
from typing import Dict, Any
from langchain.prompts import SystemMessagePromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from .tools import (
    get_exim_trade_data,
    get_iqvia_market_data,
    get_patent_landscape_data,
    get_clinical_trials_data,
    get_internal_document_data,
    pubmed_search,
    web_search,
)
from .report_generator import ReportGeneratorAgent
from ..config.settings import llm, streaming_llm

report_agent = ReportGeneratorAgent()

class EximTradeAgentExecutor:
    """
    Agent for querying and synthesizing EXIM trade data
    from the internal Django API.
    """
    
    def __init__(self, llm: ChatOpenAI, max_iterations: int = 2):
        self.llm = llm
        self.max_iterations = max_iterations
        
        self.tools = [get_exim_trade_data]
        self.tool_executor = {tool.name: tool for tool in self.tools}

        self.sys_prompt_template = SystemMessagePromptTemplate.from_template(
            """You are the EXIM Trends Agent, a specialist in global pharmaceutical trade data.

            YOUR ROLE:
            Your *only* job is to answer questions about export-import trends by querying an internal API.
            You must provide a clear, natural-language summary of the trade data you retrieve.

            YOUR TOOL:
            You have exactly ONE tool: `get_exim_trade_data(molecule_name: str)`
            
            YOUR PROCESS:
            1.  Receive a user's query (e.g., "What are the trade trends for metformin?").
            2.  You *must* identify the core **molecule_name** from the query.
            3.  You *must* then call your tool `get_exim_trade_data` with that molecule.
            4.  The tool will return a JSON string with trade data.
            5.  Your *final* response must be a **natural language synthesis** of this JSON data.
            
            OUTPUT FORMAT:
            -   **DO NOT** just return the raw JSON.
            -   Summarize the key findings, including:
                -   **API Exports:** Analyze the 'api_exports_2023' data. Highlight key exporters (e.g., India, China), their volumes, values, market share, and top destinations.
                -   **Formulation Imports:** Analyze the 'formulation_imports_2023' data. Highlight key importers (e.g., United States, Germany), their volumes, top sources, and import dependency.
                -   **Market Trend:** Summarize the 'market_trend' string.
                -   **Forecast:** Summarize the 'forecast_2024_2026' string.
            
            EXAMPLE SYNTHESIS:
            -   User Query: "Tell me about metformin trade."
            -   Agent Action: Calls `get_exim_trade_data(molecule_name="metformin")`
            -   Tool Result: (Receives the large JSON blob for metformin)
            -   Agent Final Answer: "For Metformin, 2023 API exports were led by China (28,000 tons, 48.3% share) and India (15,000 tons, 28.5% share). Key importers of formulations include the United States, which has a 78% import dependency and sources mainly from India and China, and Germany (65% dependency). The current market trend shows India's exports to the US growing while China's share declines due to trade tensions. A stable 4-5% CAGR is forecasted."

            CRITICAL RULES:
            ✓   Always call your tool to get data. Never answer from memory.
            ✓   If the user's query is vague (e.g., "What's the trade data?"), ask for clarification: "Which molecule are you interested in?"
            ✓   If the tool returns an error (e.g., "Molecule not found"), report this error clearly.
            """
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            self.sys_prompt_template,
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("human", "{input}"), 
        ])

        self.agent: Runnable = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", [])
            }
            | self.prompt
            | self.llm.bind_tools(self.tools, tool_choice="auto")
        )

    def invoke(self, query: str) -> dict:
        """
        Executes the EXIM Trends work cycle.
        Returns a dictionary with 'analysis' and 'raw_data'.
        """
        count = 0
        agent_scratchpad: list[BaseMessage] = []
        current_input = {"input": query}
        raw_data_json = {}

        while count < self.max_iterations:
            current_input["agent_scratchpad"] = agent_scratchpad
            
            response_ai_message = self.agent.invoke(current_input)

            if not response_ai_message.tool_calls:
                # CASE 1: No tools called. This is the final, synthesized answer.
                return {
                    "analysis": response_ai_message.content,
                    "raw_data": raw_data_json
                }
            
            else:
                # CASE 2: Tools were called.
                agent_scratchpad.append(response_ai_message)
                
                for tool_call in response_ai_message.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_function = self.tool_executor.get(tool_name)
                    
                    if tool_function:
                        try:
                            result_str = str(tool_function.invoke(tool_args))
                            try:
                                raw_data_json = json.loads(result_str)
                            except json.JSONDecodeError:
                                raw_data_json = {"error": result_str}
                        except Exception as e:
                            result_str = f"Error executing tool {tool_name}: {e}"
                            raw_data_json = {"error": result_str}
                    else:
                        result_str = f"Error: Tool '{tool_name}' not found."
                        raw_data_json = {"error": result_str}
                        
                    print(f"--- 🧠 Tool Result for {tool_name}: {result_str[:500]} ---")
                    
                    agent_scratchpad.append(
                        ToolMessage(content=result_str, tool_call_id=tool_call['id'])
                    )
                
                count += 1
        
        print("--- ⚠️ Agent reached maximum iterations without completion. ---")
        return {
            "analysis": "Error: EXIM Trade Agent reached max iterations.",
            "raw_data": raw_data_json
        }
    
class IqviaInsightsAgentExecutor:
    """
    Agent for querying and synthesizing IQVIA market intelligence data
    from the internal Django API.
    """
    
    def __init__(self, llm: ChatOpenAI, max_iterations: int = 2):
        self.llm = llm
        self.max_iterations = max_iterations
        self.tools = [get_iqvia_market_data]
        self.tool_executor = {tool.name: tool for tool in self.tools}

        # --- THIS IS THE FULL, RECONSTRUCTED SYSTEM PROMPT ---
        self.sys_prompt_template = SystemMessagePromptTemplate.from_template(
            """You are the IQVIA Insights Agent, a specialist in global pharmaceutical market intelligence.

            YOUR ROLE:
            Your *only* job is to answer questions about market data by querying an internal API.
            You must provide a clear, natural-language summary of the market data you retrieve.

            YOUR TOOL:
            You have exactly ONE tool: `get_iqvia_market_data(therapy_area: str)`
            
            YOUR PROCESS:
            1.  Receive a user's query (e.g., "What is the market size for oncology?").
            2.  You *must* identify the core **therapy_area** from the query (e.g., 'oncology', 'respiratory').
            3.  You *must* then call your tool `get_iqvia_market_data` with that therapy area.
            4.  The tool will return a JSON string with market data.
            5.  Your *final* response must be a **natural language synthesis** of this JSON data.
            
            OUTPUT FORMAT:
            -   **DO NOT** just return the raw JSON.
            -   Summarize the key findings, including:
                -   **Market Size & Growth:** Analyze 'market_size_usd_billions' and 'cagr_percent'.
                -   **Competitor Landscape:** Summarize the 'competitor_market_share' data, highlighting top players.
                -   **Key Trends:** Summarize the 'key_trends' string.
            
            EXAMPLE SYNTHESIS:
            -   User Query: "Tell me about the respiratory market."
            -   Agent Action: Calls `get_iqvia_market_data(therapy_area="respiratory")`
            -   Tool Result: (Receives JSON: {"therapy_area": "respiratory", "market_size_usd_billions": 95.2, "cagr_percent": 5.2, "competitor_market_share": {"GSK": 28.5, "AstraZeneca": 22.1, "Sanofi": 18.9}, "key_trends": "Market driven by new biologics for asthma/COPD; increasing payer pressure."})
            -   Agent Final Answer: "According to IQVIA data, the global respiratory market is valued at $95.2 billion with a 5.2% CAGR. The market is led by GSK (28.5% share), AstraZeneca (22.1%), and Sanofi (18.9%). Key trends show growth driven by new biologics for asthma and COPD, though there is increasing payer pressure."

            CRITICAL RULES:
            ✓   Always call your tool to get data. Never answer from memory.
            ✓   If the user's query is vague and you cannot extract a therapy_area (e.g., "What's the market?"), ask for clarification: "Which therapy area are you interested in?"
            ✓   If the tool returns an error (e.g., "Therapy area not found"), report this error clearly to the user.
            """
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            self.sys_prompt_template,
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("human", "{input}"), 
        ])

        self.agent: Runnable = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", [])
            }
            | self.prompt
            | self.llm.bind_tools(self.tools, tool_choice="auto")
        )

    def invoke(self, query: str) -> dict:
        """
        Executes the IQVIA Insights work cycle.
        Returns a dictionary with 'analysis' and 'raw_data'.
        """
        print(f"--- 🧠 IQVIA Agent Invoked with Query: '{query}' ---")
        count = 0
        agent_scratchpad: list[BaseMessage] = []
        current_input = {"input": query}
        raw_data_json = {}

        while count < self.max_iterations:
            print(f"--- 🔁 Iteration {count + 1}/{self.max_iterations} ---")
            current_input["agent_scratchpad"] = agent_scratchpad
            
            response_ai_message = self.agent.invoke(current_input)
            print(f"--- 🤖 LLM Response Received ---")

            if not response_ai_message.tool_calls:
                # CASE 1: No tools called. This is the final, synthesized answer.
                print("--- ✅ Final Synthesis Reached ---")
                return {
                    "analysis": response_ai_message.content,
                    "raw_data": raw_data_json
                }
            
            else:
                # CASE 2: Tools were called.
                agent_scratchpad.append(response_ai_message)
                
                for tool_call in response_ai_message.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    print(f"--- 🔍 Tool Call Detected: {tool_name} | Args: {tool_args} ---")
                    
                    tool_function = self.tool_executor.get(tool_name)
                    
                    if tool_function:
                        try:
                            result_str = str(tool_function.invoke(tool_args))
                            print(f"--- 📦 Tool Result Raw: {result_str[:500]} ---")  # Show first 500 chars
                            try:
                                raw_data_json = json.loads(result_str)
                            except json.JSONDecodeError:
                                raw_data_json = {"error": result_str}
                        except Exception as e:
                            result_str = f"Error executing tool {tool_name}: {e}"
                            raw_data_json = {"error": result_str}
                            print(f"--- ❌ Tool Execution Error: {e} ---")
                    else:
                        result_str = f"Error: Tool '{tool_name}' not found."
                        raw_data_json = {"error": result_str}
                        print(f"--- ⚠️ Tool Not Found: {tool_name} ---")
                        
                    agent_scratchpad.append(
                        ToolMessage(content=result_str, tool_call_id=tool_call['id'])
                    )
                
                count += 1
        
        print("--- ⚠️ IQVIA Agent reached maximum iterations without completion. ---")
        return {
            "analysis": "Error: IQVIA Agent reached max iterations.",
            "raw_data": raw_data_json
        }
    
class PatentLandscapeAgentExecutor:
    """
    Agent for querying and synthesizing patent landscape data
    from the internal Django API.
    """
    
    def __init__(self, llm: ChatOpenAI, max_iterations: int = 2):
        self.llm = llm
        self.max_iterations = max_iterations
        self.tools = [get_patent_landscape_data]
        self.tool_executor = {tool.name: tool for tool in self.tools}

        # --- THIS IS THE FULL, RECONSTRUCTED SYSTEM PROMPT ---
        self.sys_prompt_template = SystemMessagePromptTemplate.from_template(
            """You are the Patent Landscape Agent, a specialist in pharmaceutical intellectual property.

            YOUR ROLE:
            Your *only* job is to answer questions about patent data by querying an internal API.
            You must provide a clear, natural-language summary of the patent data you retrieve.

            YOUR TOOL:
            You have exactly ONE tool: `get_patent_landscape_data(molecule_name: str)`
            
            YOUR PROCESS:
            1.  Receive a user's query (e.g., 'What is the FTO for semaglutide?').
            2.  You *must* identify the core **molecule_name** from the query (e.g., 'semaglutide').
            3.  You *must* then call your tool `get_patent_landscape_data` with that molecule.
            4.  The tool will return a JSON string with patent data.
            5.  Your *final* response must be a **natural language synthesis** of this JSON data.
            
            OUTPUT FORMAT:
            -   **DO NOT** just return the raw JSON.
            -   Summarize the key findings, including:
                -   **Patent Status:** Analyze 'patent_status' and 'fto_analysis'.
                -   **Key Expiry:** Highlight the 'key_patent_expiry' dates (e.g., for Composition of Matter or key indications).
                -   **Active Patents:** Summarize the 'active_patents_summary' (e.g., 'Active patents focus on new formulations and delivery systems...').
                -   **Opportunities:** Conclude with the 'white_space_opportunities'.
            
           EXAMPLE SYNTHESIS:
-   User Query: Tell me about the patent situation for sitagliptin.
-   Agent Action: Calls get_patent_landscape_data with molecule sitagliptin
-   Tool Result: Receives patent data including status, FTO analysis, expiry dates, and opportunities
-   Agent Final Answer: For sitagliptin, the key Composition of Matter patent expired in late 2022, and the DPP-IV indication patent expired in March 2024. Freedom-to-Operate is clear for generic entry on the base molecule. Remaining active patents primarily cover co-formulations like with metformin and extended-release versions. White-space opportunities exist in novel combination therapies or alternative salt forms.

            CRITICAL RULES:
            ✓   Always call your tool to get data. Never answer from memory.
            ✓   If the user's query is vague, ask for clarification: 'Which molecule's patent data are you interested in?'
            ✓   If the tool returns an error, report that error clearly.
            """
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            self.sys_prompt_template,
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("human", "{input}"), 
        ])

        self.agent: Runnable = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", [])
            }
            | self.prompt
            | self.llm.bind_tools(self.tools, tool_choice="auto")
        )

    def invoke(self, query: str) -> dict:
        """
        Executes the Patent Landscape work cycle.
        Returns a dictionary with 'analysis' and 'raw_data'.
        """
        print(f"--- 🧠 Patent Agent Invoked with Query: '{query}' ---")
        count = 0
        agent_scratchpad: list[BaseMessage] = []
        current_input = {"input": query}
        raw_data_json = {}

        while count < self.max_iterations:
            print(f"--- 🔁 Iteration {count + 1}/{self.max_iterations} ---")
            current_input["agent_scratchpad"] = agent_scratchpad
            
            print("--- 🤖 Sending query to LLM ---")
            response_ai_message = self.agent.invoke(current_input)
            print("--- 📥 Response from LLM received ---")

            if not response_ai_message.tool_calls:
                print("--- ✅ Final synthesis detected, returning analysis ---")
                return {
                    "analysis": response_ai_message.content,
                    "raw_data": raw_data_json
                }
            
            else:
                print(f"--- 🧩 Tool Calls Detected: {len(response_ai_message.tool_calls)} ---")
                agent_scratchpad.append(response_ai_message)
                
                for tool_call in response_ai_message.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    print(f"--- 🔍 Executing Tool: {tool_name} | Args: {tool_args} ---")
                    
                    tool_function = self.tool_executor.get(tool_name)
                    
                    if tool_function:
                        try:
                            result_str = str(tool_function.invoke(tool_args))
                            print(f"--- 📦 Tool Result (first 500 chars): {result_str[:500]} ---")
                            try:
                                raw_data_json = json.loads(result_str)
                                print("--- ✅ JSON Parsed Successfully ---")
                            except json.JSONDecodeError:
                                raw_data_json = {"error": result_str}
                                print("--- ⚠️ Failed to Parse JSON ---")
                        except Exception as e:
                            result_str = f"Error executing tool {tool_name}: {e}"
                            raw_data_json = {"error": result_str}
                            print(f"--- ❌ Exception During Tool Execution: {e} ---")
                    else:
                        result_str = f"Error: Tool '{tool_name}' not found."
                        raw_data_json = {"error": result_str}
                        print(f"--- ⚠️ Tool Not Found: {tool_name} ---")
                        
                    print("--- 🧠 Appending Tool Result to Scratchpad ---")
                    agent_scratchpad.append(
                        ToolMessage(content=result_str, tool_call_id=tool_call['id'])
                    )
                
                count += 1
                print(f"--- 🔁 End of Iteration {count} ---")
        
        print("--- ⚠️ Patent Agent reached maximum iterations without completion ---")
        return {
            "analysis": "Error: Patent Agent reached max iterations.",
            "raw_data": raw_data_json
        }
    
class ClinicalTrialsAgentExecutor:
    """
    Agent for querying and synthesizing clinical trials data
    from the internal Django API.
    """
    
    def __init__(self, llm: ChatOpenAI, max_iterations: int = 2):
        self.llm = llm
        self.max_iterations = max_iterations
        self.tools = [get_clinical_trials_data]
        self.tool_executor = {tool.name: tool for tool in self.tools}

        # --- SYSTEM PROMPT TEMPLATE ---
        self.sys_prompt_template = SystemMessagePromptTemplate.from_template(
            """You are the Clinical Trials Agent, a specialist in pharmaceutical R&D pipelines.

            YOUR ROLE:
            Your *only* job is to answer questions about clinical trial data by querying an internal API.
            You must provide a clear, natural-language summary of the trial data you retrieve.

            YOUR TOOL:
            You have exactly ONE tool: `get_clinical_trials_data(molecule_name: str)`
            
            YOUR PROCESS:
            1.  Receive a user's query (e.g., "What trials are active for pirfenidone?").
            2.  Identify the core **molecule_name** from the query (e.g., 'pirfenidone').
            3.  Call your tool `get_clinical_trials_data` with that molecule.
            4.  The tool returns a JSON string with trial data.
            5.  Your *final* response must be a **natural language synthesis** of this JSON data.
            
            OUTPUT FORMAT:
            -   Summarize the key findings, including:
                -   **Trial Counts:** State the 'total_trials' and 'active_trials'.
                -   **Ongoing Trials:** List key 'ongoing_trials' (e.g., NCT ID, title, phase, status).
                -   **Sponsors:** Analyze the 'sponsor_breakdown' (e.g., "Sponsors are 60% academic, 40% industry...").
                -   **Indications:** Summarize the 'indication_distribution' (e.g., "Trials focus on IPF (45%), SSc-ILD (20%), and others...").

            CRITICAL RULES:
            ✓   Always call your tool to get data. Never answer from memory.
            ✓   If the query is vague, ask: "Which molecule's clinical trials are you interested in?"
            ✓   If the tool returns an error, report it clearly.
            """
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            self.sys_prompt_template,
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("human", "{input}"),
        ])

        self.agent: Runnable = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", []),
            }
            | self.prompt
            | self.llm.bind_tools(self.tools, tool_choice="auto")
        )

    def invoke(self, query: str) -> dict:
        """
        Executes the Clinical Trials work cycle.
        Returns a dictionary with 'analysis' and 'raw_data'.
        """
        print(f"=== 🧠 Clinical Trials Agent Invoked with Query: '{query}' ===")
        count = 0
        agent_scratchpad: list[BaseMessage] = []
        current_input = {"input": query}
        raw_data_json = {}

        while count < self.max_iterations:
            print(f"--- 🔁 Iteration {count + 1}/{self.max_iterations} ---")
            current_input["agent_scratchpad"] = agent_scratchpad

            print("--- 🤖 Sending query to LLM for reasoning ---")
            response_ai_message = self.agent.invoke(current_input)
            print("--- 📥 LLM Response Received ---")

            # CASE 1: No tool call, LLM produced final analysis
            if not response_ai_message.tool_calls:
                print("--- ✅ Final synthesis reached. Returning analysis. ---")
                return {
                    "analysis": response_ai_message.content,
                    "raw_data": raw_data_json
                }

            # CASE 2: LLM requests tool execution
            else:
                print(f"--- 🧩 Tool Calls Detected: {len(response_ai_message.tool_calls)} ---")
                agent_scratchpad.append(response_ai_message)

                for tool_call in response_ai_message.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    print(f"--- 🔍 Executing Tool: {tool_name} | Args: {tool_args} ---")

                    tool_function = self.tool_executor.get(tool_name)

                    if tool_function:
                        try:
                            print(f"--- ⚙️ Invoking {tool_name} ---")
                            result_str = str(tool_function.invoke(tool_args))
                            print(f"--- 📦 Tool Result (first 500 chars): {result_str[:500]} ---")

                            try:
                                raw_data_json = json.loads(result_str)
                                print("--- ✅ JSON Parsed Successfully ---")
                            except json.JSONDecodeError:
                                raw_data_json = {"error": result_str}
                                print("--- ⚠️ JSON Parsing Failed ---")

                        except Exception as e:
                            result_str = f"Error executing tool {tool_name}: {e}"
                            raw_data_json = {"error": result_str}
                            print(f"--- ❌ Tool Execution Error: {e} ---")
                    else:
                        result_str = f"Error: Tool '{tool_name}' not found."
                        raw_data_json = {"error": result_str}
                        print(f"--- ⚠️ Tool Not Found: {tool_name} ---")

                    print("--- 🧠 Appending Tool Result to Agent Scratchpad ---")
                    agent_scratchpad.append(
                        ToolMessage(content=result_str, tool_call_id=tool_call["id"])
                    )

                count += 1
                print(f"--- 🔁 End of Iteration {count} ---")

        print("--- ⚠️ Agent Reached Maximum Iterations Without Completion ---")
        return {
            "analysis": "Error: Clinical Trials Agent reached max iterations.",
            "raw_data": raw_data_json
        }
    
class InternalKnowledgeAgentExecutor:
    """
    Agent for retrieving and synthesizing internal company documents.
    """

    def __init__(self, llm: ChatOpenAI, max_iterations: int = 2):
        self.llm = llm
        self.max_iterations = max_iterations
        self.tools = [get_internal_document_data]
        self.tool_executor = {tool.name: tool for tool in self.tools}

        # --- SYSTEM PROMPT TEMPLATE ---
        self.sys_prompt_template = SystemMessagePromptTemplate.from_template(
            """You are the Internal Knowledge Agent, a specialist in the company's internal strategy and intelligence.

            YOUR ROLE:
            Your job is to answer user queries by retrieving and synthesizing specific, high-value internal documents.
            Your API *requires* a specific `doc_id` to function.

            YOUR TOOL:
            You have exactly ONE tool: `get_internal_document_data(doc_id: str)`
            
            YOUR PROCESS:
            1. Analyze the query.
            2. Identify the correct `doc_id` from the KEY DOCUMENT MAP.
            3. Call the tool `get_internal_document_data(doc_id)` with that ID.
            4. Summarize and synthesize the JSON data.

            **KEY DOCUMENT MAP:**
            * Strategy / Portfolio / Roadmap / 3-year plan → STRAT-2024-001
            * Field intelligence / Physician feedback / Market access → FIELD-2024-Q3
            * Manufacturing / Capabilities / Supply chain → MFG-CAP-2024-001
            * Regulatory / FDA / Orphan / 505(b)(2) → REG-2024-002
            * Competitors / Teva / Sun Pharma → COMP-2024-005

            CRITICAL RULES:
            ✓ Always call your tool — never answer from memory.
            ✓ If unclear, ask: “Which internal document or topic (e.g., strategy, field intelligence) are you interested in?”
            ✓ Clearly report API or data errors.
            """
        )

        self.prompt = ChatPromptTemplate.from_messages([
            self.sys_prompt_template,
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("human", "{input}")
        ])

        self.agent: Runnable = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", [])
            }
            | self.prompt
            | self.llm.bind_tools(self.tools, tool_choice="auto")
        )

    def invoke(self, query: str) -> dict:
        """
        Executes the Internal Knowledge work cycle.
        Returns a dictionary with 'analysis' and 'raw_data'.
        """
        print(f"=== 🧠 Internal Knowledge Agent Invoked with Query: '{query}' ===")
        count = 0
        agent_scratchpad: list[BaseMessage] = []
        current_input = {"input": query}
        raw_data_json = {}

        while count < self.max_iterations:
            print(f"--- 🔁 Iteration {count + 1}/{self.max_iterations} ---")
            current_input["agent_scratchpad"] = agent_scratchpad

            print("--- 🤖 Sending query to LLM for reasoning ---")
            response_ai_message = self.agent.invoke(current_input)
            print("--- 📥 LLM Response Received ---")

            # CASE 1: LLM provided final synthesis
            if not response_ai_message.tool_calls:
                print("--- ✅ Final synthesis reached. Returning analysis. ---")
                return {
                    "analysis": response_ai_message.content,
                    "raw_data": raw_data_json
                }

            # CASE 2: LLM requested tool use
            else:
                print(f"--- 🧩 Tool Calls Detected: {len(response_ai_message.tool_calls)} ---")
                agent_scratchpad.append(response_ai_message)

                for tool_call in response_ai_message.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    print(f"--- 🔍 Executing Tool: {tool_name} | Args: {tool_args} ---")

                    tool_function = self.tool_executor.get(tool_name)

                    if tool_function:
                        try:
                            print(f"--- ⚙️ Invoking {tool_name} ---")
                            result_str = str(tool_function.invoke(tool_args))
                            print(f"--- 📦 Tool Result (first 500 chars): {result_str[:500]} ---")

                            try:
                                raw_data_json = json.loads(result_str)
                                print("--- ✅ JSON Parsed Successfully ---")
                            except json.JSONDecodeError:
                                raw_data_json = {"error": result_str}
                                print("--- ⚠️ JSON Parsing Failed ---")

                        except Exception as e:
                            result_str = f"Error executing tool {tool_name}: {e}"
                            raw_data_json = {"error": result_str}
                            print(f"--- ❌ Tool Execution Error: {e} ---")
                    else:
                        result_str = f"Error: Tool '{tool_name}' not found."
                        raw_data_json = {"error": result_str}
                        print(f"--- ⚠️ Tool Not Found: {tool_name} ---")

                    print("--- 🧠 Appending Tool Result to Agent Scratchpad ---")
                    agent_scratchpad.append(
                        ToolMessage(content=result_str, tool_call_id=tool_call["id"])
                    )

                count += 1
                print(f"--- 🔁 End of Iteration {count} ---")

        print("--- ⚠️ Agent Reached Maximum Iterations Without Completion ---")
        return {
            "analysis": "Error: Internal Knowledge Agent reached max iterations.",
            "raw_data": raw_data_json
        }
class WebIntelligenceAgentExecutor:
    """
    Agent responsible for performing structured public web and literature research.
    Combines SerpAPI-based web search and PubMed scientific queries.
    """

    def __init__(self, llm: ChatOpenAI, tools_list: list, max_iterations: int = 3):
        self.llm = llm
        self.max_iterations = max_iterations
        self.tools_list = tools_list
        self.tool_executor = {tool.name: tool for tool in tools_list}

        # --- SYSTEM PROMPT (FULLY RECONSTRUCTED) ---
        self.sys_prompt_template = SystemMessagePromptTemplate.from_template(
            """You are the Web Intelligence Agent, a specialist in public web and scientific literature research.

            YOUR ROLE:
            You are a **research reporter** — not an analyst or strategist. 
            You must find, extract, and summarize factual findings from the web and PubMed.

            TOOLS:
            1. `web_search(query: str)` → For general web/news content.
            2. `pubmed_search(query: str)` → For scientific papers and studies.

            PROCESS:
            1. Analyze the user's request.
            2. Decide whether to use web_search, pubmed_search, or both.
            3. Call your tools with specific, relevant queries.
            4. Synthesize the factual findings into a structured report.

            OUTPUT:
            - **Organize** your findings under:
                - "🌐 Web Search Findings"
                - "📚 PubMed Literature"
            - **Cite** sources clearly (title, publication, date, or PMID).
            - **Avoid** opinion, speculation, or strategy commentary.
            - **If no data**, clearly state "No relevant results found."

            EXAMPLE:
            User: "Find latest news and PubMed articles on semaglutide for obesity."
            Tools: `web_search("semaglutide obesity news 2024")`, `pubmed_search("semaglutide obesity")`
            Final: Summarized, cited report by section.
            """
        )

        self.prompt = ChatPromptTemplate.from_messages([
            self.sys_prompt_template,
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.agent: Runnable = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", [])
            }
            | self.prompt
            | llm.bind_tools(tools_list, tool_choice="auto")
        )

    # -----------------------------------------------------------------
    # INVOKE METHOD — FULLY INSTRUMENTED
    # -----------------------------------------------------------------
    def invoke(self, query: str) -> dict:
        """
        Executes the Web Intelligence Agent work cycle.
        Returns dict with structured analysis and raw tool data.
        """
        print(f"\n=== 🌐 WEB INTELLIGENCE AGENT INVOKED ===")
        print(f"--- 🧠 Incoming Query: '{query}' ---")
        count = 0
        agent_scratchpad: list[BaseMessage] = []
        current_input = {"input": query}
        raw_data_json = {}

        while count < self.max_iterations:
            print(f"\n--- 🔄 Iteration {count + 1}/{self.max_iterations} ---")
            current_input["agent_scratchpad"] = agent_scratchpad

            print("--- 🤖 Sending to LLM for reasoning and tool call decisions ---")
            response_ai_message = self.agent.invoke(current_input)
            print("--- 📥 LLM Response Received ---")

            # CASE 1: LLM produces a final answer directly
            if not response_ai_message.tool_calls:
                print("--- ✅ Final synthesis reached, no further tools to call ---")
                raw_data_json["report_content"] = response_ai_message.content
                print("--- 🧾 Returning completed synthesis and raw data ---\n")
                return {
                    "analysis": response_ai_message.content,
                    "raw_data": raw_data_json
                }

            # CASE 2: LLM requests tool calls
            print(f"--- 🧩 Tool Calls Detected: {len(response_ai_message.tool_calls)} ---")
            agent_scratchpad.append(response_ai_message)

            for tool_call in response_ai_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                print(f"--- ⚙️ Preparing Tool Execution: {tool_name} ---")
                print(f"--- 📦 Tool Args: {tool_args} ---")

                if tool_name in self.tool_executor:
                    tool_function = self.tool_executor[tool_name]
                    try:
                        print(f"--- 🚀 Executing {tool_name} ---")
                        result_str = str(tool_function.invoke(tool_args))
                        print(f"--- 📬 Tool Result (first 300 chars): {result_str[:300]} ---")

                        raw_data_json[f"{tool_name}_result_{tool_call['id']}"] = result_str
                    except Exception as e:
                        print(f"--- ❌ Tool Execution Error: {e} ---")
                        result_str = f"Error executing tool {tool_name}: {e}"
                        raw_data_json[f"{tool_name}_error_{tool_call['id']}"] = result_str
                else:
                    print(f"--- ⚠️ Tool Not Found: {tool_name} ---")
                    result_str = f"Error: Tool '{tool_name}' not found."
                    raw_data_json[f"{tool_name}_error_{tool_call['id']}"] = result_str

                print("--- 🧠 Appending Tool Result to Agent Scratchpad ---")
                agent_scratchpad.append(
                    ToolMessage(content=result_str, tool_call_id=tool_call["id"])
                )

            count += 1
            print(f"--- 🔁 End of Iteration {count} ---")

        print("--- ⚠️ Agent Reached Maximum Iterations Without Completion ---\n")
        return {
            "analysis": "Error: Web Intelligence Agent reached max iterations.",
            "raw_data": raw_data_json
        }
    
web_tools = [web_search, pubmed_search]

web_agent = WebIntelligenceAgentExecutor(llm=llm, tools_list=web_tools)
exim_agent = EximTradeAgentExecutor(llm=llm)
internal_agent = InternalKnowledgeAgentExecutor(llm=llm)
iqvia_agent = IqviaInsightsAgentExecutor(llm=llm, max_iterations=2)
patent_agent = PatentLandscapeAgentExecutor(llm=llm)
clinical_trials_agent = ClinicalTrialsAgentExecutor(llm=llm)

from .invoke_tools import master_tools, tool_executor
class MasterAgentExecturor:

    def __init__(self, llm: ChatOpenAI, streaming_llm: ChatOpenAI, tools_list: list, report_agent: ReportGeneratorAgent, max_iterations: int = 5):
        
        # This is the full, corrected system prompt
        self.sys_prompt_template = SystemMessagePromptTemplate.from_template("""
        You are the "Master Agent," an advanced AI assistant with two modes of operation:
        
        1.  **Conversational Chatbot (Default):** Your primary role is to be a helpful and conversational chatbot. For general questions, small talk, or simple explanations (e.g., "hello", "explain what an API is", "how are you?"), you will answer directly **without using any tools**.
        
        2.  **Specialized Task Executor (On-Demand):** When the user asks a specific, complex query or requests a task that requires data, you will activate your specialized tools to gather, process, and synthesize information.
        
        ---
        
        ### 🚨 Your Core Logic
        
        1.  **Analyze Intent:** First, analyze the user's input.
            * Is this a simple conversation? -> **Answer directly.**
            * Is this a complex query for data? -> **Move to Step 2.**
    
        2.  **Select Tools:** If it's a complex query, you MUST select one or more of the following tools to gather all necessary information. **You can and should call multiple tools in parallel** if the query demands it (e.g., "compare market size and patents").
        
        ---
        
        ### 🛠️ Available Tools
        
        * **`invoke_web_intelligence_agent(query)`:** Your primary tool for all web-based research. Use this to find news, articles, guidelines, patient perspectives (from the web) and scientific/biomedical papers (from PubMed). The query you pass to it should be descriptive.
        * **`iqvia_insights(query)`:** For market size, growth trends, competition, therapy areas, and disease landscapes.
        * **`invoke_exim_trade_agent(query)`:** For export-import data, trade volumes, and sourcing for specific molecules.
        * **`invoke_patent_landscape_agent(query)`:** For patent FTO analysis, patent expiry, and IP strategy.
        * **`invoke_clinical_trials_agent(query)`:** For clinical trial status, phases, sponsors, and emerging indications.
        * **`invoke_internal_knowledge_agent(query)`:** For internal company strategy, field reports, and manufacturing capabilities.

        (IMPORTANT: You do NOT have a 'generate_report' tool. You will synthesize the final
         text summary, and the system will generate a report from your summary
         if the user asks for one.)
        
        ---
        
        ### 🔄 Execution Flow
        
        * **Iteration 1 (Planning):** You will be given the user's query. Your job is to call the correct tool(s) with the correct inputs.
        * **Iteration 2+ (Synthesis):** You will be given the original query *and* the data from your tool calls (in the `agent_scratchpad`). Your job is to **stop calling tools** and synthesize all the information into a single, comprehensive, human-readable answer.
            * **DO NOT** just list the raw JSON.
            * Integrate the findings into a well-structured response.
            * Cite your data sources (e.g., "According to market data...", "The patent search found...", "The web intelligence agent reported...").
            * Stream your final, synthesized answer to the user.
        """)
        
        self.max_iterations = max_iterations # Note: This is no longer used by the loop, but good to keep
        self.streaming_llm = streaming_llm 
        self.report_agent = report_agent 
        
        # --- REMOVED self.friendly_name_map ---
        
        self.prompt = ChatPromptTemplate.from_messages([
            self.sys_prompt_template,
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),  # Move this AFTER human
        ])
        
        self.agent: Runnable = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", [])
            }
            | self.prompt
            | llm.bind_tools(tools_list, tool_choice="auto")
        )
        
        self.final_answer_chain = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", [])
            }
            | self.prompt
            | self.streaming_llm
        )
    
    # --- REMOVED _animate_status METHOD ---

    def invoke(self, user_prompt: str):
        # --- 1. SETUP ---
        agent_scratchpad: list[BaseMessage] = []
        current_input = {"input": user_prompt}
        
        # Report detection logic
        report_requested = False
        report_format = None 
        query_lower = user_prompt.lower()
    
        if "report" in query_lower or "pdf" in query_lower or "excel" in query_lower:
            report_requested = True
            
        if "pdf" in query_lower and "excel" in query_lower:
            report_format = "both"
        elif "excel" in query_lower:
            report_format = "excel"
        elif "pdf" in query_lower or "report" in query_lower:
            report_format = "pdf"
    
        # --- 2. PLAN (Run the planning chain *once*) ---
        response_ai_message = self.agent.invoke(current_input)
    
        # --- 3. DECIDE & ACT ---
        if not response_ai_message.tool_calls:
            # CASE 1: NO TOOLS CALLED (Simple Chat)
            yield from self.final_answer_chain.stream(current_input)
            return
    
        else:
            # CASE 2: TOOLS CALLED (Complex Query)
            
            # Add the AI's decision to the scratchpad
            agent_scratchpad.append(response_ai_message)
            
            # Execute all planned tool calls
            for tool_call in response_ai_message.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                # Store the full result for reporting
                full_result_for_reporting = {}
    
                if tool_name in tool_executor:
                    tool_function = tool_executor[tool_name]
                    try:
                        # Invoke the tool function
                        result = tool_function.invoke(tool_args)
                        
                        # Parse the result (most tools return JSON strings)
                        if isinstance(result, str):
                            try:
                                result_dict = json.loads(result)
                                analysis_content = result_dict.get("analysis", "No analysis provided.")
                                full_result_for_reporting = result_dict
                            except json.JSONDecodeError:
                                # If it's not JSON, treat the entire string as analysis
                                analysis_content = result
                                full_result_for_reporting = {
                                    "analysis": result,
                                    "raw_data": {"error": "String output, not JSON"}
                                }
                        elif isinstance(result, dict):
                            analysis_content = result.get("analysis", "No analysis provided.")
                            full_result_for_reporting = result
                        else:
                            analysis_content = f"Error: Unknown tool output type: {type(result)}"
                            full_result_for_reporting = {
                                "analysis": analysis_content,
                                "raw_data": {"error": "Unknown output type"}
                            }
    
                    except Exception as e:
                        analysis_content = f"Error executing tool {tool_name}: {str(e)}"
                        full_result_for_reporting = {
                            "analysis": analysis_content,
                            "raw_data": {"error": str(e)}
                        }
                else:
                    analysis_content = f"Error: Tool '{tool_name}' not found."
                    full_result_for_reporting = {
                        "analysis": analysis_content,
                        "raw_data": {"error": "Tool not found"}
                    }
                
                # Create the ToolMessage with the analysis in content
                # and store the full result in additional_kwargs for reporting
                tool_message = ToolMessage(
                    content=analysis_content,  # Only the analysis text goes here
                    tool_call_id=tool_call['id'],
                    name=tool_name
                )
                tool_message.additional_kwargs = {
                    "full_json_for_reporting": json.dumps(full_result_for_reporting)
                }
                agent_scratchpad.append(tool_message)
    
            # --- 4. SYNTHESIZE (Run the synthesis chain *once*) ---
            synthesis_input = {
                "input": user_prompt,
                "agent_scratchpad": agent_scratchpad
            }
    
            # Stream the final answer and capture it for the report
            final_summary_chunks = []
            for chunk in self.final_answer_chain.stream(synthesis_input):
                yield chunk  # Stream to user
                if hasattr(chunk, 'content'):
                    final_summary_chunks.append(chunk.content)
                else:
                    final_summary_chunks.append(str(chunk))
            
            final_summary = "".join(final_summary_chunks)
    
            # --- 5. GENERATE REPORT (After synthesis) ---
            report_confirmation = ""
            if report_requested and report_format:
                try:
                    tool_messages = [msg for msg in agent_scratchpad if isinstance(msg, ToolMessage)]
                    agent_responses_list = []
                    agent_name_map = {
                        "invoke_internal_knowledge_agent": "Internal Knowledge Agent",
                        "invoke_clinical_trials_agent": "Clinical Trials Agent",
                        "invoke_patent_landscape_agent": "Patent Landscape Agent",
                        "invoke_exim_trade_agent": "EXIM Trends Agent",
                        "iqvia_insights": "IQVIA Insights Agent",
                        "invoke_web_intelligence_agent": "Web Intelligence Agent"
                    }
    
                    for tool_msg in tool_messages:
                        full_json_str = tool_msg.additional_kwargs.get("full_json_for_reporting")
                        try:
                            data_dict = json.loads(full_json_str) 
                            analysis = data_dict.get("analysis", "No analysis provided.")
                            raw_data = data_dict.get("raw_data", {"error": "No raw data."})
                        except (json.JSONDecodeError, TypeError):
                            analysis = tool_msg.content 
                            raw_data = {
                                "analysis_summary": analysis,
                                "error": "Could not parse full_json_for_reporting"
                            }
    
                        agent_name = agent_name_map.get(tool_msg.name, tool_msg.name)
                        agent_responses_list.append({
                            "agent": agent_name, 
                            "analysis": analysis,
                            "sources": [f"Source: {agent_name}"],
                            "raw_data": raw_data
                        })
                    
                    report_result = self.report_agent.generate_report(
                        query=user_prompt,
                        agent_responses=agent_responses_list,
                        summary=final_summary,
                        format=report_format
                    )
                    
                    if report_result.get("status") == "success":
                        report_path = report_result.get('filepath', 'Failed to get path')
                        report_confirmation = f"\n\n**📊 Report File:**\n{report_path}"
                    else:
                        report_confirmation = f"\n\n**📊 Report Generation Failed:**\n{report_result.get('message', 'Unknown error')}"
    
                except Exception as e:
                    report_confirmation = f"\n\n**📊 Report Generation Failed:**\n{e}"
            
            if report_confirmation:
                yield report_confirmation
            
        return
master_agent = MasterAgentExecturor(
    llm=llm,
    streaming_llm=streaming_llm,
    tools_list=master_tools,
    report_agent=report_agent,
    max_iterations=5,
)