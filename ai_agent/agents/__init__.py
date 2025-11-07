# ai_agent/agents/__init__.py
"""
Agents package initializer.

This file imports the all_agents module to initialize the specialized agent instances
and exports a single singleton `master_agent` that other modules (services/views) import.
"""

from . import all_agents  # this runs all_agents module top-level code and creates specialized agents

# Export the singleton Master Agent
# all_agents should define `master_agent` after it defines specialized agents and imports master_tools
try:
    master_agent = getattr(all_agents, "master_agent")
except AttributeError:
    # If master_agent isn't present, raise a helpful error
    raise ImportError("master_agent not created in ai_agent.agents.all_agents. "
                      "Make sure all_agents instantiates master_agent at the end of the module.")
