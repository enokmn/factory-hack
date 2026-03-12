from dotenv import load_dotenv
from agent_framework import WorkflowBuilder, Executor, handler, WorkflowContext

import os
import sys
import re
import logging
from typing import Any
from agent_framework import ChatAgent


def extract_work_order_id(text: str) -> str | None:
    """Extract work order ID (wo-XXXX-XXXXXXXX) from text."""
    match = re.search(r'wo-\d{4}-[a-f0-9]+', text, re.IGNORECASE)
    return match.group(0) if match else None
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

# Add challenge-3 agents to the Python path for in-place imports
# This path is relative to this file's location: challenge-4/agent-workflow/app -> challenge-3/agents
CHALLENGE_3_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "challenge-3", "agents"))
if CHALLENGE_3_PATH not in sys.path:
    sys.path.insert(0, CHALLENGE_3_PATH)

# Load .env from workspace root to get COSMOS and AI_FOUNDRY credentials
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ENV_FILE = os.path.join(WORKSPACE_ROOT, ".env")
loaded = load_dotenv(ENV_FILE, override=True)
logger = logging.getLogger(__name__)

# Debug: Log env loading status
logger.info(f"Loading env from: {ENV_FILE} (exists: {os.path.exists(ENV_FILE)}, loaded: {loaded})")
logger.info(f"COSMOS_ENDPOINT set: {bool(os.getenv('COSMOS_ENDPOINT'))}")
logger.info(f"COSMOS_DATABASE set: {bool(os.getenv('COSMOS_DATABASE'))}")
logger.info(f"AI_FOUNDRY_PROJECT_ENDPOINT set: {bool(os.getenv('AI_FOUNDRY_PROJECT_ENDPOINT'))}")


# =============================================================================
# A2A Server Wrappers for Challenge-3 Agents
# =============================================================================

def create_maintenance_scheduler_a2a_app():
    """Create an A2A Starlette application for the Maintenance Scheduler Agent."""
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.agent_execution import AgentExecutor, RequestContext
    from a2a.server.events.event_queue import EventQueue
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TextPart, Message

    # Get the base URL from environment or use default
    # The URL should point to where this agent's RPC endpoint is accessible
    # Must use https:// to match what the .NET workflow uses via Aspire
    default_url = os.getenv("MAINTENANCE_SCHEDULER_AGENT_SELF_URL", "https://localhost:8000/maintenance-scheduler/")
    
    agent_card = AgentCard(
        name="MaintenanceSchedulerAgent",
        description="Predictive maintenance scheduling agent that analyzes work orders, historical maintenance data, and available windows to recommend optimal maintenance schedules.",
        url=default_url,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True, pushNotifications=False),
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[
            AgentSkill(
                id="schedule_maintenance",
                name="Schedule Maintenance",
                description="Predict optimal maintenance schedule for a work order",
                tags=["maintenance", "scheduling", "predictive"],
            )
        ],
    )

    class MaintenanceSchedulerExecutor(AgentExecutor):
        """A2A executor that wraps the MaintenanceSchedulerAgent from challenge-3."""

        async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
            from maintenance_scheduler_agent import MaintenanceSchedulerAgent
            from services.cosmos_db_service import CosmosDbService

            try:
                # Extract the message text from context.message
                message = context.message
                logger.info(f"MaintenanceSchedulerExecutor received message: {message}")
                input_text = ""
                if message and message.parts:
                    # Parts are wrapped in Part(root=TextPart(...)) structure
                    for p in reversed(message.parts):
                        logger.info(f"Part: type={type(p)}, root={getattr(p, 'root', None)}")
                        # Access the inner TextPart via p.root
                        if hasattr(p, 'root') and hasattr(p.root, 'text'):
                            input_text = p.root.text
                            logger.info(f"Extracted text from p.root.text: '{input_text}'")
                            break
                else:
                    logger.warning("No message parts found in context.message")

                # Initialize services
                cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
                cosmos_key = os.getenv("COSMOS_KEY")
                database_name = os.getenv("COSMOS_DATABASE_NAME") or os.getenv("COSMOS_DATABASE")
                project_endpoint = os.getenv("AI_FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT")
                deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o")

                if not all([cosmos_endpoint, cosmos_key, database_name, project_endpoint]):
                    response_text = "Error: Missing required environment variables for MaintenanceSchedulerAgent"
                else:
                    cosmos_service = CosmosDbService(cosmos_endpoint, cosmos_key, database_name)
                    agent = MaintenanceSchedulerAgent(project_endpoint, deployment_name, cosmos_service)

                    # Parse work order ID from input (default matches challenge-3 maintenance_scheduler_agent.py)
                    work_order_id = extract_work_order_id(input_text) if input_text else None
                    if not work_order_id:
                        work_order_id = "wo-2024-468"  # fallback default
                    logger.info(f"Looking up work order: '{work_order_id}'")

                    # Get work order and run prediction
                    work_order = await cosmos_service.get_work_order(work_order_id)
                    logger.info(f"Found work order: {work_order.id} for machine: {work_order.machine_id}")
                    history = await cosmos_service.get_maintenance_history(work_order.machine_id)
                    windows = await cosmos_service.get_available_maintenance_windows(14)

                    schedule = await agent.predict_schedule(work_order, history, windows)

                    response_text = (
                        f"Maintenance Schedule Created:\n"
                        f"- Schedule ID: {schedule.id}\n"
                        f"- Machine: {schedule.machine_id}\n"
                        f"- Scheduled Date: {schedule.scheduled_date}\n"
                        f"- Risk Score: {schedule.risk_score}/100\n"
                        f"- Failure Probability: {schedule.predicted_failure_probability * 100:.1f}%\n"
                        f"- Recommended Action: {schedule.recommended_action}\n"
                        f"- Reasoning: {schedule.reasoning}"
                    )

                    await cosmos_service.save_maintenance_schedule(schedule)

            except Exception as e:
                logger.exception("MaintenanceSchedulerAgent error")
                response_text = f"Error processing maintenance schedule request: {str(e)}"

            # Send response - messageId is required by A2A protocol
            import uuid
            response_message = Message(
                messageId=str(uuid.uuid4()),
                role="agent",
                parts=[TextPart(text=response_text)],
            )
            await event_queue.enqueue_event(response_message)

        async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
            pass

    executor = MaintenanceSchedulerExecutor()
    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(agent_executor=executor, task_store=task_store)

    return A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)


def create_parts_ordering_a2a_app():
    """Create an A2A Starlette application for the Parts Ordering Agent."""
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.agent_execution import AgentExecutor, RequestContext
    from a2a.server.events.event_queue import EventQueue
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TextPart, Message

    # Get the base URL from environment or use default
    # Must use https:// to match what the .NET workflow uses via Aspire
    default_url = os.getenv("PARTS_ORDERING_AGENT_SELF_URL", "https://localhost:8000/parts-ordering/")

    agent_card = AgentCard(
        name="PartsOrderingAgent",
        description="Parts ordering agent that analyzes inventory status and generates optimized parts orders from suppliers.",
        url=default_url,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True, pushNotifications=False),
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[
            AgentSkill(
                id="order_parts",
                name="Order Parts",
                description="Generate optimized parts order for a work order",
                tags=["parts", "ordering", "inventory", "suppliers"],
            )
        ],
    )

    class PartsOrderingExecutor(AgentExecutor):
        """A2A executor that wraps the PartsOrderingAgent from challenge-3."""

        async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
            from parts_ordering_agent import PartsOrderingAgent
            from services.cosmos_db_service import CosmosDbService

            try:
                # Extract the message text from context.message
                message = context.message
                
                input_text = ""
                if message and message.parts:
                    # Parts are wrapped in Part(root=TextPart(...)) structure
                    # Get the last part to capture the previous agent's message, not the user's
                    for p in reversed(message.parts):
                        if hasattr(p, 'root') and hasattr(p.root, 'text'):
                            input_text = p.root.text
                            break

                # Initialize services
                cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
                cosmos_key = os.getenv("COSMOS_KEY")
                database_name = os.getenv("COSMOS_DATABASE_NAME") or os.getenv("COSMOS_DATABASE")
                project_endpoint = os.getenv("AI_FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT")
                deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o")

                if not all([cosmos_endpoint, cosmos_key, database_name, project_endpoint]):
                    response_text = "Error: Missing required environment variables for PartsOrderingAgent"
                else:
                    cosmos_service = CosmosDbService(cosmos_endpoint, cosmos_key, database_name)
                    agent = PartsOrderingAgent(project_endpoint, deployment_name, cosmos_service)

                    # Parse work order ID from input (default matches challenge-3 parts_ordering_agent.py)
                    work_order_id = extract_work_order_id(input_text) if input_text else None
                    if not work_order_id:
                        work_order_id = "wo-2024-468"  # fallback default

                    # Get work order and generate order
                    work_order = await cosmos_service.get_work_order(work_order_id)
                    part_numbers = [p.part_number for p in work_order.required_parts]
                    inventory = await cosmos_service.get_inventory_items(part_numbers)

                    parts_needing_order = [p for p in work_order.required_parts if not p.is_available]

                    if not parts_needing_order:
                        response_text = "All required parts are available in stock. No parts order needed."
                        await cosmos_service.update_work_order_status(work_order.id, "Ready")
                    else:
                        needed_part_numbers = [p.part_number for p in parts_needing_order]
                        suppliers = await cosmos_service.get_suppliers_for_parts(needed_part_numbers)

                        if not suppliers:
                            response_text = "Error: No suppliers found for required parts."
                        else:
                            order = await agent.generate_order(work_order, inventory, suppliers)

                            response_text = (
                                f"Parts Order Generated:\n"
                                f"- Order ID: {order.id}\n"
                                f"- Work Order: {order.work_order_id}\n"
                                f"- Supplier: {order.supplier_name}\n"
                                f"- Expected Delivery: {order.expected_delivery_date}\n"
                                f"- Total Cost: ${order.total_cost:.2f}\n"
                                f"- Items: {len(order.order_items)} part(s)"
                            )

                            await cosmos_service.save_parts_order(order)
                            await cosmos_service.update_work_order_status(work_order.id, "PartsOrdered")

            except Exception as e:
                logger.exception("PartsOrderingAgent error")
                response_text = f"Error processing parts order request: {str(e)}"

            # Send response - messageId is required by A2A protocol
            import uuid
            response_message = Message(
                messageId=str(uuid.uuid4()),
                role="agent",
                parts=[TextPart(text=response_text)],
            )
            await event_queue.enqueue_event(response_message)

        async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
            pass

    executor = PartsOrderingExecutor()
    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(agent_executor=executor, task_store=task_store)

    return A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "This workflow expects Anomaly/Fault agents to be hosted in Foundry Agent Service and referenced by ID."
        )
    return value


async def get_a2a_agent(server_url: str) -> ChatAgent:
    """Create and return an A2A ChatAgent connected to the specified server URL."""
    try:
        from agent_framework.a2a import A2AAgent
        import importlib

        a2a = importlib.import_module("agent_framework_a2a")
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "A2A support requires the 'agent-framework-a2a' package. "
            "If you're using uv, run `uv sync` in this directory."
        ) from e

    resolver_cls = getattr(a2a, "A2ACardResolver", None)
    if resolver_cls is not None:
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as http_client:
            resolver = resolver_cls(httpx_client=http_client, base_url=server_url)
            agent_card = await resolver.get_agent_card(relative_card_path=".well-known/agent-card.json")

        return A2AAgent(
            name=agent_card.name,
            description=getattr(agent_card, "description", ""),
            agent_card=agent_card,
            url=server_url,
        )

    # Fallback: older/newer A2A packages may not ship a card resolver.
    # Try the most common constructor shapes.
    for kwargs in (
        {"url": server_url},
        {"name": "RepairPlannerAgent", "description": "A2A agent", "url": server_url},
    ):
        try:
            return A2AAgent(**kwargs)
        except TypeError:
            continue

    raise RuntimeError(
        "Unable to construct A2A agent from 'agent-framework-a2a'. "
        "Please ensure the package version matches the workflow sample."
    )


def extract_text_from_message(msg: Any) -> str:
    """Helper to extract text from various message types used in the workflow."""
    text = ""
    # Priority 1: Check for AgentExecutorResponse used by framework workflows
    if hasattr(msg, 'agent_run_response') and hasattr(msg.agent_run_response, 'text'):
        text = msg.agent_run_response.text
    # Priority 2: Direct text attribute
    elif getattr(msg, 'text', None):
        text = msg.text
    # Priority 3: Nested response (e.g. wrapper)
    elif getattr(msg, 'response', None) and getattr(msg.response, 'text', None):
        text = msg.response.text
    # Priority 4: Event parameters
    elif getattr(msg, 'params', None):
        params = msg.params
        if isinstance(params, dict):
            text = params.get('text', '') or str(params)
        elif hasattr(params, 'text'):
            text = params.text
        else:
            text = str(params)
    # Priority 5: Fallback string representation
    else:
        text = str(msg)
    return text

# --- Workflow Executors ---


class RequestProcessor(Executor):
    @handler
    async def process(self, data: dict, ctx: WorkflowContext[str]) -> None:
        machine_id = data.get("machine_id")
        telemetry = data.get("telemetry")
        # Format the initial prompt for the Anomaly Agent
        prompt = f'Classify the following anomalies for machine {machine_id}: {telemetry}'
        await ctx.send_message(prompt)


def diagnosis_condition(msg) -> bool:
    """Determine if Fault Diagnosis is needed based on Anomaly Agent output."""
    logger.info(f"Evaluating diagnosis condition on message type: {type(msg)}")

    text = extract_text_from_message(msg)

    logger.info(f"Diagnosis text extracted: {text[:200]}...")

    keywords = ["critical", "warning", "high", "alert"]
    should_run = any(keyword in text.lower() for keyword in keywords)
    logger.info(f"Diagnosis condition result: {should_run}")
    return should_run

# --- Main Workflow Function ---


async def _call_foundry_agent(openai_client, agent_name: str, input_text: str) -> str:
    """Call a named Foundry agent using the OpenAI responses API with agent reference."""
    logger.info(f"Calling Foundry agent '{agent_name}' with input: {input_text[:200]}...")
    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        conversation=conversation.id,
        input=input_text,
        extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
    )
    output = response.output_text
    logger.info(f"Agent '{agent_name}' responded: {output[:200]}...")
    return output


async def run_factory_workflow(machine_id: str, telemetry: list):
    """
    Creates and runs the Factory Analysis Workflow.

    AnomalyDetectionAgent + FaultDiagnosisAgent are hosted in Foundry Agent Service
    and called via OpenAI responses API with agent references (named agents).
    """
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential as SyncDefaultAzureCredential

    project_endpoint = _require_env("AZURE_AI_PROJECT_ENDPOINT")
    repair_planner_url = os.getenv("REPAIR_PLANNER_AGENT_URL")

    # Use sync AIProjectClient to get openai_client (Foundry named agents API)
    sync_credential = SyncDefaultAzureCredential()
    project_client = AIProjectClient(endpoint=project_endpoint, credential=sync_credential)
    openai_client = project_client.get_openai_client()

    outputs = []
    try:
        # Step 1: Anomaly Classification
        anomaly_prompt = f"Classify the following anomalies for machine {machine_id}: {telemetry}"
        anomaly_result = await _call_foundry_agent(openai_client, "AnomalyClassificationAgent", anomaly_prompt)
        outputs.append(anomaly_result)

        # Step 2: Fault Diagnosis (conditional — only if anomaly detected)
        if diagnosis_condition_text(anomaly_result):
            fault_result = await _call_foundry_agent(openai_client, "FaultDiagnosisAgent", anomaly_result)
            outputs.append(fault_result)
        else:
            logger.info("No anomaly detected — skipping Fault Diagnosis")
            return outputs

        # Step 3: Repair Planner (A2A, if configured)
        if repair_planner_url:
            try:
                repair_agent = await get_a2a_agent(server_url=repair_planner_url)
                # Use agent framework to call A2A
                from agent_framework import ChatMessage, ChatOptions, Role, TextContent
                repair_msg = ChatMessage(role=Role.USER, items=[TextContent(text=fault_result)])
                repair_response = await repair_agent.get_response([repair_msg])
                repair_text = repair_response.text if hasattr(repair_response, 'text') else str(repair_response)
                outputs.append(repair_text)
                logger.info(f"RepairPlanner responded: {repair_text[:200]}...")
            except Exception as e:
                logger.warning(f"RepairPlanner A2A failed: {e}")
                outputs.append(f"RepairPlanner error: {e}")

        return outputs
    finally:
        pass


def diagnosis_condition_text(text: str) -> bool:
    """Determine if Fault Diagnosis is needed based on anomaly text output."""
    keywords = ["critical", "warning", "high", "alert"]
    return any(keyword in text.lower() for keyword in keywords)
