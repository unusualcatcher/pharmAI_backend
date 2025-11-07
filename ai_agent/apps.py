from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class AiAgentConfig(AppConfig):
    name = "ai_agent"
    verbose_name = "AI Agent"

    def ready(self):
        # Import the agents package -> runs ai_agent.agents.__init__ -> all_agents executes
        try:
            # Import ensures ai_agent.agents.__init__ runs, which imports all_agents and creates master_agent
            from . import agents as _agents  # noqa: F401
            logger.info("ai_agent: agents module imported and initialized.")
        except Exception as e:
            # Do not crash entire server on startup — log instead (you can raise if you prefer hard-fail)
            logger.exception("Failed to initialize ai_agent agents on Django startup: %s", e)
