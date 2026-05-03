import os
import json
import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from openai import OpenAI

# ==========================================
# 1. Schemas & Data Structures
# ==========================================
# These Pydantic models define the structured data used
# throughout the mystery-generation pipeline.

class Suspect(BaseModel):
    # Basic suspect info used for reasoning during the investigation
    name: str = Field(description="Name of the suspect.")
    means: str = Field(description="How they could have committed the crime.")
    motive: str = Field(description="Why they would want to commit the crime.")
    opportunity: str = Field(description="Their alibi or presence at the scene.")
    is_lying: bool = Field(default=False, description="Whether this suspect will lie in testimonies.")

class HiddenStoryDB(BaseModel):
    # The full hidden truth of the case, known only to the system
    victim: str = Field(description="Name of the victim.")
    killer: str = Field(description="Name of the actual killer.")
    true_motive: str = Field(description="The real reason the killer committed the crime.")
    weapon: str = Field(description="The weapon used to commit the murder.")
    timeline: List[str] = Field(description="Timeline of the killer's actions before, during, and after the crime.")
    suspects: List[Suspect] = Field(description="List of all plausible suspects including the killer and innocent parties.")
    red_herrings: List[str] = Field(description="Irrelevant clues meant to confuse the detective.")
    interference_plan: str = Field(description="How the killer is actively trying to hide their tracks or frame others.")

class PersistentSuspenseBeat(BaseModel):
    # A single suspense mechanism that repeats across the whole story
    core_beat: str = Field(description="The one suspense idea that persists across the entire story.")
    target: str = Field(description="The main person, object, or narrative thread under pressure.")
    why_it_matters: str = Field(description="Why this beat makes solving the case fragile or urgent.")

class ScenePromptInput(BaseModel):
    # Planner output: tells the next scene generator what kind of scene to make
    action_hint: str = Field(description="The next investigative step.")
    obstacle_hint: str = Field(description="The main obstacle in that step.")
    target_suspect: Optional[str] = Field(default=None, description="Which suspect the scene primarily focuses on.")
    coverage_goal: str = Field(description="What investigation need this scene should satisfy.")
    suspense_use_in_scene: str = Field(description="How the persistent suspense beat should appear concretely in this scene.")

class SceneOutcome(BaseModel):
    # Investigation generator output: what happened in one scene
    plot_point_number: int = Field(description="Current plot step.")
    action_taken: str = Field(description="What the detective did.")
    suspect_focus: Optional[str] = Field(default=None, description="Primary suspect in the scene.")
    clue_found: Optional[str] = Field(default=None, description="Concrete clue found in this scene.")
    testimony_gained: Optional[str] = Field(default=None, description="Statement gained from suspect or witness.")
    alibi_status: Optional[str] = Field(default=None, description="confirmed / contradicted / unclear")
    means_tested: bool = Field(default=False, description="Whether the suspect's means were examined.")
    motive_tested: bool = Field(default=False, description="Whether the suspect's motive was examined.")
    opportunity_tested: bool = Field(default=False, description="Whether the suspect's opportunity was examined.")
    suspect_cleared: bool = Field(default=False, description="Whether this suspect was ruled out in this scene.")
    weapon_relevance: Optional[str] = Field(default=None, description="How this scene connects to the murder weapon.")
    motive_relevance: Optional[str] = Field(default=None, description="How this scene connects to the true motive.")
    timeline_fact_verified: Optional[str] = Field(default=None, description="Which timeline fact was verified.")
    red_herring_used: Optional[str] = Field(default=None, description="A misleading clue introduced or revisited.")
    red_herring_resolved: Optional[str] = Field(default=None, description="Which misleading clue was explained away.")
    interference_exposed: Optional[str] = Field(default=None, description="How the killer's cover-up was exposed.")

    # Tracks how the persistent suspense beat shows up in this scene
    suspense_manifestation: str = Field(
        description="The concrete way the persistent suspense beat appears in this scene."
    )
    suspense_consequence: str = Field(
        description="How that suspense event makes the next step riskier, harder, or more urgent."
    )

    # Natural-language explanation of what happened and why it matters
    outcome: str = Field(description="What happened in the scene.")
    theory_progress: str = Field(description="How the case became more solvable after this scene.")
    weapon_confirmed: bool = Field(default=False, description="Whether this scene confirms the murder weapon.")
    motive_confirmed: bool = Field(default=False, description="Whether this scene confirms the true motive.")

class StateTracker(BaseModel):
    # Global investigation state that gets updated after every scene
    current_plot_count: int = Field(default=0)
    known_clues: List[str] = Field(default_factory=list)
    testimonies: Dict[str, str] = Field(default_factory=dict)

    # Suspect coverage tracking
    suspects_all: List[str] = Field(default_factory=list)
    suspects_introduced: List[str] = Field(default_factory=list)
    suspects_interviewed: List[str] = Field(default_factory=list)
    suspects_cleared: List[str] = Field(default_factory=list)
    suspects_with_means_checked: List[str] = Field(default_factory=list)
    suspects_with_motive_checked: List[str] = Field(default_factory=list)
    suspects_with_opportunity_checked: List[str] = Field(default_factory=list)

    # Case detail coverage tracking
    verified_timeline_events: List[str] = Field(default_factory=list)
    red_herrings_introduced: List[str] = Field(default_factory=list)
    red_herrings_resolved: List[str] = Field(default_factory=list)
    interference_exposed_points: List[str] = Field(default_factory=list)

    # Flags for whether core mystery pieces are fully supported
    confirmed_weapon: bool = Field(default=False)
    confirmed_motive: bool = Field(default=False)
    final_theory_ready: bool = Field(default=False)

    # A simple countdown mechanic to add urgency
    remaining_time: int = Field(default=24)
    completed_scenes: List[SceneOutcome] = Field(default_factory=list)

    # Persistent suspense tracking across scenes
    persistent_suspense: Optional[PersistentSuspenseBeat] = Field(default=None)
    suspense_history: List[str] = Field(default_factory=list)
    suspense_consequences: List[str] = Field(default_factory=list)

# ==========================================
# 2. LLM Utilities
# ==========================================
# Shared helper functions for calling the OpenAI API.

def get_openai_client():
    # Try environment variable first
    api_key = os.environ.get("OPENAI_API_KEY")

    # If not found, try Streamlit secrets
    if not api_key:
        try:
            if "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            pass

    # Stop the app if no key is available
    if not api_key:
        st.error("Missing OPENAI_API_KEY. Please set it in environment variables or Streamlit secrets.")
        st.stop()

    return OpenAI(api_key=api_key)

def generate_structured_response(
    system_prompt: str,
    user_prompt: str,
    response_model: type[BaseModel],
    model: str = "gpt-4o-mini"
):
    """
    Calls the model and parses the response directly into a Pydantic model.
    This is used whenever you want consistent structured outputs.
    """
    client = get_openai_client()
    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=response_model,
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

def generate_text_response(system_prompt: str, user_prompt: str, model: str = "gpt-4o"):
    """
    Calls the model for normal text output.
    This is mainly used for the narrator, which writes the final story.
    """
    client = get_openai_client()
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

# ==========================================
# 3. Crime Creator
# ==========================================
# This creates the hidden ground truth of the entire mystery.

def run_crime_creator() -> HiddenStoryDB:
    system = """
    You are the master designer of a logically consistent murder mystery.

    Generate a Hidden Story DB with:
    - one victim
    - one actual killer
    - a clear true motive
    - a specific weapon or method
    - a detailed timeline
    - 4 plausible suspects total, including the killer
    - at least 2 red herrings
    - a realistic interference plan by the killer

    Rules:
    - all suspects must be plausible
    - innocent suspects must have believable means, motive, and opportunity but still be ultimately exonerable
    - the timeline must support later investigation
    - the solution must be solvable
    - the interference plan should create recurring opportunities for suspense
    """
    user = "Generate the complete hidden truth of the murder mystery."
    return generate_structured_response(system, user, HiddenStoryDB)

# ==========================================
# 4. Suspense + Coverage Helpers
# ==========================================
# These helper functions decide the recurring suspense beat
# and summarize state for later prompts.

def choose_persistent_suspense_beat(gt: HiddenStoryDB) -> PersistentSuspenseBeat:
    system = """
    You are choosing ONE persistent suspense beat for a murder mystery.

    Pick exactly one suspense beat that can recur throughout the whole investigation.

    Good suspense beat examples:
    - case closure deadline
    - detective is being threatened
    - a key piece of evidence is being quietly erased or altered

    Rules:
    1. Choose only one core suspense beat.
    2. It must naturally fit the killer's interference plan and hidden story.
    3. It must be concrete enough to reappear in multiple scenes.
    4. It must stay relevant until the final reveal.
    5. Do not create multiple options.
    6. Keep it usable across many scenes.
    """

    user = f"""
    HIDDEN STORY DB:
    {gt.model_dump_json(indent=2)}

    Choose the single best persistent suspense beat.
    """

    beat = generate_structured_response(system, user, PersistentSuspenseBeat)

    # Fallback in case the model call fails
    if beat is None:
        return PersistentSuspenseBeat(
            core_beat="The killer is trying to keep the truth unstable long enough for the detective to lose control of the story.",
            target="the investigation's version of what happened",
            why_it_matters="If the detective cannot stabilize evidence and testimony quickly, the false version of the case may become the accepted one."
        )
    return beat

def initialize_state_from_ground_truth(gt: HiddenStoryDB) -> StateTracker:
    # Create the initial investigation state from the hidden story
    suspense = choose_persistent_suspense_beat(gt)
    return StateTracker(
        suspects_all=[s.name for s in gt.suspects],
        persistent_suspense=suspense
    )

def case_ready_for_final_reveal(gt: HiddenStoryDB, state: StateTracker) -> bool:
    """
    Determines whether the investigation has covered enough material
    to support a satisfying and justified final reveal.
    """
    nonkiller_count = len([s for s in gt.suspects if s.name != gt.killer])
    return (
        all(name in state.suspects_introduced for name in state.suspects_all)
        and all(name in state.suspects_interviewed for name in state.suspects_all)
        and len(state.suspects_cleared) >= nonkiller_count
        and state.confirmed_weapon
        and state.confirmed_motive
        and len(state.verified_timeline_events) >= min(4, len(gt.timeline))
        and len(state.red_herrings_resolved) >= len(gt.red_herrings)
    )

def compact_state_summary(gt: HiddenStoryDB, state: StateTracker) -> str:
    """
    Creates a compact JSON summary of the current investigation state.
    This is fed into prompts so the model has context without too much bloat.
    """
    persistent_suspense_json = (
        state.persistent_suspense.model_dump()
        if state.persistent_suspense is not None
        else None
    )

    return json.dumps(
        {
            "current_plot_count": state.current_plot_count,
            "suspects_all": state.suspects_all,
            "suspects_introduced": state.suspects_introduced,
            "suspects_interviewed": state.suspects_interviewed,
            "suspects_cleared": state.suspects_cleared,
            "means_checked": state.suspects_with_means_checked,
            "motive_checked": state.suspects_with_motive_checked,
            "opportunity_checked": state.suspects_with_opportunity_checked,
            "known_clues": state.known_clues[-8:],
            "verified_timeline_events": state.verified_timeline_events,
            "red_herrings_introduced": state.red_herrings_introduced,
            "red_herrings_resolved": state.red_herrings_resolved,
            "interference_exposed_points": state.interference_exposed_points,
            "confirmed_weapon": state.confirmed_weapon,
            "confirmed_motive": state.confirmed_motive,
            "remaining_time": state.remaining_time,
            "persistent_suspense": persistent_suspense_json,
            "recent_suspense_history": state.suspense_history[-6:],
            "recent_suspense_consequences": state.suspense_consequences[-6:],
            "final_theory_ready": state.final_theory_ready,
        },
        indent=2
    )

def recent_scene_summary(state: StateTracker, max_scenes: int = 3) -> str:
    """
    Returns the most recent scene outcomes so the planner
    can avoid repetition and build naturally on what happened.
    """
    if not state.completed_scenes:
        return "No prior scenes."
    trimmed = [s.model_dump() for s in state.completed_scenes[-max_scenes:]]
    return json.dumps(trimmed, indent=2)

# ==========================================
# 5. Planner / Meta-Controller
# ==========================================
# The planner chooses what the next scene should accomplish.

def get_scene_action_obstacle(gt: HiddenStoryDB, state: StateTracker) -> ScenePromptInput:
    system = """
    You are the investigation planner for a murder mystery.

    Your job is to choose the next best scene so that:
    1. the hidden story is fully investigated
    2. the same persistent suspense beat continues across the whole story

    COVERAGE RULES:
    1. Every suspect must appear in at least one meaningful scene.
    2. Every suspect must be interviewed or examined.
    3. Every suspect's means, motive, and opportunity must be tested.
    4. Innocent suspects must be ruled out with evidence, not ignored.
    5. The murder weapon must be verified before the final reveal.
    6. The true motive must be verified before the final reveal.
    7. The killer's timeline must be gradually verified.
    8. Red herrings must be introduced and later resolved.
    9. The killer's interference plan should actively complicate the investigation.
    10. Do not repeat the same confrontation unless new evidence justifies it.

    SUSPENSE RULES:
    1. Use the SAME persistent suspense beat in every scene.
    2. Do not invent a new main suspense concept.
    3. The suspense must show up as a concrete event, not vague language.
    4. The suspense event in this scene should make the next scene more fragile or urgent.
    5. The suspense beat should evolve, not reset.
    6. Avoid generic phrasing like 'tension rises' or 'pressure increases' unless tied to a real event.

    Output:
    - action_hint
    - obstacle_hint
    - target_suspect
    - coverage_goal
    - suspense_use_in_scene
    """

    persistent_suspense_json = (
        state.persistent_suspense.model_dump_json(indent=2)
        if state.persistent_suspense is not None
        else "None"
    )

    user = f"""
    HIDDEN STORY DB:
    {gt.model_dump_json(indent=2)}

    CURRENT STATE:
    {compact_state_summary(gt, state)}

    PERSISTENT SUSPENSE BEAT:
    {persistent_suspense_json}

    RECENT SCENES:
    {recent_scene_summary(state)}

    Choose the next scene.
    """

    scene = generate_structured_response(system, user, ScenePromptInput)

    # Fallback plan if the model fails
    if scene is None:
        return ScenePromptInput(
            action_hint="The detective pursues the most unresolved suspect or clue.",
            obstacle_hint="The killer's interference makes the next piece of truth unstable or difficult to secure.",
            target_suspect=None,
            coverage_goal="Advance the most urgent unresolved part of the case.",
            suspense_use_in_scene="The persistent suspense beat appears as a concrete disruption that makes the next step harder to trust or verify."
        )
    return scene

# ==========================================
# 6. Investigation Generator
# ==========================================
# This turns the planner's scene idea into an actual scene outcome.

def run_investigation_generator(
    plot_num: int,
    gt: HiddenStoryDB,
    state: StateTracker,
    scene_plan: ScenePromptInput,
    is_final_scene: bool = False
) -> SceneOutcome:

    # Use a stricter prompt for the final reveal scene
    if is_final_scene:
        system = """
        You are the simulation engine for a detective solving a murder.

        This is the final reveal scene.

        You must explicitly state:
        1. who committed the murder
        2. the exact motive
        3. the exact weapon or method
        4. the step-by-step timeline of the murder
        5. why each other suspect is not the killer
        6. how each red herring misled the investigation
        7. how the killer interfered with the investigation
        8. what evidence proves the conclusion

        FINAL SCENE SUSPENSE RULES:
        1. The same persistent suspense beat must appear one last time.
        2. This final appearance should show that beat failing or collapsing under the truth.
        3. Do not invent a new suspense idea in the final scene.
        4. The suspense manifestation must still be concrete and observable.
        5. The suspense consequence should make clear what almost went wrong before the detective stabilized the case.

        Return valid SceneOutcome.
        """
    else:
        system = """
        You are the simulation engine for a detective solving a murder.

        Generate the next scene using:
        - the hidden ground truth
        - the investigation state
        - the planned next scene
        - the persistent suspense beat

        INVESTIGATION RULES:
        1. Advance the investigation concretely.
        2. Use specific evidence and suspect reasoning.
        3. If the suspect is innocent, move toward ruling them out.
        4. clue_found must be specific.
        5. testimony_gained must be specific if present.
        6. Do not contradict the hidden story.

        SUSPENSE RULES:
        1. The persistent suspense beat must appear in this scene as a concrete event.
        2. Do not replace it with a different suspense idea.
        3. Do not write vague phrases like 'tension rises' or 'pressure increases.'
        4. The suspense manifestation must be observable and story-relevant.
        5. The suspense consequence must create pressure that carries into the next scene.
        6. The suspense should feel like the same recurring problem taking a new form.

        Return valid SceneOutcome.
        """

    persistent_suspense_json = (
        state.persistent_suspense.model_dump_json(indent=2)
        if state.persistent_suspense is not None
        else "None"
    )

    user = f"""
    PLOT POINT NUMBER:
    {plot_num}

    HIDDEN STORY DB:
    {gt.model_dump_json(indent=2)}

    CURRENT STATE:
    {compact_state_summary(gt, state)}

    PERSISTENT SUSPENSE BEAT:
    {persistent_suspense_json}

    PLANNED SCENE:
    {scene_plan.model_dump_json(indent=2)}

    Generate the scene outcome.
    """

    out = generate_structured_response(system, user, SceneOutcome)

    # Force the scene number onto the output if generation worked
    if out:
        out.plot_point_number = plot_num
    return out

# ==========================================
# 7. State Updates
# ==========================================
# After each scene, this function updates the investigation record.

def update_state_from_scene(gt: HiddenStoryDB, state: StateTracker, outcome: SceneOutcome):
    # Add new clue if it has not already been recorded
    if outcome.clue_found and outcome.clue_found not in state.known_clues:
        state.known_clues.append(outcome.clue_found)

    # Mark suspect as introduced/interviewed if they were the scene focus
    if outcome.suspect_focus:
        if outcome.suspect_focus not in state.suspects_introduced:
            state.suspects_introduced.append(outcome.suspect_focus)
        if outcome.suspect_focus not in state.suspects_interviewed:
            state.suspects_interviewed.append(outcome.suspect_focus)

    # Store testimony tied to that suspect
    if outcome.testimony_gained and outcome.suspect_focus:
        state.testimonies[outcome.suspect_focus] = outcome.testimony_gained

    # Track which suspects have had means/motive/opportunity tested
    if outcome.suspect_focus and outcome.means_tested and outcome.suspect_focus not in state.suspects_with_means_checked:
        state.suspects_with_means_checked.append(outcome.suspect_focus)

    if outcome.suspect_focus and outcome.motive_tested and outcome.suspect_focus not in state.suspects_with_motive_checked:
        state.suspects_with_motive_checked.append(outcome.suspect_focus)

    if outcome.suspect_focus and outcome.opportunity_tested and outcome.suspect_focus not in state.suspects_with_opportunity_checked:
        state.suspects_with_opportunity_checked.append(outcome.suspect_focus)

    # Only non-killers can be added to cleared suspects
    if outcome.suspect_focus and outcome.suspect_cleared and outcome.suspect_focus != gt.killer:
        if outcome.suspect_focus not in state.suspects_cleared:
            state.suspects_cleared.append(outcome.suspect_focus)

    # These flags currently turn true if either relevance OR explicit confirmation appears
    if outcome.weapon_confirmed or outcome.weapon_relevance:
        state.confirmed_weapon = True

    if outcome.motive_confirmed or outcome.motive_relevance:
        state.confirmed_motive = True

    # Record verified timeline facts
    if outcome.timeline_fact_verified and outcome.timeline_fact_verified not in state.verified_timeline_events:
        state.verified_timeline_events.append(outcome.timeline_fact_verified)

    # Track red herrings
    if outcome.red_herring_used and outcome.red_herring_used not in state.red_herrings_introduced:
        state.red_herrings_introduced.append(outcome.red_herring_used)

    if outcome.red_herring_resolved and outcome.red_herring_resolved not in state.red_herrings_resolved:
        state.red_herrings_resolved.append(outcome.red_herring_resolved)

    # Track when the killer's interference is exposed
    if outcome.interference_exposed and outcome.interference_exposed not in state.interference_exposed_points:
        state.interference_exposed_points.append(outcome.interference_exposed)

    # Add suspense tracking for continuity across scenes
    if outcome.suspense_manifestation:
        state.suspense_history.append(outcome.suspense_manifestation)

    if outcome.suspense_consequence:
        state.suspense_consequences.append(outcome.suspense_consequence)

    # Store the whole scene outcome
    state.completed_scenes.append(outcome)

    # Decrease available time to reinforce urgency
    state.remaining_time -= 1

    # Re-check whether the case is ready for the final reveal
    state.final_theory_ready = case_ready_for_final_reveal(gt, state)

def run_narrator(gt: HiddenStoryDB, scenes: List[SceneOutcome], state: StateTracker) -> str:
    """
    Converts the ordered investigation record into a polished, continuous mystery story.
    """
    system = """
    You are a mystery novelist.

    Transform the ordered investigation record into a cohesive, immersive detective story.

    The story must preserve:
    - the victim
    - every suspect and their investigative role
    - the true culprit
    - the true motive
    - the true weapon or method
    - the real timeline of the crime
    - the red herrings and how they were resolved
    - the killer's interference with the investigation
    - the persistent suspense beat

    STYLE RULES:
    1. Do NOT number scenes or label plot points.
    2. Do NOT write like a summary or report.
    3. Write as a continuous, flowing story with natural transitions.
    4. Follow the chronological order of discoveries, but blend them smoothly.
    5. Let clues emerge through action, dialogue, and observation.
    6. Maintain the same persistent suspense beat throughout.
    7. Avoid repetitive phrasing like “then they investigated.”
    8. Write in the style of contemporary detective fiction: immersive, clear, and suspenseful.

    CRITICAL ENDING REQUIREMENTS:
    The final portion of the story MUST include a clear and explicit reconstruction of the crime.

    This reconstruction must:
    1. Clearly state WHY the killer committed the crime (motive).
    2. Clearly explain HOW the crime was physically carried out (method and execution).
    3. Walk through the timeline step-by-step in natural language.
    4. Show how the evidence discovered supports each part of the reconstruction.
    5. Explicitly explain why each other suspect is not the killer.
    6. Show how the killer’s interference failed in the end.
    7. Feel like a dramatic but precise explanation, not a vague summary.

    The reader should finish the story with ZERO ambiguity about:
    - what happened
    - how it happened
    - why it happened

    The ending should feel like the truth finally locking into place after being unstable.

    Do NOT rush the ending.
    """

    persistent_suspense_json = (
        state.persistent_suspense.model_dump_json(indent=2)
        if state.persistent_suspense else "None"
    )

    user = f"""
    Adapt the following into a continuous mystery story.

    HIDDEN STORY DB:
    {gt.model_dump_json(indent=2)}

    PERSISTENT SUSPENSE BEAT:
    {persistent_suspense_json}

    ORDERED SCENE OUTCOMES:
    {json.dumps([s.model_dump() for s in scenes], indent=2)}

    Important:
    - Preserve the chronological order of discoveries.
    - Include all suspects meaningfully.
    - Ensure the ending fully reconstructs the crime in detail.
    """

    return generate_text_response(system, user)

# ==========================================
# 9. Meta-Controller Loop
# ==========================================
# This is the main engine that coordinates all major components.

def run_meta_controller(yield_updates: bool = True) -> Tuple[Optional[HiddenStoryDB], Optional[str], Optional[StateTracker]]:
    if yield_updates:
        st.write("🕵️ **Step 1:** Initializing Crime Creator...")

    # Generate the full hidden crime
    ground_truth = run_crime_creator()
    if not ground_truth:
        return None, "Error generating crime.", None

    if yield_updates:
        st.success(f"Crime generated! The killer is secretly: {ground_truth.killer}")

    # Start tracking state
    state = initialize_state_from_ground_truth(ground_truth)

    if yield_updates and state.persistent_suspense is not None:
        st.write("**Persistent Suspense Beat Chosen:**")
        st.write(f"**Core Beat:** {state.persistent_suspense.core_beat}")
        st.write(f"**Target:** {state.persistent_suspense.target}")
        st.write(f"**Why It Matters:** {state.persistent_suspense.why_it_matters}")

    # Force a minimum amount of development before ending
    MIN_PLOT_POINTS = 15
    MAX_PLOT_POINTS = 18

    # Keep generating scenes until enough coverage is done
    while True:
        needs_more_coverage = not case_ready_for_final_reveal(ground_truth, state)
        under_minimum = state.current_plot_count < MIN_PLOT_POINTS

        # Stop only when minimum length is met and coverage is complete
        if not needs_more_coverage and not under_minimum:
            break

        # Safety cap so the loop cannot run forever
        if state.current_plot_count >= MAX_PLOT_POINTS:
            break

        state.current_plot_count += 1

        # Planner chooses the next scene
        scene_plan = get_scene_action_obstacle(ground_truth, state)
        if not scene_plan:
            return None, "Error generating scene plan.", state

        if yield_updates:
            st.info(
                f"**Plot Point {state.current_plot_count}:** {scene_plan.action_hint}\n\n"
                f"**Coverage Goal:** {scene_plan.coverage_goal}\n\n"
                f"**Obstacle:** {scene_plan.obstacle_hint}\n\n"
                f"**Suspense Use In Scene:** {scene_plan.suspense_use_in_scene}"
            )

        # Investigation generator creates the actual scene result
        outcome = run_investigation_generator(
            state.current_plot_count,
            ground_truth,
            state,
            scene_plan,
            is_final_scene=False
        )

        if not outcome:
            return None, "Error generating scene outcome.", state

        # Update tracking state after the scene
        update_state_from_scene(ground_truth, state, outcome)

        if yield_updates:
            with st.expander(f"Scene {state.current_plot_count} Outcome"):
                st.write(f"**Action:** {outcome.action_taken}")
                st.write(f"**Suspect Focus:** {outcome.suspect_focus}")
                st.write(f"**Clue Found:** {outcome.clue_found}")
                st.write(f"**Testimony:** {outcome.testimony_gained}")
                st.write(f"**Timeline Verified:** {outcome.timeline_fact_verified}")
                st.write(f"**Red Herring Resolved:** {outcome.red_herring_resolved}")
                st.write(f"**Interference Exposed:** {outcome.interference_exposed}")
                st.write(f"**Suspense Manifestation:** {outcome.suspense_manifestation}")
                st.write(f"**Suspense Consequence:** {outcome.suspense_consequence}")
                st.write(f"**Outcome:** {outcome.outcome}")
                st.write(f"**Theory Progress:** {outcome.theory_progress}")

    # If the case is ready, generate one formal final-reveal scene
    if case_ready_for_final_reveal(ground_truth, state) and state.current_plot_count < MAX_PLOT_POINTS:
        state.current_plot_count += 1

        final_plan = ScenePromptInput(
            action_hint="The detective gathers all suspects and delivers the final reconstruction of the crime.",
            obstacle_hint="The killer makes one last attempt to keep the truth unstable before the case locks into an official version.",
            target_suspect=ground_truth.killer,
            coverage_goal="Deliver the final reveal using weapon, motive, timeline, suspect elimination, red herrings, and interference evidence.",
            suspense_use_in_scene="The persistent suspense beat appears one last time as a concrete final attempt to preserve the false version of events, but it fails under the full weight of the evidence."
        )

        final_outcome = run_investigation_generator(
            state.current_plot_count,
            ground_truth,
            state,
            final_plan,
            is_final_scene=True
        )

        if final_outcome:
            update_state_from_scene(ground_truth, state, final_outcome)

            if yield_updates:
                with st.expander(f"Final Reveal Scene {state.current_plot_count}"):
                    st.write(f"**Suspense Manifestation:** {final_outcome.suspense_manifestation}")
                    st.write(f"**Suspense Consequence:** {final_outcome.suspense_consequence}")
                    st.write(f"**Outcome:** {final_outcome.outcome}")
                    st.write(f"**Theory Progress:** {final_outcome.theory_progress}")

    if yield_updates:
        st.write("✍️ **Step 3:** Investigation complete! Passing structured investigation record to the Narrator...")

    # Convert structured scenes into final prose story
    final_story = run_narrator(ground_truth, state.completed_scenes, state)
    return ground_truth, final_story, state

# ==========================================

# ==========================================
# 10. Phase II Interactive Storytelling Models
# ==========================================
# These models turn the Phase I generated investigation into a playable text game.
# The player acts as the detective. Their actions are categorized as:
# - constituent: part of the planned story event
# - consistent: extra action that fits the world and does not break causal links
# - exceptional: action that threatens an active causal link or makes the mystery unsolvable

class Room(BaseModel):
    name: str = Field(description="Room/location name.")
    description: str = Field(description="What the detective sees in this room.")
    exits: Dict[str, str] = Field(default_factory=dict, description="Direction/action to neighboring room name.")
    objects: List[str] = Field(default_factory=list, description="Objects currently visible in the room.")
    hidden_objects: List[str] = Field(default_factory=list, description="Objects physically in the room but not visible until discovered by investigation.")
    characters: List[str] = Field(default_factory=list, description="Characters currently in the room.")

class SceneRoomAssignment(BaseModel):
    scene_index: int = Field(description="1-based index of the investigation scene.")
    room_name: str = Field(description="Unique, concrete physical room/location assigned to this scene.")
    reason: str = Field(description="Why this room fits the planned action and scene content.")

class SynthesizedRoom(BaseModel):
    name: str = Field(description="Clear unique physical room/location name.")
    description: str = Field(description="Short first-visit description for this room.")
    connected_rooms: List[str] = Field(default_factory=list, description="Nearby rooms reachable from this room.")

class WorldLocationPlan(BaseModel):
    rooms: List[SynthesizedRoom] = Field(description="All unique physical rooms needed for the whole 15-event mystery.")
    assignments: List[SceneRoomAssignment] = Field(description="Scene-to-room assignment for each investigation scene.")
    weapon_room: str = Field(description="Room where the murder weapon physically exists as hidden evidence, without revealing it to the player.")

class InteractiveEvent(BaseModel):
    event_id: int
    title: str
    location: str
    planned_action: str
    preconditions: List[str] = Field(default_factory=list)
    effects: List[str] = Field(default_factory=list)
    causal_links: List[str] = Field(default_factory=list)
    clue_gate: Optional[str] = Field(default=None, description="Clue/testimony needed before this event should fire.")
    completed: bool = False
    blocked: bool = False

class WorldState(BaseModel):
    rooms: Dict[str, Room] = Field(default_factory=dict)
    player_location: str = "Crime Scene"
    inventory: List[str] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    damaged_or_destroyed: List[str] = Field(default_factory=list)
    locked_locations: List[str] = Field(default_factory=list)
    unavailable_characters: List[str] = Field(default_factory=list)
    # Tracks where each NPC currently is so a character cannot appear in two rooms at once.
    character_locations: Dict[str, str] = Field(default_factory=dict)
    # Tracks which rooms have already received a full first-visit description.
    visited_rooms: List[str] = Field(default_factory=list)
    # The murder weapon exists as a physical object in one room, even if the player has not identified it yet.
    murder_weapon_location: Optional[str] = None
    murder_weapon_found: bool = False
    cause_of_death_found: bool = False
    final_accusation: Optional[str] = None
    event_index: int = 0
    solved: bool = False
    turns: int = 0
    last_classification: Optional[str] = None
    game_log: List[str] = Field(default_factory=list)
    # Stores only the latest NPC movement that the detective could physically notice this turn.
    # This prevents old movement notes from being narrated repeatedly.
    last_visible_npc_movement_note: Optional[str] = None

class ActionInterpretation(BaseModel):
    intent: str = Field(description="Short verb phrase summarizing what the player attempted.")
    action_type: str = Field(description="move / inspect / interview / take / destroy / lock / accuse / wait / other")
    target: Optional[str] = None
    location_target: Optional[str] = None
    suspect_target: Optional[str] = None
    likely_effects: List[str] = Field(default_factory=list)
    threatens_mystery: bool = False
    commonsense_risk: Optional[str] = None

class ActionEvaluation(BaseModel):
    classification: str = Field(description="constituent / consistent / exceptional")
    reason: str
    world_updates: List[str] = Field(default_factory=list)
    response_text: str
    should_advance_event: bool = False
    accommodation_needed: bool = False
    intervention_needed: bool = False

class AccommodationResult(BaseModel):
    response_text: str
    repaired_events: List[InteractiveEvent] = Field(default_factory=list)
    world_updates: List[str] = Field(default_factory=list)
    mystery_still_solvable: bool = True

class InterventionResult(BaseModel):
    response_text: str
    prevented_world_updates: List[str] = Field(default_factory=list)
    timeline_preserved: bool = True


class SceneDiscoveryMarker(BaseModel):
    scene_index: int = Field(description="1-based scene index after adaptation.")
    reveals_cause_of_death: bool = Field(default=False, description="True only if this scene is the plot point where the detective learns the cause of death.")
    reveals_murder_weapon: bool = Field(default=False, description="True only if this scene is the plot point where the detective identifies or finds the murder weapon.")
    reason: str = Field(description="Why the marker applies to this scene.")


class TimelineAdaptationResult(BaseModel):
    """Event Timeline Adaptation output for Phase II.

    The Phase I generator still creates the actual investigation plot points. This model
    adapts those generated plot points into exactly 14 playable pre-accusation events,
    removes repeated beats, and marks which generated scenes reveal cause of death and
    murder weapon. It does not use hardcoded replacement scenes.
    """
    scenes: List[SceneOutcome] = Field(description="Exactly 14 non-repeating Phase-I-derived scenes before the final accusation.")
    discovery_markers: List[SceneDiscoveryMarker] = Field(description="Markers showing where cause of death and murder weapon are discovered.")
    removed_or_merged_repetitions: List[str] = Field(default_factory=list, description="Brief notes on repeated scenes that were merged, rewritten, or removed.")
    causal_consistency_notes: str = Field(description="How the sequence makes each later event motivated by earlier information.")


class ActionEventMatch(BaseModel):
    matches_current_event: bool = Field(description="Whether the player's interpreted action satisfies the current planned event.")
    reason: str = Field(description="Short explanation grounded in the event, current room, known facts, and player intent.")




class DramaToolDecision(BaseModel):
    tool: str = Field(description="accommodation or intervention")
    reason: str = Field(description="Why this tool is appropriate for the exceptional player action.")


class CausalThreatAssessment(BaseModel):
    threatens_timeline: bool = Field(description="Whether the action threatens future event preconditions, causal links, or mystery solvability.")
    threatened_link: Optional[str] = Field(default=None, description="Specific threatened link or commonsense threat if any.")
    reason: str = Field(description="Why the action does or does not threaten the story plan.")


FINAL_INTERACTIVE_EVENT_COUNT = 15

PHYSICAL_ROOM_DESCRIPTIONS = {}
BANNED_ROOM_WORDS = ["interrogation", "interview", "confrontation", "accusation", "reveal", "questioning"]

def sanitize_room_name(name: Optional[str]) -> str:
    """Clean the room name, returning a safe default if missing."""
    if not name:
        return "Crime Scene"
    cleaned = name.strip().replace("\n", " ").strip('"').title()[:60]
    return cleaned if cleaned else "Crime Scene"

def ensure_room_exists(world: WorldState, room_name: str):
    """Create a reachable physical room if the event plan names a specific place not in the base map."""
    room_name = sanitize_room_name(room_name)
    if room_name not in world.rooms:
        world.rooms[room_name] = Room(
            name=room_name,
            description=f"A distinct physical location tied to the current lead: {room_name}. Details here may clarify the crime timeline."
        )
    # Make dynamically discovered rooms reachable without breaking the simple graph.
    if room_name != "Crime Scene" and room_name not in world.rooms.get("Crime Scene", Room(name="Crime Scene", description="")).exits.values():
        direction_key = f"to {room_name}"
        world.rooms["Crime Scene"].exits[direction_key] = room_name
    if room_name != "Crime Scene" and "back to Crime Scene" not in world.rooms[room_name].exits:
        world.rooms[room_name].exits["back to Crime Scene"] = "Crime Scene"

def extract_explicit_physical_location(text: str) -> Optional[str]:
    """Detect explicit locations via LLM."""
    if not text:
        return None
    system = "Extract the explicit physical location from the text. Return ONLY the location name (2-4 words). If no physical location is mentioned, return 'None'."
    user = f"Text: {text}"
    res = generate_text_response(system, user, model="gpt-4o-mini")
    if res and res.lower() != "none":
        return sanitize_room_name(res)
    return None

def normalize_event_ids(events: List[InteractiveEvent]) -> List[InteractiveEvent]:
    """Guarantee exactly 15 sequential, unique event ids with no missing numbers."""
    fixed = events[:FINAL_INTERACTIVE_EVENT_COUNT]
    for idx, event in enumerate(fixed, start=1):
        event.event_id = idx
        if idx == FINAL_INTERACTIVE_EVENT_COUNT:
            event.title = "Final Accusation"
        elif not event.title:
            event.title = f"Evidence Beat {idx}"
    return fixed

def action_words(text: str) -> set:
    stop = {
        "the", "a", "an", "to", "and", "or", "of", "in", "on", "at", "with", "from", "for",
        "detective", "event", "can", "has", "have", "is", "are", "be", "this", "that", "into"
    }
    cleaned = ''.join(ch.lower() if ch.isalnum() or ch.isspace() else ' ' for ch in text)
    return {w for w in cleaned.split() if len(w) > 2 and w not in stop}


def fallback_room_for_scene(scene: SceneOutcome, gt: HiddenStoryDB) -> str:
    """Small technical fallback used only if the LLM world synthesizer fails.

    Normal room assignment is handled by synthesize_world_locations(), which sees all
    scenes together and assigns unique physical rooms with an LLM. This fallback avoids
    keyword-based semantic decisions.
    """
    return "Crime Scene"


def infer_event_location(gt: HiddenStoryDB, scene: SceneOutcome) -> str:
    # First use deterministic extraction from the planned action/outcome. This prevents
    # scenes that explicitly say “investigate the rooftop/storage room/etc.” from being
    # flattened into the generic Crime Scene.
    deterministic = fallback_room_for_scene(scene, gt)
    if deterministic != "Crime Scene":
        return deterministic

    system = """
    You convert a detective scene into one concise playable text-game location.
    Return only a concrete physical place name, 2 to 4 words.
    Good examples: Crime Scene, Police Station, Records Office, Forensics Lab, Evidence Locker, Victim's Apartment, Security Office, Medical Examiner's Office, Apartment Hallway, Courtyard.
    Bad examples: Interrogation Room, Interview Room, Confrontation Room, Reveal Room, Accusation Room.
    """
    user = f"""
    Hidden case: {gt.model_dump_json(indent=2)}
    Scene: {scene.model_dump_json(indent=2)}
    What is the best concrete physical room/location for this scene?
    """
    text = generate_text_response(system, user, model="gpt-4o-mini")
    if not text:
        return fallback_room_for_scene(scene, gt)
    return sanitize_room_name(text)




def synthesize_world_locations(gt: HiddenStoryDB, scenes: List[SceneOutcome]) -> WorldLocationPlan:
    """Create all room names in one global pass, then assign every scene to one room.

    This replaces the older one-scene-at-a-time location inference. The LLM sees the
    whole pre-accusation investigation plan at once, so it can avoid overlapping names like
    "Office" vs "Victim's Office" and keep locations aligned with planned actions.
    """
    scene_briefs = []
    for idx, scene in enumerate(scenes, start=1):
        scene_briefs.append({
            "scene_index": idx,
            "planned_action": scene.action_taken,
            "suspect_focus": scene.suspect_focus,
            "clue_found": scene.clue_found,
            "testimony_gained": scene.testimony_gained,
            "timeline_fact_verified": scene.timeline_fact_verified,
            "outcome": scene.outcome,
            "theory_progress": scene.theory_progress,
        })

    system = """
    You are the world generator for an interactive murder mystery text game.

    You will receive the entire investigation timeline at once. Your job is to synthesize
    the minimum useful set of concrete physical rooms and assign each scene to one room.

    HARD RULES:
    1. Return valid WorldLocationPlan.
    2. Every room name must be a concrete physical place, not an action label.
    3. Forbidden room names include: Interrogation Room, Interview Room, Confrontation Room,
       Reveal Room, Accusation Room, Questioning Room, Evidence Beat Room.
    4. Room names must be clearly different from each other. Do not create near-duplicates
       such as Office/Victim's Office, Lab/Forensics Lab, Hall/Hallway.
    5. If a planned action investigates a specific physical place, create/use that place as
       a room and assign that scene there.
    6. Assign every investigation scene exactly once using its 1-based scene_index.
    7. Include Crime Scene as the starting room.
    8. Include Police Station as the final accusation room.
    9. The murder weapon must be placed in weapon_room as hidden evidence, but do not reveal
       the weapon name in any room name or room description.
    10. connected_rooms should form a simple navigable map. Crime Scene should connect to
        nearby evidence locations, and Police Station should connect to official locations.
    """
    user = f"""
    HIDDEN CASE TRUTH, for consistency only. Do not reveal hidden truth in descriptions:
    {gt.model_dump_json(indent=2)}

    INVESTIGATION SCENES TO PLACE:
    {json.dumps(scene_briefs, indent=2)}

    Build a global room plan and scene-to-room assignment.
    """
    plan = generate_structured_response(system, user, WorldLocationPlan, model="gpt-4o-mini")

    if plan is None:
        # Deterministic fallback still uses the full scene list, then de-duplicates globally.
        assignments = []
        room_names = ["Crime Scene", "Police Station"]
        for idx, scene in enumerate(scenes, start=1):
            room_name = sanitize_room_name(fallback_room_for_scene(scene, gt))
            if room_name not in room_names:
                # Avoid too many generic one-off rooms by relying on sanitize/fallback.
                room_names.append(room_name)
            assignments.append(SceneRoomAssignment(
                scene_index=idx,
                room_name=room_name,
                reason="Deterministic fallback based on scene action and clue text."
            ))
        rooms = [SynthesizedRoom(
            name=name,
            description=PHYSICAL_ROOM_DESCRIPTIONS.get(
                name,
                f"A distinct physical location connected to the investigation: {name}."
            ),
            connected_rooms=[]
        ) for name in room_names]
        return WorldLocationPlan(rooms=rooms, assignments=assignments, weapon_room="Crime Scene")

    # Clean and validate the LLM output so the rest of the engine can trust it.
    used_names = set()
    cleaned_rooms: List[SynthesizedRoom] = []
    for room in plan.rooms:
        name = sanitize_room_name(room.name)
        if name in used_names:
            continue
        if any(bad in name.lower() for bad in BANNED_ROOM_WORDS):
            name = "Police Station"
        used_names.add(name)
        cleaned_rooms.append(SynthesizedRoom(
            name=name,
            description=room.description or PHYSICAL_ROOM_DESCRIPTIONS.get(name, f"A distinct physical location connected to the investigation: {name}."),
            connected_rooms=[sanitize_room_name(r) for r in room.connected_rooms if sanitize_room_name(r) != name]
        ))

    # Guarantee required anchor rooms.
    required = ["Crime Scene", "Police Station"]
    for required_room in required:
        if required_room not in used_names:
            cleaned_rooms.append(SynthesizedRoom(
                name=required_room,
                description=PHYSICAL_ROOM_DESCRIPTIONS.get(required_room, f"A required location: {required_room}."),
                connected_rooms=[]
            ))
            used_names.add(required_room)

    cleaned_assignments: List[SceneRoomAssignment] = []
    assigned_indices = set()
    known_rooms = {room.name for room in cleaned_rooms}
    for assignment in plan.assignments:
        idx = assignment.scene_index
        if idx < 1 or idx > len(scenes) or idx in assigned_indices:
            continue
        room_name = sanitize_room_name(assignment.room_name)
        if room_name not in known_rooms:
            cleaned_rooms.append(SynthesizedRoom(
                name=room_name,
                description=PHYSICAL_ROOM_DESCRIPTIONS.get(room_name, f"A distinct physical location connected to the investigation: {room_name}."),
                connected_rooms=[]
            ))
            known_rooms.add(room_name)
        cleaned_assignments.append(SceneRoomAssignment(
            scene_index=idx,
            room_name=room_name,
            reason=assignment.reason
        ))
        assigned_indices.add(idx)

    # Fill any missing scene assignment with the deterministic fallback.
    for idx, scene in enumerate(scenes, start=1):
        if idx not in assigned_indices:
            room_name = sanitize_room_name(fallback_room_for_scene(scene, gt))
            if room_name not in known_rooms:
                cleaned_rooms.append(SynthesizedRoom(
                    name=room_name,
                    description=PHYSICAL_ROOM_DESCRIPTIONS.get(room_name, f"A distinct physical location connected to the investigation: {room_name}."),
                    connected_rooms=[]
                ))
                known_rooms.add(room_name)
            cleaned_assignments.append(SceneRoomAssignment(
                scene_index=idx,
                room_name=room_name,
                reason="Fallback assignment because the global plan skipped this scene."
            ))

    weapon_room = sanitize_room_name(plan.weapon_room)
    if weapon_room not in known_rooms:
        weapon_room = "Crime Scene"

    cleaned_assignments.sort(key=lambda a: a.scene_index)
    return WorldLocationPlan(rooms=cleaned_rooms, assignments=cleaned_assignments, weapon_room=weapon_room)




class CauseOfDeathResult(BaseModel):
    cause_of_death: str = Field(description="A spoiler-safe medical cause category derived from the hidden weapon/method.")

def derive_cause_of_death_from_weapon(weapon: str) -> str:
    """Return a spoiler-safe medical cause category from the hidden weapon/method using an LLM.

    This lets the detective discover cause of death before the exact murder weapon.
    """
    weapon_str = weapon if weapon else "unknown"
    system = """
    You are a medical examiner. Given a murder weapon or method, return a spoiler-safe medical cause of death category.
    Examples of cause of death: 
    - poisoning
    - gunshot trauma
    - sharp-force trauma
    - asphyxiation from neck compression
    - blunt-force trauma
    - fatal smoke or burn injury
    If unclear, return 'injuries consistent with a deliberate homicide'.
    """
    user = f"Weapon/Method: {weapon_str}"
    
    res = generate_structured_response(system, user, CauseOfDeathResult, model="gpt-4o-mini")
    if res and res.cause_of_death:
        return res.cause_of_death.strip()
    return "injuries consistent with a deliberate homicide"


def adapt_phase1_scenes_to_interactive_timeline(gt: HiddenStoryDB, generated_scenes: List[SceneOutcome]) -> Tuple[List[SceneOutcome], Dict[int, SceneDiscoveryMarker]]:
    """Use an LLM to adapt Phase I plot points into 14 playable pre-accusation beats.

    This does not create hardcoded discovery scenes. The Phase I generator remains the
    source of the story. The LLM sees all Phase I scenes, removes repeats, makes the
    timeline causal, and marks where cause of death and murder weapon are discovered.
    """
    phase1_briefs = []
    for idx, scene in enumerate(generated_scenes, start=1):
        phase1_briefs.append({
            "phase1_index": idx,
            "plot_point_number": scene.plot_point_number,
            "action_taken": scene.action_taken,
            "suspect_focus": scene.suspect_focus,
            "clue_found": scene.clue_found,
            "testimony_gained": scene.testimony_gained,
            "alibi_status": scene.alibi_status,
            "means_tested": scene.means_tested,
            "motive_tested": scene.motive_tested,
            "opportunity_tested": scene.opportunity_tested,
            "weapon_relevance": scene.weapon_relevance,
            "motive_relevance": scene.motive_relevance,
            "timeline_fact_verified": scene.timeline_fact_verified,
            "red_herring_used": scene.red_herring_used,
            "red_herring_resolved": scene.red_herring_resolved,
            "interference_exposed": scene.interference_exposed,
            "outcome": scene.outcome,
            "theory_progress": scene.theory_progress,
            "weapon_confirmed": scene.weapon_confirmed,
            "motive_confirmed": scene.motive_confirmed,
        })

    system = """
    You are the Event Timeline Adaptation module for an interactive murder mystery.

    Keep the Phase I story generator as the source of the plot. Do not invent generic
    hardcoded scenes. Use the generated plot points below as the basis for the playable
    timeline.

    Return a valid TimelineAdaptationResult.

    HARD RULES:
    1. Return exactly 14 pre-accusation scenes. Event 15 is the final accusation and is
       added elsewhere.
    2. Use the Phase I generated scenes as the content source. You may lightly rewrite,
       merge, split, or clarify them only to make them interactive and causally ordered.
    3. Do not repeat the same plot beat. If two scenes accomplish the same clue, testimony,
       suspect check, or evidence discovery, merge or remove the repetition.
    4. The detective finding the cause of death must be one of the 14 scenes. Do not add
       a canned scene. Choose or lightly rewrite the most relevant Phase I scene so the
       discovery naturally happens there.
    5. The detective finding or identifying the murder weapon must be one of the 14 scenes.
       Do not add a canned scene. Choose or lightly rewrite the most relevant Phase I scene
       so the discovery naturally happens there.
    6. Cause of death and murder weapon discovery can happen early, middle, or late, wherever
       the Phase I sequence makes them natural.
    7. Later scenes must not require knowledge that earlier scenes did not reveal. If a scene
       depends on a clue, statement, location, or suspect, an earlier scene must reveal or
       motivate it.
    8. Keep the hidden truth consistent. Do not change the killer, true motive, weapon, or crime timeline.
    9. In discovery_markers, mark exactly one scene as reveals_cause_of_death and exactly one
       scene as reveals_murder_weapon. If one natural scene reveals both, mark both true for
       that single scene.
    """
    user = f"""
    HIDDEN CASE TRUTH, for consistency only. Do not reveal it too early in player narration:
    {gt.model_dump_json(indent=2)}

    PHASE I GENERATED INVESTIGATION SCENES:
    {json.dumps(phase1_briefs, indent=2)}

    Adapt these generated plot points into the Phase II event timeline.
    """
    result = generate_structured_response(system, user, TimelineAdaptationResult, model="gpt-4o-mini")

    if result is None or not result.scenes:
        repair_system = system + """
        The previous attempt failed. Return the same model, but base it directly on the
        available Phase I scenes and rewrite only enough to include the two required
        discoveries and remove repeats.
        """
        result = generate_structured_response(repair_system, user, TimelineAdaptationResult, model="gpt-4o-mini")

    if result and result.scenes:
        scenes = [scene.model_copy(deep=True) for scene in result.scenes[:FINAL_INTERACTIVE_EVENT_COUNT - 1]]
        markers = {m.scene_index: m for m in result.discovery_markers if 1 <= m.scene_index <= FINAL_INTERACTIVE_EVENT_COUNT - 1}
    else:
        scenes = [scene.model_copy(deep=True) for scene in generated_scenes[:FINAL_INTERACTIVE_EVENT_COUNT - 1]]
        markers = {}

    if len(scenes) < FINAL_INTERACTIVE_EVENT_COUNT - 1 and generated_scenes:
        repair_user = f"""
        The adapted timeline below has only {len(scenes)} scenes. Expand it to exactly 14 by
        using unresolved Phase I material without repeating the same plot beat.

        HIDDEN CASE TRUTH:
        {gt.model_dump_json(indent=2)}

        CURRENT ADAPTED SCENES:
        {json.dumps([s.model_dump() for s in scenes], indent=2)}

        ORIGINAL PHASE I SCENES:
        {json.dumps(phase1_briefs, indent=2)}
        """
        repaired = generate_structured_response(system, repair_user, TimelineAdaptationResult, model="gpt-4o-mini")
        if repaired and len(repaired.scenes) >= FINAL_INTERACTIVE_EVENT_COUNT - 1:
            scenes = [s.model_copy(deep=True) for s in repaired.scenes[:FINAL_INTERACTIVE_EVENT_COUNT - 1]]
            markers = {m.scene_index: m for m in repaired.discovery_markers if 1 <= m.scene_index <= FINAL_INTERACTIVE_EVENT_COUNT - 1}

    # Structural normalization only: ids must be unique and sequential.
    scenes = scenes[:FINAL_INTERACTIVE_EVENT_COUNT - 1]
    for idx, scene in enumerate(scenes, start=1):
        scene.plot_point_number = idx

    return scenes, markers


def scene_discovery_marker_for(idx: int, markers: Dict[int, SceneDiscoveryMarker]) -> SceneDiscoveryMarker:
    return markers.get(idx, SceneDiscoveryMarker(
        scene_index=idx,
        reveals_cause_of_death=False,
        reveals_murder_weapon=False,
        reason="No required discovery marker for this scene."
    ))


def apply_world_location_plan(world: WorldState, plan: WorldLocationPlan):
    """Add globally synthesized rooms and connections to the live world."""
    # Start from the stable base map, then add/override the synthesized room details.
    for room in plan.rooms:
        name = sanitize_room_name(room.name)
        if name not in world.rooms:
            world.rooms[name] = Room(name=name, description=room.description)
        else:
            world.rooms[name].description = room.description or world.rooms[name].description

    # Add connections suggested by the global room planner.
    for room in plan.rooms:
        room_name = sanitize_room_name(room.name)
        if room_name not in world.rooms:
            continue
        for connected in room.connected_rooms:
            connected_name = sanitize_room_name(connected)
            if connected_name == room_name:
                continue
            ensure_room_exists(world, connected_name)
            if connected_name not in world.rooms[room_name].exits.values():
                world.rooms[room_name].exits[f"to {connected_name}"] = connected_name
            if room_name not in world.rooms[connected_name].exits.values():
                world.rooms[connected_name].exits[f"to {room_name}"] = room_name

    # Make any unconnected generated room reachable from Crime Scene so the player is never trapped.
    for room_name in list(world.rooms.keys()):
        if room_name == "Crime Scene":
            continue
        has_exit_to_room = any(room_name in room.exits.values() for room in world.rooms.values())
        if not has_exit_to_room:
            world.rooms["Crime Scene"].exits[f"to {room_name}"] = room_name
            world.rooms[room_name].exits.setdefault("back to Crime Scene", "Crime Scene")

def connect_rooms(world: WorldState):
    """Build a dynamic map for the text game instead of hardcoding exits."""
    world.rooms["Crime Scene"] = Room(name="Crime Scene", description="The primary scene where responders have taped off the area and physical evidence still needs to be interpreted.", exits={"to Police Station": "Police Station"})
    world.rooms["Police Station"] = Room(name="Police Station", description="A working station with desks, phones, tired officers, and private corners where witnesses can be questioned.", exits={"to Crime Scene": "Crime Scene"})



def place_character(world: WorldState, character: str, room_name: str, narrate_move: bool = False) -> Optional[str]:
    """Move one character to one room, removing them from any previous room first."""
    room_name = sanitize_room_name(room_name)
    if room_name not in world.rooms:
        room_name = "Crime Scene"
    previous = world.character_locations.get(character)
    if previous and previous in world.rooms and character in world.rooms[previous].characters:
        world.rooms[previous].characters.remove(character)
    if character not in world.rooms[room_name].characters:
        world.rooms[room_name].characters.append(character)
    world.character_locations[character] = room_name
    if narrate_move and previous and previous != room_name:
        if previous == world.player_location:
            move_note = f"{character} leaves the room, heading toward {room_name}."
        elif room_name == world.player_location:
            move_note = f"{character} enters from {previous}."
        else:
            move_note = f"{character} moves from {previous} to {room_name}."
        world.game_log.append(move_note)
        return move_note
    return None


def assign_murder_weapon_to_room(gt: HiddenStoryDB, world: WorldState, preferred_room: str = "Crime Scene") -> str:
    """Place the murder weapon as a physical hidden object in exactly one room.

    The weapon exists in the world for consistency, but it is not listed as a visible
    object at the start. The player should discover the cause of death and weapon
    through investigation, not through the opening narration.
    """
    weapon = gt.weapon.strip() if gt.weapon else "murder weapon"
    room_name = preferred_room if preferred_room in world.rooms else "Crime Scene"
    for room in world.rooms.values():
        room.objects = [obj for obj in room.objects if obj.lower() != weapon.lower()]
        room.hidden_objects = [obj for obj in room.hidden_objects if obj.lower() != weapon.lower()]
    if weapon not in world.rooms[room_name].hidden_objects:
        world.rooms[room_name].hidden_objects.append(weapon)
    world.murder_weapon_location = room_name
    return room_name


def sync_room_characters_from_locations(world: WorldState):
    """Rebuild room character lists from character_locations to prevent duplicate NPC placement."""
    existing_known = set(world.character_locations.keys())
    for room_name, room in world.rooms.items():
        room.characters = [c for c in room.characters if c not in existing_known]
    for character, room_name in world.character_locations.items():
        if room_name in world.rooms and character not in world.rooms[room_name].characters:
            world.rooms[room_name].characters.append(character)


def maybe_move_suspect_for_current_event(world: WorldState, events: List[InteractiveEvent]) -> Optional[str]:
    """Let NPCs move when the next event requires them elsewhere, without duplicating them."""
    world.last_visible_npc_movement_note = None
    if world.event_index >= len(events):
        return None
    event = events[world.event_index]
    for condition in event.preconditions:
        if " is available" in condition:
            character = condition.split(" is available", 1)[0]
            if character in world.character_locations and world.character_locations[character] != event.location:
                previous = world.character_locations.get(character)
                note = place_character(world, character, event.location, narrate_move=True)
                # Only surface NPC movement when the detective can actually notice it.
                if previous == world.player_location or event.location == world.player_location:
                    world.last_visible_npc_movement_note = note
                    return note
                return None
    return None


def room_entry_context(world: WorldState, events: List[InteractiveEvent]) -> Dict[str, object]:
    """Get visible details for narration whenever the detective enters or stands in a room."""
    room = world.rooms[world.player_location]
    first_visit = world.player_location not in world.visited_rooms
    if first_visit:
        world.visited_rooms.append(world.player_location)
    destinations = []
    for dest in room.exits.values():
        if dest not in destinations:
            destinations.append(dest)
    return {
        "room_name": room.name,
        "first_visit": first_visit,
        "room_description": room.description,
        "visible_objects": room.objects,
        "visible_characters": room.characters,
        "nearby_rooms": destinations,
        "movement_note": world.last_visible_npc_movement_note,
    }


def format_entry_fallback(context: Dict[str, object]) -> str:
    """Fallback room-entry narration if the LLM narrator is unavailable."""
    name = context["room_name"]
    objects = context.get("visible_objects") or []
    people = context.get("visible_characters") or []
    nearby = context.get("nearby_rooms") or []
    lines = []
    if context.get("first_visit"):
        lines.append(f"You step into {name}. {context.get('room_description', '')}")
        if objects:
            lines.append(f"You notice {', '.join(objects)} in the room.")
    else:
        lines.append(f"You are back in {name}. The room feels a little more familiar now.")
    if people:
        lines.append(f"Present here: {', '.join(people)}.")
    else:
        lines.append("No one else is immediately visible here.")
    if nearby:
        lines.append(f"From here, you can go to {', '.join(nearby)}.")
    return "\n\n".join(lines)

def build_interactive_plan(gt: HiddenStoryDB, state: StateTracker) -> Tuple[WorldState, List[InteractiveEvent]]:
    """Build a 15-event, playable, causally consistent event plan from Phase I scenes."""
    world = WorldState()
    events: List[InteractiveEvent] = []
    connect_rooms(world)

    world.player_location = "Crime Scene"
    world.facts.append(f"Victim: {gt.victim}")
    world.facts.append("The detective has just arrived; no clues, interviews, or conclusions have happened yet.")

    # Only immediately visible people start at the crime scene. Suspects exist in the world,
    # but their statements are not known until the player questions them.
    place_character(world, "Uniformed Officer", "Crime Scene")
    place_character(world, "Forensic Technician", "Crime Scene")
    for suspect in gt.suspects:
        place_character(world, suspect.name, "Police Station")

    # Build the 14 pre-accusation beats globally. Cause-of-death discovery and
    # murder-weapon discovery are guaranteed plot points, but they are placed
    # wherever they naturally fit instead of being hardcoded as Event 1/Event 2.
    scenes, discovery_markers = adapt_phase1_scenes_to_interactive_timeline(gt, state.completed_scenes)

    # IMPORTANT: synthesize all rooms in one global pass instead of naming one room
    # at a time. This lets the LLM avoid duplicate/similar room names and assign
    # each scene to the physical place that best matches the planned action.
    location_plan = synthesize_world_locations(gt, scenes)
    apply_world_location_plan(world, location_plan)
    scene_to_room = {a.scene_index: sanitize_room_name(a.room_name) for a in location_plan.assignments}

    # The murder weapon is a hidden physical object in the world, but the detective
    # does not know what it is or where it is yet. The global location plan decides
    # which room contains it, without revealing the weapon in opening narration.
    assign_murder_weapon_to_room(gt, world, preferred_room=location_plan.weapon_room)

    previous_unlock_fact = None
    for idx, scene in enumerate(scenes, start=1):
        room_name = scene_to_room.get(idx) or sanitize_room_name(fallback_room_for_scene(scene, gt))
        marker = scene_discovery_marker_for(idx, discovery_markers)
        # If the globally adapted timeline marks this as the weapon discovery, put
        # the event in the same room as the hidden physical weapon. This uses the
        # LLM marker rather than keyword checks or hardcoded scene positions.
        if marker.reveals_murder_weapon and world.murder_weapon_location:
            room_name = world.murder_weapon_location
        ensure_room_exists(world, room_name)

        # Do not place every focused suspect during world generation. Suspects start in one
        # physical place, then move only when the live event logic needs them elsewhere.

        # Preconditions are deliberately player-actionable: location access, character availability,
        # object intactness, and the previous lead being discovered through earlier play.
        preconditions = [f"Detective is at {room_name}"]
        if previous_unlock_fact:
            preconditions.append(previous_unlock_fact)
        if scene.suspect_focus:
            preconditions.append(f"{scene.suspect_focus} is available to the detective")
        if scene.clue_found:
            preconditions.append(f"Potential evidence connected to this event has not been destroyed")

        effects = []
        if scene.clue_found:
            effects.append(f"Detective learns clue: {scene.clue_found}")
        if marker.reveals_cause_of_death:
            effects.append("Cause of death has been discovered")
        if marker.reveals_murder_weapon:
            effects.append("Murder weapon has been found")
        if scene.testimony_gained and scene.suspect_focus:
            effects.append(f"Detective gains testimony from {scene.suspect_focus}: {scene.testimony_gained}")
        if scene.timeline_fact_verified:
            effects.append(f"Timeline verified: {scene.timeline_fact_verified}")
        if scene.red_herring_used:
            effects.append(f"Red herring introduced: {scene.red_herring_used}")
        if scene.red_herring_resolved:
            effects.append(f"Red herring resolved: {scene.red_herring_resolved}")
        if scene.interference_exposed:
            effects.append(f"Interference exposed: {scene.interference_exposed}")

        # Add an explicit lead that makes the next event logically unlocked by a previous event.
        unlock_fact = f"Lead unlocked for event {idx + 1}"
        if idx == FINAL_INTERACTIVE_EVENT_COUNT - 1:
            unlock_fact = "Ready to accuse murderer"
        effects.append(unlock_fact)

        causal_links = [f"location_accessible:{room_name}"]
        if scene.clue_found:
            causal_links.append(f"clue_available:{scene.clue_found}")
        if scene.suspect_focus:
            causal_links.append(f"character_available:{scene.suspect_focus}")
        if previous_unlock_fact:
            causal_links.append(f"known_fact:{previous_unlock_fact}")

        if marker.reveals_cause_of_death and marker.reveals_murder_weapon:
            event_title = "Identify Cause and Weapon"
        elif marker.reveals_cause_of_death:
            event_title = "Determine Cause of Death"
        elif marker.reveals_murder_weapon:
            event_title = "Find Murder Weapon"
        else:
            event_title = f"Evidence Beat {idx}"

        events.append(InteractiveEvent(
            event_id=idx,
            title=event_title,
            location=room_name,
            planned_action=scene.action_taken,
            preconditions=preconditions,
            effects=effects,
            causal_links=causal_links,
            clue_gate=previous_unlock_fact,
        ))
        previous_unlock_fact = unlock_fact

    # Final playable beat: the detective must choose who the murderer is.
    # The full truth is revealed only after a successful accusation.
    accusation_preconditions = ["Detective is at Police Station", "Cause of death has been discovered", "Murder weapon has been found"]
    if previous_unlock_fact:
        accusation_preconditions.append(previous_unlock_fact)
    events.append(InteractiveEvent(
        event_id=FINAL_INTERACTIVE_EVENT_COUNT,
        title="Final Accusation",
        location="Police Station",
        planned_action="Accuse the person the detective believes committed the murder",
        preconditions=accusation_preconditions,
        effects=["Case completed after correct accusation"],
        causal_links=["known_fact:Ready to accuse murderer", "location_accessible:Police Station"],
        clue_gate=previous_unlock_fact,
    ))

    events = normalize_event_ids(events)
    # Put the first required NPC in place if the opening beat needs them, without
    # duplicating every suspect across all future locations. Later NPC movement is narrated.
    if events:
        for condition in events[0].preconditions:
            if " is available" in condition:
                first_character = condition.split(" is available", 1)[0]
                place_character(world, first_character, events[0].location, narrate_move=False)
                break
    sync_room_characters_from_locations(world)
    return world, events


def describe_current_location(world: WorldState, events: List[InteractiveEvent]) -> str:
    """
    Present the player's current situation as live narration instead of a dashboard.
    The room data still exists for the game engine, but the player sees a story-like scene.
    """
    room = world.rooms[world.player_location]
    next_event = events[world.event_index] if world.event_index < len(events) else None

    sensory_bits = []
    if room.objects:
        sensory_bits.append(f"Your eye catches {', '.join(room.objects[:3])}.")
    if room.characters:
        sensory_bits.append(f"Nearby, {', '.join(room.characters[:3])} waits under the weight of the case.")
    if room.exits:
        exit_names = list(room.exits.values())[:3]
        sensory_bits.append(f"From here, the investigation could pull you toward {', '.join(exit_names)}.")

    pressure = ""
    if next_event and next_event.location != world.player_location:
        pressure = f" The next solid lead seems connected to {next_event.location}, but you decide how to approach it."
    elif next_event:
        pressure = " The next lead is within reach here, depending on what you choose to examine or who you decide to question."

    body = " ".join([room.description] + sensory_bits) + pressure
    return f"### {room.name}\n\n{body}\n\n*What do you do as the detective? Type any natural action.*"


def nearby_areas_text(world: WorldState) -> str:
    """Return a natural-language list of nearby explorable areas."""
    room = world.rooms[world.player_location]
    destinations = []
    for _, dest in room.exits.items():
        if dest not in destinations:
            destinations.append(dest)
    if not destinations:
        return "There are no obvious routes out from here yet."
    if len(destinations) == 1:
        return f"Nearby, you can move toward {destinations[0]}."
    return f"Nearby, you can move toward {', '.join(destinations[:-1])}, or {destinations[-1]}."


def room_options_text(world: WorldState) -> str:
    """Return clearly labeled room choices from the current room."""
    room = world.rooms[world.player_location]
    destinations = []
    for dest in room.exits.values():
        if dest not in destinations:
            destinations.append(dest)
    if not destinations:
        return "No nearby rooms are clearly reachable from here."
    return "Available nearby rooms: " + ", ".join(destinations) + "."


def generate_opening_narration(gt: HiddenStoryDB, world: WorldState, events: List[InteractiveEvent], state: StateTracker) -> str:
    """Create the first live-fiction paragraph the player sees after generation."""
    context = room_entry_context(world, events)
    nearby = nearby_areas_text(world)
    room_options = room_options_text(world)
    system = """
    You are the narrator of an interactive detective text game.
    Write the opening scene in second person, as if the player is the detective arriving for the first time.

    Hard continuity rules:
    - The detective has JUST arrived at the scene.
    - Do NOT say the detective has already interviewed anyone, searched anything, collected evidence, followed leads, or investigated earlier.
    - Do NOT reference future events, future clues, hidden motives, the killer, or the generated event timeline.
    - Only describe what is visible right now at the current location.
    - Make it clear the player can decide what to do next.

    Content requirements:
    - Introduce the overall situation: there has been a murder, who the victim is, why the detective was called, and what immediate uncertainty surrounds the scene.
    - Describe how the crime scene looks and feels.
    - Mention people physically present in the room and make clear they have not been questioned yet.
    - Mention visible objects in the room, but do NOT identify or name the murder weapon.
    - You may describe visual clues from the corpse, such as posture, marks, lividity, spilled items, or disturbance, but do NOT state the cause of death.
    - Mention nearby explorable areas naturally.
    - Also include one clear sentence listing the exact room names the player can move to next.
    - 3 to 5 short paragraphs.
    - Keep the tone like contemporary detective fiction.
    """
    user = f"""
    Victim name, allowed to reveal: {gt.victim}
    Current location: {world.player_location}
    First visit to this room: {context['first_visit']}
    Current room description: {context['room_description']}
    People physically present here: {context['visible_characters']}
    Visible objects here: {context['visible_objects']}
    Nearby explorable areas: {nearby}
    Exact room options to include clearly: {room_options}
    Hidden weapon/location for world consistency only, NEVER mention in opening: weapon is hidden in {world.murder_weapon_location}
    Persistent pressure, do not over-explain: {state.persistent_suspense.core_beat if state.persistent_suspense else 'None'}
    """
    text = generate_text_response(system, user, model="gpt-4o-mini")
    if text:
        return text
    people = ", ".join(context["visible_characters"]) if context["visible_characters"] else "a few uneasy responders"
    objects = ", ".join(context["visible_objects"]) if context["visible_objects"] else "scattered evidence markers"
    return (
        f"You arrive at {world.player_location} after the call about {gt.victim}. The scene is still fresh: tape at the edge of the room, quiet movement from responders, and the strange stillness that settles before facts become evidence.\n\n"
        f"{people} are here, watching you for direction but waiting to be questioned. You can see {objects}, but nothing has been interpreted yet. {nearby} {room_options}\n\n"
        "Nothing has been solved yet. You are the detective, and the first move is yours."
    )

def narrate_player_turn(
    command: str,
    action: ActionInterpretation,
    evaluation: ActionEvaluation,
    world: WorldState,
    events: List[InteractiveEvent],
    gt: HiddenStoryDB,
    state: StateTracker,
    event_resolution: str = "",
    accommodation_text: str = ""
) -> str:
    """
    Convert the game engine's classification/result into player-facing narration.
    This keeps the classification internally available but avoids showing a mechanical report.
    """
    room = world.rooms[world.player_location]
    nearby = nearby_areas_text(world)
    room_options = room_options_text(world)
    entered_room = action.action_type == "move" and evaluation.classification != "exceptional"
    entry_context = room_entry_context(world, events) if entered_room else {
        "room_name": room.name,
        "first_visit": False,
        "room_description": "",
        "visible_objects": room.objects,
        "visible_characters": room.characters,
        "nearby_rooms": list(dict.fromkeys(room.exits.values())),
        "movement_note": world.last_visible_npc_movement_note,
    }
    system = """
    You are the live narrator for an interactive murder mystery text game.
    The player is the detective. Turn the engine result into natural second-person narration.

    Hard continuity rules:
    - Only narrate consequences of the player's CURRENT command plus facts already in Current known facts.
    - Do NOT say the detective has interviewed, searched, found, learned, or accused anyone unless the current command or Event resolution says it happened.
    - Do NOT reference upcoming events, future clues, hidden motives, or the killer unless the case has just been completed.
    - Do NOT make it sound like a scene was already investigated before the player acted.
    - If the player moved rooms, describe arriving in the new location, who is there, and what rooms can be reached from there.
    - Only describe what is going on in the room, who is in the room, and nearby room options when Entered new room is true.
    - On the first visit to a room, describe the room itself and the visible objects inside it. On later visits, keep the room recap brief.
    - If Entered new room is false, do NOT repeat the room description or list all people/exits; focus mainly on the effect of the detective's current action.
    - If NPC movement note says someone leaves or enters while visible to the detective, clearly narrate it.
    - Do NOT say a character enters the room just because they are listed as currently visible; only say they enter if NPC movement note explicitly says they enter.
    - If a character is already present, describe them as present/waiting/standing there, not entering.
    - If the action did not advance the plot, keep the response grounded in the current action and ask for the next move naturally.

    Style rules:
    - Write 1 to 3 short paragraphs.
    - Do NOT show labels like classification, reason, world state, exits, objects, or event plan.
    - Acknowledge exactly what the player tried to do.
    - If the action advanced the plot, make the clue/testimony feel discovered through that action.
    - If the action was exceptional, narrate either the intervention or accommodation in-world.
    - Do not start with a markdown location header; the interface will show the location before your narration.
    - End with a soft cue that the detective can choose the next action.
    """
    user = f"""
    Player command: {command}
    Parsed action: {action.model_dump_json(indent=2)}
    Engine classification: {evaluation.classification}
    Engine response, for narrator only: {evaluation.response_text}
    Event resolution, use only if it happened now: {event_resolution}
    Drama manager text, use only if it happened now: {accommodation_text}

    Current location after the action: {world.player_location}
    Room entry context: {json.dumps(entry_context, indent=2)}
    Current room description: {room.description}
    People currently visible in this room: {room.characters}
    Visible objects in this room: {room.objects}
    Nearby explorable areas: {nearby}
    Exact room options, use only if Entered new room is true: {room_options}
    Entered new room: {entered_room}
    NPC movement note, mention clearly if visible/relevant: {entry_context.get('movement_note')}
    Current known facts already discovered by the player: {world.facts[-8:]}
    Inventory: {world.inventory}
    Case completed: {world.solved}
    Hidden truth constraints, do not reveal directly unless the game has completed: killer={gt.killer}, motive={gt.true_motive}, weapon={gt.weapon}
    """
    text = generate_text_response(system, user, model="gpt-4o-mini")
    if text:
        return text

    # Fallback if the narrator call fails.
    if evaluation.classification == "exceptional":
        return accommodation_text or "Your move lands harder than expected, bending the investigation off its clean path. The case is not lost, but the truth will have to be reached another way."
    if event_resolution:
        return event_resolution
    if action.action_type == "move":
        return format_entry_fallback(entry_context)
    if entry_context.get("movement_note"):
        return f"{evaluation.response_text}\n\n{entry_context['movement_note']}"
    return evaluation.response_text

def interpret_player_action(command: str, world: WorldState, events: List[InteractiveEvent], gt: HiddenStoryDB) -> ActionInterpretation:
    command = command.strip()[:300]

    # Direct room-name navigation is handled by the world graph. This recognizes
    # actual reachable destinations, while all semantic action classification is
    # delegated to the LLM.
    lower = command.lower()
    room = world.rooms[world.player_location]
    for exit_name, dest in room.exits.items():
        if lower in [exit_name.lower(), f"go {exit_name.lower()}", f"move {exit_name.lower()}"] or dest.lower() in lower:
            return ActionInterpretation(
                intent=f"move to {dest}", action_type="move", location_target=dest,
                likely_effects=[f"player_location={dest}"]
            )

    system = """
    You are the Action Interpreter for an open-ended detective text game.

    Convert the player's natural-language command into structured intent. Use context,
    not keyword rules. Decide whether the player is trying to move, inspect, interview,
    take evidence, destroy or alter something, lock/block access, accuse someone, wait,
    or do something else.

    Be especially alert for actions that could destroy clues, make suspects unavailable,
    lock rooms, shortcut the mystery, accuse someone, or otherwise threaten the planned
    timeline.
    """
    next_event = events[world.event_index].model_dump() if world.event_index < len(events) else None
    user = f"""
    Player command: {command}
    Current location: {world.player_location}
    Current room: {world.rooms[world.player_location].model_dump_json(indent=2)}
    Reachable rooms from here: {list(room.exits.values())}
    Inventory: {world.inventory}
    Known facts: {world.facts[-10:]}
    Next planned event: {json.dumps(next_event, indent=2)}
    Suspects: {[s.name for s in gt.suspects]}

    Interpret the command as ActionInterpretation.
    """
    parsed = generate_structured_response(system, user, ActionInterpretation, model="gpt-4o-mini")
    if parsed:
        return parsed

    # Last-resort technical fallback avoids semantic keyword decisions.
    return ActionInterpretation(intent=command, action_type="other", target=command)


def action_matches_event(action: ActionInterpretation, event: InteractiveEvent) -> bool:
    """Use an LLM to decide whether the player action satisfies the current event.

    This replaces the older word-overlap matcher. The decision is made from the
    interpreted action, event preconditions/effects, and planned action rather than
    hardcoded keyword overlap.
    """
    system = """
    You are checking whether a detective player's action completes the current planned
    story event in an interactive mystery.

    Return ActionEventMatch. Do not require exact wording. A match means the action would
    reasonably accomplish the planned action or directly produce the event's intended
    investigative effect. A non-match means the action may still be consistent with the
    world, but it does not complete this plot point.
    """
    user = f"""
    Interpreted player action:
    {action.model_dump_json(indent=2)}

    Current planned event:
    {event.model_dump_json(indent=2)}

    Does the player action satisfy this event?
    """
    match = generate_structured_response(system, user, ActionEventMatch, model="gpt-4o-mini")
    if match is None:
        return False
    return match.matches_current_event


def event_preconditions_met(world: WorldState, event: InteractiveEvent) -> Tuple[bool, str]:
    """Check only conditions the detective can directly affect through play."""
    if world.player_location != event.location:
        return False, f"The next lead is at {event.location}."
    for condition in event.preconditions:
        if condition.startswith("Lead unlocked") and condition not in world.facts:
            return False, "You have not uncovered the previous lead yet."
        if "has not been destroyed" in condition:
            for destroyed in world.damaged_or_destroyed:
                if destroyed.lower() in condition.lower() or condition.lower() in destroyed.lower():
                    return False, "A needed piece of evidence has been damaged or destroyed."
        if condition == "Cause of death has been discovered" and not world.cause_of_death_found:
            return False, "You still need to determine the cause of death before making the final accusation."
        if condition == "Murder weapon has been found" and not world.murder_weapon_found:
            return False, "You still need to find the murder weapon before making the final accusation."
        if "is available" in condition:
            name = condition.split(" is available", 1)[0]
            if name in world.unavailable_characters:
                return False, f"{name} is not available right now."
    return True, "Preconditions satisfied."


def threatens_active_causal_link(action: ActionInterpretation, world: WorldState, events: List[InteractiveEvent]) -> Optional[str]:
    """Use an LLM to identify whether an action threatens active causal links.

    This replaces keyword/word-overlap threat detection. The LLM receives the future
    event plan, current world state, and interpreted action, then decides whether the
    action would negate a precondition, causal link, evidence path, character availability,
    or overall mystery solvability.
    """
    remaining = events[world.event_index:]
    system = """
    You are a causal-link monitor for an interactive detective story.

    Decide whether the player's action threatens the remaining event timeline. A threat
    can be explicit, such as destroying an object named in a causal link, or commonsense,
    such as making a witness unavailable, blocking a room, shortcutting the solution,
    or making future investigation impossible.

    Return CausalThreatAssessment.
    """
    user = f"""
    Interpreted player action:
    {action.model_dump_json(indent=2)}

    Current location: {world.player_location}
    Current room:
    {world.rooms[world.player_location].model_dump_json(indent=2)}

    World facts: {world.facts[-10:]}
    Inventory: {world.inventory}
    Damaged/destroyed: {world.damaged_or_destroyed}
    Locked locations: {world.locked_locations}
    Unavailable characters: {world.unavailable_characters}

    Remaining planned events:
    {json.dumps([event.model_dump() for event in remaining], indent=2)}

    Does this action threaten an active causal link or mystery solvability?
    """
    assessment = generate_structured_response(system, user, CausalThreatAssessment, model="gpt-4o-mini")
    if assessment and assessment.threatens_timeline:
        return assessment.threatened_link or assessment.reason or "llm_detected_timeline_threat"
    return None


def evaluate_player_action(action: ActionInterpretation, command: str, world: WorldState, events: List[InteractiveEvent], gt: HiddenStoryDB) -> ActionEvaluation:
    next_event = events[world.event_index] if world.event_index < len(events) else None

    # Final event: the player must explicitly accuse a suspect. Do not auto-complete
    # the case from a generic investigative action.
    if next_event and next_event.event_id == FINAL_INTERACTIVE_EVENT_COUNT:
        met, why_not = event_preconditions_met(world, next_event)
        if not met and action.action_type != "move":
            return ActionEvaluation(
                classification="consistent",
                reason=why_not,
                response_text=why_not,
            )
        if action.action_type == "accuse":
            named = action.suspect_target or action.target or ""
            if gt.killer.lower() in named.lower():
                return ActionEvaluation(
                    classification="constituent",
                    reason="The player made the correct final accusation.",
                    response_text=f"You accuse {gt.killer}.",
                    should_advance_event=True,
                )
            return ActionEvaluation(
                classification="consistent",
                reason="The accusation is not supported by the completed evidence chain.",
                response_text="The accusation does not hold. The evidence you have gathered points somewhere else, and the case remains open.",
            )
        if action.action_type != "move":
            return ActionEvaluation(
                classification="consistent",
                reason="The investigation is ready for a final accusation, but the player has not accused anyone yet.",
                response_text="The case is ready for you to name the murderer. Accuse the suspect you believe committed the crime.",
            )

    # Movement changes the location and can be used by the player to satisfy the next event's location precondition.
    if action.action_type == "move" and action.location_target:
        if action.location_target in world.locked_locations:
            return ActionEvaluation(
                classification="consistent",
                reason="The player tried to move, but the location is currently locked.",
                response_text=f"You try to go to {action.location_target}, but it is locked for now.",
            )
        return ActionEvaluation(
            classification="consistent",
            reason="Movement directly updates player_location, which may satisfy a future event precondition.",
            world_updates=[f"player_location={action.location_target}"],
            response_text=f"You move to {action.location_target}.",
        )

    threat = threatens_active_causal_link(action, world, events)
    if threat:
        tool = choose_drama_manager_tool(action, command, threat, world, events)
        return ActionEvaluation(
            classification="exceptional",
            reason=f"The action threatens an active causal link: {threat}. Drama Manager selected {tool}.",
            response_text="That action would seriously disrupt the investigation timeline.",
            accommodation_needed=(tool == "accommodation"),
            intervention_needed=(tool == "intervention"),
        )

    if next_event:
        met, why_not = event_preconditions_met(world, next_event)
        if met and action_matches_event(action, next_event):
            return ActionEvaluation(
                classification="constituent",
                reason="The action matches the next planned event and all actionable preconditions are met.",
                response_text="You push the investigation forward in the intended direction.",
                should_advance_event=True,
            )

        # Important fix: if the player performs a reasonable investigative action in the correct location,
        # advance the beat even if the LLM phrased the planned_action differently.
        if met and action.action_type in ["inspect", "interview", "take", "other"]:
            return ActionEvaluation(
                classification="constituent",
                reason="The player is in the correct physical location and performed an action capable of satisfying the event.",
                response_text="Your action directly engages the current lead.",
                should_advance_event=True,
            )

        if not met:
            return ActionEvaluation(
                classification="consistent",
                reason=why_not,
                response_text=why_not,
            )

    return ActionEvaluation(
        classification="consistent",
        reason="The action fits the world but does not complete the next planned event.",
        world_updates=action.likely_effects,
        response_text="You do that. It fits the scene, but it does not move the core mystery forward yet.",
    )


def apply_world_updates(world: WorldState, evaluation: ActionEvaluation, action: ActionInterpretation):
    for update in evaluation.world_updates:
        if update.startswith("player_location="):
            dest = update.split("=", 1)[1]
            if dest in world.rooms:
                world.player_location = dest

    target = action.target or action.suspect_target or action.location_target
    if action.action_type == "take" and target:
        room = world.rooms[world.player_location]
        for obj in list(room.objects):
            if obj.lower() in target.lower() or target.lower() in obj.lower():
                room.objects.remove(obj)
                if obj not in world.inventory:
                    world.inventory.append(obj)
                world.game_log.append(f"Took {obj}.")
                break
    elif action.action_type == "destroy" and target:
        world.damaged_or_destroyed.append(target)
    elif action.action_type == "lock" and action.location_target:
        world.locked_locations.append(action.location_target)
    sync_room_characters_from_locations(world)


def advance_constituent_event(world: WorldState, events: List[InteractiveEvent], state: StateTracker) -> str:
    if world.event_index >= len(events):
        world.solved = True
        return "The case has reached its conclusion."

    event = events[world.event_index]
    event.completed = True
    for effect in event.effects:
        if effect not in world.facts:
            world.facts.append(effect)
        if effect == "Cause of death has been discovered" or "Cause of death discovered" in effect:
            world.cause_of_death_found = True
        if effect == "Murder weapon has been found" or "Murder weapon found" in effect:
            world.murder_weapon_found = True
    world.event_index += 1

    # Also reveal the matching Phase I scene if available.
    matching = next((s for s in state.completed_scenes if s.plot_point_number == event.event_id), None)
    if matching:
        return f"**Story event completed:** {matching.outcome}\n\n**Why it matters:** {matching.theory_progress}"
    return "The planned event resolves and the investigation moves forward."


def choose_drama_manager_tool(action: ActionInterpretation, command: str, threat: str, world: WorldState, events: List[InteractiveEvent]) -> str:
    """Use an LLM to select accommodation vs intervention for an exceptional action.

    Accommodation means the action is allowed to change the world and later events are
    repaired. Intervention means the action receives a realistic failure/redirect and
    the current timeline is preserved.
    """
    remaining_events = [event.model_dump() for event in events[world.event_index:]]
    system = """
    You are the Drama Manager for an interactive mystery using Intervention and Accommodation.

    Choose exactly one tool: accommodation or intervention.

    Accommodation should be chosen when the player's exceptional action is concrete,
    physically plausible, and can be allowed to change the world while repairing future
    event preconditions or causal links.

    Intervention should be chosen when allowing the action would shortcut the mystery,
    make the case unsolvable, violate story plausibility, require broad impossible power,
    or destroy too much of the core investigation. Intervention preserves the timeline by
    narrating a realistic failure mode or redirection.
    """
    user = f"""
    Player command: {command}
    Interpreted action:
    {action.model_dump_json(indent=2)}

    Threatened link or issue: {threat}
    Current location: {world.player_location}
    Current room:
    {world.rooms[world.player_location].model_dump_json(indent=2)}

    Known facts: {world.facts[-10:]}
    Damaged/destroyed items: {world.damaged_or_destroyed}
    Locked locations: {world.locked_locations}
    Remaining planned events:
    {json.dumps(remaining_events, indent=2)}

    Select the Drama Manager tool.
    """
    decision = generate_structured_response(system, user, DramaToolDecision, model="gpt-4o-mini")
    if decision and decision.tool.lower().strip() in ["accommodation", "intervention"]:
        return decision.tool.lower().strip()

    # Conservative technical fallback: preserve solvability if the LLM call fails.
    return "intervention"


def apply_exception_world_change(world: WorldState, action: ActionInterpretation) -> List[str]:
    """Apply only the player's concrete exceptional action for accommodation.
    This is deliberately not used for intervention.
    """
    changes = []
    target = action.target or action.suspect_target or action.location_target
    room = world.rooms.get(world.player_location)

    if action.action_type == "destroy" and target:
        if target not in world.damaged_or_destroyed:
            world.damaged_or_destroyed.append(target)
        changes.append(f"Player damaged or destroyed: {target}")
        if room:
            for obj in list(room.objects):
                if obj.lower() in target.lower() or target.lower() in obj.lower():
                    room.objects.remove(obj)
                    changes.append(f"Removed visible object from {room.name}: {obj}")
                    break

    elif action.action_type == "lock" and action.location_target:
        if action.location_target not in world.locked_locations:
            world.locked_locations.append(action.location_target)
        changes.append(f"Player locked or blocked location: {action.location_target}")

    elif action.action_type == "take" and target and room:
        for obj in list(room.objects):
            if obj.lower() in target.lower() or target.lower() in obj.lower():
                room.objects.remove(obj)
                if obj not in world.inventory:
                    world.inventory.append(obj)
                changes.append(f"Player took: {obj}")
                break

    if changes:
        world.game_log.extend(changes)
    sync_room_characters_from_locations(world)
    return changes


def intervene_exception(action: ActionInterpretation, command: str, world: WorldState, events: List[InteractiveEvent], gt: HiddenStoryDB, state: StateTracker, reason: str) -> InterventionResult:
    system = """
    You are the Intervention tool for a Drama Manager in an interactive detective story.

    The player attempted an exceptional action that should NOT be allowed to change the core world state.
    Create a believable in-world failure, delay, redirection, or social/legal constraint.

    Rules:
    1. Preserve the current event timeline exactly.
    2. Do not repair or rewrite future events.
    3. Do not reveal the killer, motive, weapon, or hidden crime timeline.
    4. Acknowledge what the player tried.
    5. Explain why it fails or is blocked in a way that feels natural for a detective story.
    6. The detective should still be able to continue investigating normally afterward.
    Return an InterventionResult.
    """
    next_event = events[world.event_index].model_dump() if world.event_index < len(events) else None
    user = f"""
    Player command: {command}
    Parsed action: {action.model_dump_json(indent=2)}
    Reason intervention was selected: {reason}
    Current location: {world.player_location}
    Current room: {world.rooms[world.player_location].model_dump_json(indent=2)}
    Next planned event, for timeline preservation only: {json.dumps(next_event, indent=2)}
    Known facts: {world.facts[-8:]}
    Hidden ground truth, do not reveal: killer={gt.killer}, motive={gt.true_motive}, weapon={gt.weapon}
    """
    result = generate_structured_response(system, user, InterventionResult, model="gpt-4o-mini")
    if result:
        return result
    return InterventionResult(
        response_text="You try to force the investigation off its rails, but the situation pushes back in a believable way. Procedure, locked access, and the limits of what you can prove stop the attempt from changing the case. The timeline remains intact, and the next lead is still waiting.",
        prevented_world_updates=[f"Prevented exceptional action: {command}"],
        timeline_preserved=True,
    )


def accommodate_exception(action: ActionInterpretation, command: str, world: WorldState, events: List[InteractiveEvent], gt: HiddenStoryDB, state: StateTracker) -> AccommodationResult:
    system = """
    You are the Accommodation tool for a Drama Manager in an interactive detective story.
    The player attempted an exceptional action that has already been allowed to change the world.

    Your job:
    1. Acknowledge the player's action and its concrete world-state consequence.
    2. Repair only the future events made impossible by that change.
    3. Keep repaired events close to the original plan, using minor substitutions like a backup clue, another witness, another access route, or a different room.
    4. Do not use intervention language such as saying the action failed; accommodation means the action happened.
    5. Do not reveal the killer unless the planned story has already reached the final reveal.
    6. Preserve the hidden ground truth: killer, motive, weapon, and core timeline cannot change.
    """
    remaining = [e.model_dump() for e in events[world.event_index:world.event_index + 5]]
    user = f"""
    Hidden ground truth constraints:
    {gt.model_dump_json(indent=2)}

    Player command: {command}
    Parsed action: {action.model_dump_json(indent=2)}
    Current world: {world.model_dump_json(indent=2)}
    Remaining planned events near current point:
    {json.dumps(remaining, indent=2)}
    Current investigation state:
    {compact_state_summary(gt, state)}

    Return an accommodation/intervention result. If repairing events, keep them close to the original plan.
    """
    result = generate_structured_response(system, user, AccommodationResult, model="gpt-4o-mini")
    if result:
        return result

    return AccommodationResult(
        response_text="You try it, but the story pushes back in a believable way: the attempt creates noise, not closure. The detective realizes the case can still be solved, but the route to the next clue has shifted.",
        world_updates=["Exception acknowledged; no core mystery facts changed."],
        repaired_events=[],
        mystery_still_solvable=True,
    )


def apply_accommodation(world: WorldState, events: List[InteractiveEvent], accommodation: AccommodationResult):
    for update in accommodation.world_updates:
        if update not in world.facts:
            world.facts.append(update)

    if accommodation.repaired_events:
        # Replace only the upcoming window; preserve already completed events.
        completed = events[:world.event_index]
        repaired = accommodation.repaired_events
        rest_start = world.event_index + len(repaired)
        rest = events[rest_start:] if rest_start < len(events) else []
        events[:] = completed + repaired + rest


def generate_full_crime_reveal(gt: HiddenStoryDB, state: StateTracker, world: WorldState) -> str:
    """Reveal the complete hidden crime story only after the player solves the case."""
    system = """
    You are the closing narrator for an interactive detective mystery.
    The player has completed the case with the correct accusation.

    Write the full crime reveal clearly and dramatically.
    Include:
    - that the case has been completed
    - the killer
    - the motive
    - the murder weapon / method
    - the step-by-step crime timeline
    - why the other suspects were not the murderer
    - how the discovered clues fit together

    Keep it concise but complete. Do not hide the truth anymore.
    """
    user = f"""
    Hidden ground truth:
    {gt.model_dump_json(indent=2)}

    Investigation facts discovered by the player:
    {json.dumps(world.facts, indent=2)}

    Phase I investigation record:
    {json.dumps([s.model_dump() for s in state.completed_scenes], indent=2)}
    """
    text = generate_text_response(system, user, model="gpt-4o-mini")
    if text:
        return text

    innocent = [s.name for s in gt.suspects if s.name != gt.killer]
    timeline = "\n".join(f"- {item}" for item in gt.timeline)
    return (
        f"### Case Completed\n\n"
        f"The murderer was **{gt.killer}**. The motive was **{gt.true_motive}**, and the weapon/method was **{gt.weapon}**.\n\n"
        f"The crime unfolded like this:\n{timeline}\n\n"
        f"The other suspects were ruled out through the evidence chain: {', '.join(innocent)}. "
        f"The killer's interference failed because the detective connected the physical evidence, testimony, and timeline into one consistent story."
    )


def generate_interactive_seed() -> Tuple[Optional[HiddenStoryDB], Optional[StateTracker], Optional[WorldState], List[InteractiveEvent]]:
    """Generate a Phase I story record, then convert it into a playable Phase II world."""
    gt, final_story, state = run_meta_controller(yield_updates=False)
    if not gt or not state:
        return None, None, None, []
    world, events = build_interactive_plan(gt, state)
    return gt, state, world, events


def reset_interactive_session():
    for key in ["phase2_gt", "phase2_state", "phase2_world", "phase2_events", "phase2_transcript", "phase2_ready", "phase2_command"]:
        st.session_state.pop(key, None)


def add_transcript_entry(role: str, text: str, location: Optional[str] = None):
    """Store the full playable history so the player can scroll back through the whole case."""
    if "phase2_transcript" not in st.session_state:
        st.session_state["phase2_transcript"] = []
    st.session_state["phase2_transcript"].append({
        "role": role,
        "text": text,
        "location": location,
    })


def render_story_history():
    """Render the complete narrator/player history in a scrollable container."""
    transcript = st.session_state.get("phase2_transcript", [])
    if not transcript:
        return

    st.markdown("### Case History")
    with st.container(height=560):
        for item in transcript:
            role = item.get("role", "system")
            text = item.get("text", "")
            location = item.get("location")

            if role == "player":
                st.markdown(f"**You:** {text}")
            else:
                if location:
                    st.markdown(f"**Location: {location}**")
                st.markdown(text)
            st.markdown("---")


def current_location_line(world: WorldState) -> str:
    """Small player-facing location marker without exposing room internals."""
    return f"**Current location: {world.player_location}**"


# ==========================================
# 11. Streamlit Frontend: Phase II Interactive Game
# ==========================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Blueberry Gorilla Interactive Mystery",
        layout="wide",
        page_icon="🕵️‍♂️"
    )

    st.title("Blueberry Gorilla Interactive Mystery")
    st.subheader("Phase II • Intervention and Accommodation Text Game")

    with st.sidebar:
        st.header("⚙️ Configuration")
        user_api_key = st.text_input("OpenAI API Key", type="password")
        if user_api_key:
            os.environ["OPENAI_API_KEY"] = user_api_key
            st.success("API Key loaded.")

        st.markdown("---")
        st.markdown("### Phase II Architecture")
        st.markdown("- **Phase I Generator:** creates hidden crime + plot points")
        st.markdown("- **World Generator:** converts scenes into rooms, objects, suspects, exits")
        st.markdown("- **Interactive Loop:** accepts open-ended player commands")
        st.markdown("- **Action Interpreter:** maps commands to structured actions")
        st.markdown("- **Drama Manager:** classifies actions as constituent, consistent, or exceptional")
        st.markdown("- **Accommodation:** allows a disruptive action, mutates world state, then repairs future events")
        st.markdown("- **Intervention:** blocks or soft-fails impossible/shortcut actions while preserving the timeline")

        if st.button("Reset Game"):
            reset_interactive_session()
            st.rerun()

    tab_game, tab_state, tab_plan, tab_hidden = st.tabs([
        "🎮 Play Interactive Mystery",
        "🌍 World State",
        "🧩 Event Plan",
        "🔒 Hidden Ground Truth"
    ])

    with tab_game:
        if "phase2_ready" not in st.session_state:
            st.write("Generate a Phase I mystery and convert it into a playable Phase II text game.")
            if st.button("Generate Interactive Mystery 🕵️"):
                with st.spinner("Generating hidden case, investigation timeline, world graph, and causal event plan..."):
                    gt, state, world, events = generate_interactive_seed()
                    if gt and state and world and events:
                        st.session_state["phase2_gt"] = gt
                        st.session_state["phase2_state"] = state
                        st.session_state["phase2_world"] = world
                        st.session_state["phase2_events"] = events
                        opening = generate_opening_narration(gt, world, events, state)
                        st.session_state["phase2_transcript"] = []
                        add_transcript_entry("system", opening, location=world.player_location)
                        st.session_state["phase2_ready"] = True
                        st.success("Interactive mystery generated.")
                        st.rerun()
                    else:
                        st.error("Generation failed. Check your API key and try again.")
        else:
            gt: HiddenStoryDB = st.session_state["phase2_gt"]
            state: StateTracker = st.session_state["phase2_state"]
            world: WorldState = st.session_state["phase2_world"]
            events: List[InteractiveEvent] = st.session_state["phase2_events"]

            st.markdown(current_location_line(world))
            render_story_history()

            command = st.text_input("What do you do next?", max_chars=300, key="phase2_command")
            if st.button("Submit Action") and command.strip():
                action = interpret_player_action(command, world, events, gt)
                evaluation = evaluate_player_action(action, command, world, events, gt)
                world.turns += 1
                world.last_classification = evaluation.classification

                add_transcript_entry("player", command, location=world.player_location)

                event_resolution = ""
                accommodation_text = ""

                if evaluation.classification == "exceptional":
                    if evaluation.intervention_needed and not evaluation.accommodation_needed:
                        intervention = intervene_exception(action, command, world, events, gt, state, evaluation.reason)
                        accommodation_text = intervention.response_text
                        world.game_log.extend(intervention.prevented_world_updates)
                    else:
                        direct_changes = apply_exception_world_change(world, action)
                        accommodation = accommodate_exception(action, command, world, events, gt, state)
                        if direct_changes:
                            accommodation.world_updates = direct_changes + accommodation.world_updates
                        apply_accommodation(world, events, accommodation)
                        accommodation_text = accommodation.response_text
                else:
                    apply_world_updates(world, evaluation, action)
                    if evaluation.should_advance_event:
                        if action.action_type == "accuse":
                            world.final_accusation = action.suspect_target or action.target
                        event_resolution = advance_constituent_event(world, events, state)
                    movement_note = maybe_move_suspect_for_current_event(world, events)
                    if movement_note:
                        event_resolution = (event_resolution + "\n\n" + movement_note).strip()

                response = narrate_player_turn(
                    command=command,
                    action=action,
                    evaluation=evaluation,
                    world=world,
                    events=events,
                    gt=gt,
                    state=state,
                    event_resolution=event_resolution,
                    accommodation_text=accommodation_text,
                )

                if world.event_index >= len(events):
                    world.solved = True
                    response += "\n\n### Case Complete\nThe final pieces lock into place. The mystery has reached its conclusion."

                st.session_state["phase2_world"] = world
                st.session_state["phase2_events"] = events
                add_transcript_entry("system", response, location=world.player_location)
                st.rerun()

    with tab_state:
        if "phase2_ready" in st.session_state:
            world: WorldState = st.session_state["phase2_world"]
            st.markdown("### Current World State")
            st.code(world.model_dump_json(indent=2), language="json")
        else:
            st.info("Generate an interactive mystery first.")

    with tab_plan:
        if "phase2_ready" in st.session_state:
            events: List[InteractiveEvent] = st.session_state["phase2_events"]
            world: WorldState = st.session_state["phase2_world"]
            st.markdown(f"### Event Timeline Progress: {world.event_index}/{len(events)}")
            st.code(json.dumps([e.model_dump() for e in events], indent=2), language="json")
        else:
            st.info("Generate an interactive mystery first.")

    with tab_hidden:
        if "phase2_ready" in st.session_state:
            gt: HiddenStoryDB = st.session_state["phase2_gt"]
            st.warning("Hidden information for debugging/demo only. Do not show this to a player during a real run.")
            st.code(gt.model_dump_json(indent=2), language="json")
        else:
            st.info("Generate an interactive mystery first.")
