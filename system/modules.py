import json
from pydantic import BaseModel, Field
from typing import List
from system.schema import HiddenStoryDB, SceneOutcome, StateTracker
from system.llm_utils import generate_structured_response, generate_text_response

def run_crime_creator() -> HiddenStoryDB:
    """
    Module 1: Crime Creator (LLM)
    Generates the hidden 'Crime Story' ground truth.
    Architecture map: "Crime Creator (LLM)" -> "Hidden Story DB"
    """
    system_prompt = (
        "You are the master designer of a thrilling murder mystery. "
        "Populate the hidden backstory of a murder. Include the killer, true motive, victim, weapon, "
        "a timeline of the crime, suspects (some innocent with fake motives/alibis, one guilty), "
        "red herrings, and how the killer actively plans to interfere with the detective."
    )
    user_prompt = "Generate the complete hidden truth of the murder mystery."
    
    return generate_structured_response(system_prompt, user_prompt, HiddenStoryDB)

class ScenePromptInput(BaseModel):
    action_hint: str = Field(description="A hint of what action the detective takes.")
    obstacle_hint: str = Field(description="A hint of the obstacle the detective faces in this scene.")

def get_scene_action_obstacle(state: StateTracker) -> ScenePromptInput:
    """
    Helper function to generate an action/obstacle combo to feed into the Investigation Generator.
    Architecture map: "Meta Controller" -> Action/Obstacle hints.
    """
    system_prompt = (
        "You are the director of a suspenseful murder mystery story. "
        "Based on the state of the investigation, propose an action the detective takes next, "
        "and an obstacle they face while doing it. The obstacle should build suspense (e.g., a fleeing suspect, an uncooperative witness, a missing clue, time ticking away)."
    )
    user_prompt = f"Current state: {state.model_dump_json()}. Generate the next action and obstacle."
    return generate_structured_response(system_prompt, user_prompt, ScenePromptInput)

def run_investigation_generator(plot_num: int, ground_truth: HiddenStoryDB, state: StateTracker, action_hint: str, obstacle_hint: str) -> SceneOutcome:
    """
    Module 2: Investigation Generator (LLM)
    Generates the next scene showing the detective's progress, factoring in ground truth and obstacles.
    Architecture map: "Investigation Generator (LLM)" + Action + Obstacle + Ground Truth Constraints -> Raw Scene Outcome
    """
    system_prompt = (
        "You are the Simulation Engine for a detective solving a murder under time pressure. "
        "You must generate what happens in this scene based on the provided ground truth constraints and the state of the investigation. "
        "The detective is trying to perform an action, but faces an obstacle. "
        "If they talk to a suspect who is marked as 'lying', they must lie. "
        "If they find a clue, determine if it is a real clue or a red herring. "
        "The scene must move the plot forward but can result in either success or failure for the detective. "
        "Ensure suspense is escalated."
    )
    
    user_prompt = (
        f"PLOT POINT NUMBER: {plot_num}\n"
        f"GROUND TRUTH: {ground_truth.model_dump_json()}\n"
        f"CURRENT INVESTIGATION STATE: {state.model_dump_json()}\n\n"
        f"DETECTIVE ACTION: {action_hint}\n"
        f"OBSTACLE: {obstacle_hint}\n\n"
        "Generate the outcome of this scene."
    )
    
    outcome = generate_structured_response(system_prompt, user_prompt, SceneOutcome)
    if outcome:
        outcome.plot_point_number = plot_num
    return outcome

def run_narrator(scenes: List[SceneOutcome]) -> str:
    """
    Module 3: Narrator (LLM)
    Takes the completed sequence of scene outcomes and writes the final cohesive story.
    Architecture map: "Completed Event Sequence" -> "Narrator (LLM)" -> "Final Novel"
    """
    system_prompt = (
        "You are a master mystery novelist. You will be provided with a sequence of raw plot points "
        "detailing a detective's investigation of a murder case. Convert these raw plot points into a "
        "fluent, suspenseful, cohesive story. You must explicitly number the plot points in your text "
        "(e.g., '1. Detective Vance arrived... 2. The first suspect was...')."
    )
    
    scenes_text = json.dumps([s.model_dump() for s in scenes], indent=2)
    user_prompt = f"Write the final mystery novel based on these ordered events:\n{scenes_text}"
    
    return generate_text_response(system_prompt, user_prompt, model="gpt-4o")
