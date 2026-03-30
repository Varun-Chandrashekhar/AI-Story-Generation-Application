# import os
# import json
# import streamlit as st
# from pydantic import BaseModel, Field
# from typing import List, Dict, Optional, Tuple
# from openai import OpenAI

# # ==========================================
# # 1. Schemas & Data Structures
# # ==========================================

# class Suspect(BaseModel):
#     name: str = Field(description="Name of the suspect.")
#     means: str = Field(description="How they could have committed the crime.")
#     motive: str = Field(description="Why they would want to commit the crime.")
#     opportunity: str = Field(description="Their alibi or presence at the scene.")
#     is_lying: bool = Field(default=False, description="Whether this suspect will lie in testimonies.")

# class HiddenStoryDB(BaseModel):
#     victim: str = Field(description="Name of the victim.")
#     killer: str = Field(description="Name of the actual killer.")
#     true_motive: str = Field(description="The real reason the killer committed the crime.")
#     weapon: str = Field(description="The weapon used to commit the murder.")
#     timeline: List[str] = Field(description="Timeline of the killer's actions before, during, and after the crime.")
#     suspects: List[Suspect] = Field(description="List of all plausible suspects including the killer and innocent parties.")
#     red_herrings: List[str] = Field(description="Irrelevant clues meant to confuse the detective.")
#     interference_plan: str = Field(description="How the killer is actively trying to hide their tracks or frame others.")

# class PersistentSuspenseBeat(BaseModel):
#     core_beat: str = Field(description="The one suspense idea that persists across the entire story.")
#     target: str = Field(description="The main person, object, or narrative thread under pressure.")
#     why_it_matters: str = Field(description="Why this beat makes solving the case fragile or urgent.")

# class ScenePromptInput(BaseModel):
#     action_hint: str = Field(description="The next investigative step.")
#     obstacle_hint: str = Field(description="The main obstacle in that step.")
#     target_suspect: Optional[str] = Field(default=None, description="Which suspect the scene primarily focuses on.")
#     coverage_goal: str = Field(description="What investigation need this scene should satisfy.")
#     suspense_use_in_scene: str = Field(description="How the persistent suspense beat should appear concretely in this scene.")

# class SceneOutcome(BaseModel):
#     plot_point_number: int = Field(description="Current plot step.")
#     action_taken: str = Field(description="What the detective did.")
#     suspect_focus: Optional[str] = Field(default=None, description="Primary suspect in the scene.")
#     clue_found: Optional[str] = Field(default=None, description="Concrete clue found in this scene.")
#     testimony_gained: Optional[str] = Field(default=None, description="Statement gained from suspect or witness.")
#     alibi_status: Optional[str] = Field(default=None, description="confirmed / contradicted / unclear")
#     means_tested: bool = Field(default=False, description="Whether the suspect's means were examined.")
#     motive_tested: bool = Field(default=False, description="Whether the suspect's motive was examined.")
#     opportunity_tested: bool = Field(default=False, description="Whether the suspect's opportunity was examined.")
#     suspect_cleared: bool = Field(default=False, description="Whether this suspect was ruled out in this scene.")
#     weapon_relevance: Optional[str] = Field(default=None, description="How this scene connects to the murder weapon.")
#     motive_relevance: Optional[str] = Field(default=None, description="How this scene connects to the true motive.")
#     timeline_fact_verified: Optional[str] = Field(default=None, description="Which timeline fact was verified.")
#     red_herring_used: Optional[str] = Field(default=None, description="A misleading clue introduced or revisited.")
#     red_herring_resolved: Optional[str] = Field(default=None, description="Which misleading clue was explained away.")
#     interference_exposed: Optional[str] = Field(default=None, description="How the killer's cover-up was exposed.")

#     suspense_manifestation: str = Field(
#         description="The concrete way the persistent suspense beat appears in this scene."
#     )
#     suspense_consequence: str = Field(
#         description="How that suspense event makes the next step riskier, harder, or more urgent."
#     )

#     outcome: str = Field(description="What happened in the scene.")
#     theory_progress: str = Field(description="How the case became more solvable after this scene.")
#     weapon_confirmed: bool = Field(default=False, description="Whether this scene confirms the murder weapon.")
#     motive_confirmed: bool = Field(default=False, description="Whether this scene confirms the true motive.")

# class StateTracker(BaseModel):
#     current_plot_count: int = Field(default=0)
#     known_clues: List[str] = Field(default_factory=list)
#     testimonies: Dict[str, str] = Field(default_factory=dict)

#     suspects_all: List[str] = Field(default_factory=list)
#     suspects_introduced: List[str] = Field(default_factory=list)
#     suspects_interviewed: List[str] = Field(default_factory=list)
#     suspects_cleared: List[str] = Field(default_factory=list)
#     suspects_with_means_checked: List[str] = Field(default_factory=list)
#     suspects_with_motive_checked: List[str] = Field(default_factory=list)
#     suspects_with_opportunity_checked: List[str] = Field(default_factory=list)

#     verified_timeline_events: List[str] = Field(default_factory=list)
#     red_herrings_introduced: List[str] = Field(default_factory=list)
#     red_herrings_resolved: List[str] = Field(default_factory=list)
#     interference_exposed_points: List[str] = Field(default_factory=list)

#     confirmed_weapon: bool = Field(default=False)
#     confirmed_motive: bool = Field(default=False)
#     final_theory_ready: bool = Field(default=False)

#     remaining_time: int = Field(default=24)
#     completed_scenes: List[SceneOutcome] = Field(default_factory=list)

#     persistent_suspense: Optional[PersistentSuspenseBeat] = Field(default=None)
#     suspense_history: List[str] = Field(default_factory=list)
#     suspense_consequences: List[str] = Field(default_factory=list)

# # ==========================================
# # 2. LLM Utilities
# # ==========================================

# def get_openai_client():
#     api_key = os.environ.get("OPENAI_API_KEY")
#     if not api_key:
#         try:
#             if "OPENAI_API_KEY" in st.secrets:
#                 api_key = st.secrets["OPENAI_API_KEY"]
#         except Exception:
#             pass
#     if not api_key:
#         st.error("Missing OPENAI_API_KEY. Please set it in environment variables or Streamlit secrets.")
#         st.stop()
#     return OpenAI(api_key=api_key)

# def generate_structured_response(
#     system_prompt: str,
#     user_prompt: str,
#     response_model: type[BaseModel],
#     model: str = "gpt-4o-mini"
# ):
#     client = get_openai_client()
#     try:
#         completion = client.beta.chat.completions.parse(
#             model=model,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ],
#             response_format=response_model,
#         )
#         return completion.choices[0].message.parsed
#     except Exception as e:
#         print(f"Error calling LLM: {e}")
#         return None

# def generate_text_response(system_prompt: str, user_prompt: str, model: str = "gpt-4o"):
#     client = get_openai_client()
#     try:
#         completion = client.chat.completions.create(
#             model=model,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ]
#         )
#         return completion.choices[0].message.content
#     except Exception as e:
#         print(f"Error calling LLM: {e}")
#         return None

# # ==========================================
# # 3. Crime Creator
# # ==========================================

# def run_crime_creator() -> HiddenStoryDB:
#     system = """
#     You are the master designer of a logically consistent murder mystery.

#     Generate a Hidden Story DB with:
#     - one victim
#     - one actual killer
#     - a clear true motive
#     - a specific weapon or method
#     - a detailed timeline
#     - 4 plausible suspects total, including the killer
#     - at least 2 red herrings
#     - a realistic interference plan by the killer

#     Rules:
#     - all suspects must be plausible
#     - innocent suspects must have believable means, motive, and opportunity but still be ultimately exonerable
#     - the timeline must support later investigation
#     - the solution must be solvable
#     - the interference plan should create recurring opportunities for suspense
#     """
#     user = "Generate the complete hidden truth of the murder mystery."
#     return generate_structured_response(system, user, HiddenStoryDB)

# # ==========================================
# # 4. Suspense + Coverage Helpers
# # ==========================================

# def choose_persistent_suspense_beat(gt: HiddenStoryDB) -> PersistentSuspenseBeat:
#     system = """
#     You are choosing ONE persistent suspense beat for a murder mystery.

#     Pick exactly one suspense beat that can recur throughout the whole investigation.

#     Good suspense beat examples:
#     - case closure deadline
#     - detective is being threatened
#     - a key piece of evidence is being quietly erased or altered

#     Rules:
#     1. Choose only one core suspense beat.
#     2. It must naturally fit the killer's interference plan and hidden story.
#     3. It must be concrete enough to reappear in multiple scenes.
#     4. It must stay relevant until the final reveal.
#     5. Do not create multiple options.
#     6. Keep it usable across many scenes.
#     """

#     user = f"""
#     HIDDEN STORY DB:
#     {gt.model_dump_json(indent=2)}

#     Choose the single best persistent suspense beat.
#     """

#     beat = generate_structured_response(system, user, PersistentSuspenseBeat)
#     if beat is None:
#         return PersistentSuspenseBeat(
#             core_beat="The killer is trying to keep the truth unstable long enough for the detective to lose control of the story.",
#             target="the investigation's version of what happened",
#             why_it_matters="If the detective cannot stabilize evidence and testimony quickly, the false version of the case may become the accepted one."
#         )
#     return beat

# def initialize_state_from_ground_truth(gt: HiddenStoryDB) -> StateTracker:
#     suspense = choose_persistent_suspense_beat(gt)
#     return StateTracker(
#         suspects_all=[s.name for s in gt.suspects],
#         persistent_suspense=suspense
#     )

# def case_ready_for_final_reveal(gt: HiddenStoryDB, state: StateTracker) -> bool:
#     nonkiller_count = len([s for s in gt.suspects if s.name != gt.killer])
#     return (
#         all(name in state.suspects_introduced for name in state.suspects_all)
#         and all(name in state.suspects_interviewed for name in state.suspects_all)
#         and len(state.suspects_cleared) >= nonkiller_count
#         and state.confirmed_weapon
#         and state.confirmed_motive
#         and len(state.verified_timeline_events) >= min(4, len(gt.timeline))
#         and len(state.red_herrings_resolved) >= len(gt.red_herrings)
#     )

# def compact_state_summary(gt: HiddenStoryDB, state: StateTracker) -> str:
#     persistent_suspense_json = (
#         state.persistent_suspense.model_dump()
#         if state.persistent_suspense is not None
#         else None
#     )

#     return json.dumps(
#         {
#             "current_plot_count": state.current_plot_count,
#             "suspects_all": state.suspects_all,
#             "suspects_introduced": state.suspects_introduced,
#             "suspects_interviewed": state.suspects_interviewed,
#             "suspects_cleared": state.suspects_cleared,
#             "means_checked": state.suspects_with_means_checked,
#             "motive_checked": state.suspects_with_motive_checked,
#             "opportunity_checked": state.suspects_with_opportunity_checked,
#             "known_clues": state.known_clues[-8:],
#             "verified_timeline_events": state.verified_timeline_events,
#             "red_herrings_introduced": state.red_herrings_introduced,
#             "red_herrings_resolved": state.red_herrings_resolved,
#             "interference_exposed_points": state.interference_exposed_points,
#             "confirmed_weapon": state.confirmed_weapon,
#             "confirmed_motive": state.confirmed_motive,
#             "remaining_time": state.remaining_time,
#             "persistent_suspense": persistent_suspense_json,
#             "recent_suspense_history": state.suspense_history[-6:],
#             "recent_suspense_consequences": state.suspense_consequences[-6:],
#             "final_theory_ready": state.final_theory_ready,
#         },
#         indent=2
#     )

# def recent_scene_summary(state: StateTracker, max_scenes: int = 3) -> str:
#     if not state.completed_scenes:
#         return "No prior scenes."
#     trimmed = [s.model_dump() for s in state.completed_scenes[-max_scenes:]]
#     return json.dumps(trimmed, indent=2)

# # ==========================================
# # 5. Planner / Meta-Controller
# # ==========================================

# def get_scene_action_obstacle(gt: HiddenStoryDB, state: StateTracker) -> ScenePromptInput:
#     system = """
#     You are the investigation planner for a murder mystery.

#     Your job is to choose the next best scene so that:
#     1. the hidden story is fully investigated
#     2. the same persistent suspense beat continues across the whole story

#     COVERAGE RULES:
#     1. Every suspect must appear in at least one meaningful scene.
#     2. Every suspect must be interviewed or examined.
#     3. Every suspect's means, motive, and opportunity must be tested.
#     4. Innocent suspects must be ruled out with evidence, not ignored.
#     5. The murder weapon must be verified before the final reveal.
#     6. The true motive must be verified before the final reveal.
#     7. The killer's timeline must be gradually verified.
#     8. Red herrings must be introduced and later resolved.
#     9. The killer's interference plan should actively complicate the investigation.
#     10. Do not repeat the same confrontation unless new evidence justifies it.

#     SUSPENSE RULES:
#     1. Use the SAME persistent suspense beat in every scene.
#     2. Do not invent a new main suspense concept.
#     3. The suspense must show up as a concrete event, not vague language.
#     4. The suspense event in this scene should make the next scene more fragile or urgent.
#     5. The suspense beat should evolve, not reset.
#     6. Avoid generic phrasing like 'tension rises' or 'pressure increases' unless tied to a real event.

#     Output:
#     - action_hint
#     - obstacle_hint
#     - target_suspect
#     - coverage_goal
#     - suspense_use_in_scene
#     """

#     persistent_suspense_json = (
#         state.persistent_suspense.model_dump_json(indent=2)
#         if state.persistent_suspense is not None
#         else "None"
#     )

#     user = f"""
#     HIDDEN STORY DB:
#     {gt.model_dump_json(indent=2)}

#     CURRENT STATE:
#     {compact_state_summary(gt, state)}

#     PERSISTENT SUSPENSE BEAT:
#     {persistent_suspense_json}

#     RECENT SCENES:
#     {recent_scene_summary(state)}

#     Choose the next scene.
#     """

#     scene = generate_structured_response(system, user, ScenePromptInput)
#     if scene is None:
#         return ScenePromptInput(
#             action_hint="The detective pursues the most unresolved suspect or clue.",
#             obstacle_hint="The killer's interference makes the next piece of truth unstable or difficult to secure.",
#             target_suspect=None,
#             coverage_goal="Advance the most urgent unresolved part of the case.",
#             suspense_use_in_scene="The persistent suspense beat appears as a concrete disruption that makes the next step harder to trust or verify."
#         )
#     return scene

# # ==========================================
# # 6. Investigation Generator
# # ==========================================

# def run_investigation_generator(
#     plot_num: int,
#     gt: HiddenStoryDB,
#     state: StateTracker,
#     scene_plan: ScenePromptInput,
#     is_final_scene: bool = False
# ) -> SceneOutcome:

#     if is_final_scene:
#         system = """
#         You are the simulation engine for a detective solving a murder.

#         This is the final reveal scene.

#         You must explicitly state:
#         1. who committed the murder
#         2. the exact motive
#         3. the exact weapon or method
#         4. the step-by-step timeline of the murder
#         5. why each other suspect is not the killer
#         6. how each red herring misled the investigation
#         7. how the killer interfered with the investigation
#         8. what evidence proves the conclusion

#         FINAL SCENE SUSPENSE RULES:
#         1. The same persistent suspense beat must appear one last time.
#         2. This final appearance should show that beat failing or collapsing under the truth.
#         3. Do not invent a new suspense idea in the final scene.
#         4. The suspense manifestation must still be concrete and observable.
#         5. The suspense consequence should make clear what almost went wrong before the detective stabilized the case.

#         Return valid SceneOutcome.
#         """
#     else:
#         system = """
#         You are the simulation engine for a detective solving a murder.

#         Generate the next scene using:
#         - the hidden ground truth
#         - the investigation state
#         - the planned next scene
#         - the persistent suspense beat

#         INVESTIGATION RULES:
#         1. Advance the investigation concretely.
#         2. Use specific evidence and suspect reasoning.
#         3. If the suspect is innocent, move toward ruling them out.
#         4. clue_found must be specific.
#         5. testimony_gained must be specific if present.
#         6. Do not contradict the hidden story.

#         SUSPENSE RULES:
#         1. The persistent suspense beat must appear in this scene as a concrete event.
#         2. Do not replace it with a different suspense idea.
#         3. Do not write vague phrases like 'tension rises' or 'pressure increases.'
#         4. The suspense manifestation must be observable and story-relevant.
#         5. The suspense consequence must create pressure that carries into the next scene.
#         6. The suspense should feel like the same recurring problem taking a new form.

#         Return valid SceneOutcome.
#         """

#     persistent_suspense_json = (
#         state.persistent_suspense.model_dump_json(indent=2)
#         if state.persistent_suspense is not None
#         else "None"
#     )

#     user = f"""
#     PLOT POINT NUMBER:
#     {plot_num}

#     HIDDEN STORY DB:
#     {gt.model_dump_json(indent=2)}

#     CURRENT STATE:
#     {compact_state_summary(gt, state)}

#     PERSISTENT SUSPENSE BEAT:
#     {persistent_suspense_json}

#     PLANNED SCENE:
#     {scene_plan.model_dump_json(indent=2)}

#     Generate the scene outcome.
#     """

#     out = generate_structured_response(system, user, SceneOutcome)
#     if out:
#         out.plot_point_number = plot_num
#     return out

# # ==========================================
# # 7. State Updates
# # ==========================================

# def update_state_from_scene(gt: HiddenStoryDB, state: StateTracker, outcome: SceneOutcome):
#     if outcome.clue_found and outcome.clue_found not in state.known_clues:
#         state.known_clues.append(outcome.clue_found)

#     if outcome.suspect_focus:
#         if outcome.suspect_focus not in state.suspects_introduced:
#             state.suspects_introduced.append(outcome.suspect_focus)
#         if outcome.suspect_focus not in state.suspects_interviewed:
#             state.suspects_interviewed.append(outcome.suspect_focus)

#     if outcome.testimony_gained and outcome.suspect_focus:
#         state.testimonies[outcome.suspect_focus] = outcome.testimony_gained

#     if outcome.suspect_focus and outcome.means_tested and outcome.suspect_focus not in state.suspects_with_means_checked:
#         state.suspects_with_means_checked.append(outcome.suspect_focus)

#     if outcome.suspect_focus and outcome.motive_tested and outcome.suspect_focus not in state.suspects_with_motive_checked:
#         state.suspects_with_motive_checked.append(outcome.suspect_focus)

#     if outcome.suspect_focus and outcome.opportunity_tested and outcome.suspect_focus not in state.suspects_with_opportunity_checked:
#         state.suspects_with_opportunity_checked.append(outcome.suspect_focus)

#     if outcome.suspect_focus and outcome.suspect_cleared and outcome.suspect_focus != gt.killer:
#         if outcome.suspect_focus not in state.suspects_cleared:
#             state.suspects_cleared.append(outcome.suspect_focus)

#     if outcome.weapon_confirmed or outcome.weapon_relevance:
#         state.confirmed_weapon = True

#     if outcome.motive_confirmed or outcome.motive_relevance:
#         state.confirmed_motive = True

#     if outcome.timeline_fact_verified and outcome.timeline_fact_verified not in state.verified_timeline_events:
#         state.verified_timeline_events.append(outcome.timeline_fact_verified)

#     if outcome.red_herring_used and outcome.red_herring_used not in state.red_herrings_introduced:
#         state.red_herrings_introduced.append(outcome.red_herring_used)

#     if outcome.red_herring_resolved and outcome.red_herring_resolved not in state.red_herrings_resolved:
#         state.red_herrings_resolved.append(outcome.red_herring_resolved)

#     if outcome.interference_exposed and outcome.interference_exposed not in state.interference_exposed_points:
#         state.interference_exposed_points.append(outcome.interference_exposed)

#     if outcome.suspense_manifestation:
#         state.suspense_history.append(outcome.suspense_manifestation)

#     if outcome.suspense_consequence:
#         state.suspense_consequences.append(outcome.suspense_consequence)

#     state.completed_scenes.append(outcome)
#     state.remaining_time -= 1
#     state.final_theory_ready = case_ready_for_final_reveal(gt, state)


# def run_narrator(gt: HiddenStoryDB, scenes: List[SceneOutcome], state: StateTracker) -> str:
#     system = """
#     You are a mystery novelist.

#     Transform the ordered investigation record into a cohesive, immersive detective story.

#     The story must preserve:
#     - the victim
#     - every suspect and their investigative role
#     - the true culprit
#     - the true motive
#     - the true weapon or method
#     - the real timeline of the crime
#     - the red herrings and how they were resolved
#     - the killer's interference with the investigation
#     - the persistent suspense beat

#     STYLE RULES:
#     1. Do NOT number scenes or label plot points.
#     2. Do NOT write like a summary or report.
#     3. Write as a continuous, flowing story with natural transitions.
#     4. Follow the chronological order of discoveries, but blend them smoothly.
#     5. Let clues emerge through action, dialogue, and observation.
#     6. Maintain the same persistent suspense beat throughout.
#     7. Avoid repetitive phrasing like “then they investigated.”
#     8. Write in the style of contemporary detective fiction: immersive, clear, and suspenseful.

#     CRITICAL ENDING REQUIREMENTS:
#     The final portion of the story MUST include a clear and explicit reconstruction of the crime.

#     This reconstruction must:
#     1. Clearly state WHY the killer committed the crime (motive).
#     2. Clearly explain HOW the crime was physically carried out (method and execution).
#     3. Walk through the timeline step-by-step in natural language.
#     4. Show how the evidence discovered supports each part of the reconstruction.
#     5. Explicitly explain why each other suspect is not the killer.
#     6. Show how the killer’s interference failed in the end.
#     7. Feel like a dramatic but precise explanation, not a vague summary.

#     The reader should finish the story with ZERO ambiguity about:
#     - what happened
#     - how it happened
#     - why it happened

#     The ending should feel like the truth finally locking into place after being unstable.

#     Do NOT rush the ending.
#     """

#     persistent_suspense_json = (
#         state.persistent_suspense.model_dump_json(indent=2)
#         if state.persistent_suspense else "None"
#     )

#     user = f"""
#     Adapt the following into a continuous mystery story.

#     HIDDEN STORY DB:
#     {gt.model_dump_json(indent=2)}

#     PERSISTENT SUSPENSE BEAT:
#     {persistent_suspense_json}

#     ORDERED SCENE OUTCOMES:
#     {json.dumps([s.model_dump() for s in scenes], indent=2)}

#     Important:
#     - Preserve the chronological order of discoveries.
#     - Include all suspects meaningfully.
#     - Ensure the ending fully reconstructs the crime in detail.
#     """

#     return generate_text_response(system, user)

# # ==========================================
# # 9. Meta-Controller Loop
# # ==========================================

# def run_meta_controller(yield_updates: bool = True) -> Tuple[Optional[HiddenStoryDB], Optional[str], Optional[StateTracker]]:
#     if yield_updates:
#         st.write("🕵️ **Step 1:** Initializing Crime Creator...")

#     ground_truth = run_crime_creator()
#     if not ground_truth:
#         return None, "Error generating crime.", None

#     if yield_updates:
#         st.success(f"Crime generated! The killer is secretly: {ground_truth.killer}")

#     state = initialize_state_from_ground_truth(ground_truth)

#     if yield_updates and state.persistent_suspense is not None:
#         st.write("**Persistent Suspense Beat Chosen:**")
#         st.write(f"**Core Beat:** {state.persistent_suspense.core_beat}")
#         st.write(f"**Target:** {state.persistent_suspense.target}")
#         st.write(f"**Why It Matters:** {state.persistent_suspense.why_it_matters}")

#     MIN_PLOT_POINTS = 15
#     MAX_PLOT_POINTS = 18

#     while True:
#         needs_more_coverage = not case_ready_for_final_reveal(ground_truth, state)
#         under_minimum = state.current_plot_count < MIN_PLOT_POINTS

#         if not needs_more_coverage and not under_minimum:
#             break

#         if state.current_plot_count >= MAX_PLOT_POINTS:
#             break

#         state.current_plot_count += 1

#         scene_plan = get_scene_action_obstacle(ground_truth, state)
#         if not scene_plan:
#             return None, "Error generating scene plan.", state

#         if yield_updates:
#             st.info(
#                 f"**Plot Point {state.current_plot_count}:** {scene_plan.action_hint}\n\n"
#                 f"**Coverage Goal:** {scene_plan.coverage_goal}\n\n"
#                 f"**Obstacle:** {scene_plan.obstacle_hint}\n\n"
#                 f"**Suspense Use In Scene:** {scene_plan.suspense_use_in_scene}"
#             )

#         outcome = run_investigation_generator(
#             state.current_plot_count,
#             ground_truth,
#             state,
#             scene_plan,
#             is_final_scene=False
#         )

#         if not outcome:
#             return None, "Error generating scene outcome.", state

#         update_state_from_scene(ground_truth, state, outcome)

#         if yield_updates:
#             with st.expander(f"Scene {state.current_plot_count} Outcome"):
#                 st.write(f"**Action:** {outcome.action_taken}")
#                 st.write(f"**Suspect Focus:** {outcome.suspect_focus}")
#                 st.write(f"**Clue Found:** {outcome.clue_found}")
#                 st.write(f"**Testimony:** {outcome.testimony_gained}")
#                 st.write(f"**Timeline Verified:** {outcome.timeline_fact_verified}")
#                 st.write(f"**Red Herring Resolved:** {outcome.red_herring_resolved}")
#                 st.write(f"**Interference Exposed:** {outcome.interference_exposed}")
#                 st.write(f"**Suspense Manifestation:** {outcome.suspense_manifestation}")
#                 st.write(f"**Suspense Consequence:** {outcome.suspense_consequence}")
#                 st.write(f"**Outcome:** {outcome.outcome}")
#                 st.write(f"**Theory Progress:** {outcome.theory_progress}")

#     if case_ready_for_final_reveal(ground_truth, state) and state.current_plot_count < MAX_PLOT_POINTS:
#         state.current_plot_count += 1

#         final_plan = ScenePromptInput(
#             action_hint="The detective gathers all suspects and delivers the final reconstruction of the crime.",
#             obstacle_hint="The killer makes one last attempt to keep the truth unstable before the case locks into an official version.",
#             target_suspect=ground_truth.killer,
#             coverage_goal="Deliver the final reveal using weapon, motive, timeline, suspect elimination, red herrings, and interference evidence.",
#             suspense_use_in_scene="The persistent suspense beat appears one last time as a concrete final attempt to preserve the false version of events, but it fails under the full weight of the evidence."
#         )

#         final_outcome = run_investigation_generator(
#             state.current_plot_count,
#             ground_truth,
#             state,
#             final_plan,
#             is_final_scene=True
#         )

#         if final_outcome:
#             update_state_from_scene(ground_truth, state, final_outcome)

#             if yield_updates:
#                 with st.expander(f"Final Reveal Scene {state.current_plot_count}"):
#                     st.write(f"**Suspense Manifestation:** {final_outcome.suspense_manifestation}")
#                     st.write(f"**Suspense Consequence:** {final_outcome.suspense_consequence}")
#                     st.write(f"**Outcome:** {final_outcome.outcome}")
#                     st.write(f"**Theory Progress:** {final_outcome.theory_progress}")

#     if yield_updates:
#         st.write("✍️ **Step 3:** Investigation complete! Passing structured investigation record to the Narrator...")

#     final_story = run_narrator(ground_truth, state.completed_scenes, state)
#     return ground_truth, final_story, state

# # ==========================================
# # 10. Streamlit Frontend
# # ==========================================

# if __name__ == "__main__":
#     st.set_page_config(
#         page_title="Suspense Generation - CS7634",
#         layout="wide",
#         page_icon="🕵️‍♂️"
#     )

#     st.title("Blueberry Gorilla Suspense Generator")
#     st.subheader("AI Storytelling Phase 1 • CS7634")

#     with st.sidebar:
#         st.header("⚙️ Configuration")
#         user_api_key = st.text_input("OpenAI API Key", type="password")
#         if user_api_key:
#             os.environ["OPENAI_API_KEY"] = user_api_key
#             st.success("API Key loaded into environment.")

#         st.markdown("---")
#         st.markdown("### Architecture")
#         st.markdown("- **Crime Creator:** fixed hidden truth")
#         st.markdown("- **Planner:** chooses scenes based on coverage + one persistent suspense beat")
#         st.markdown("- **State Tracker:** tracks suspects, clues, motive, weapon, timeline, red herrings")
#         st.markdown("- **Persistent Suspense Beat:** one recurring suspense thread used across the whole story")
#         st.markdown("- **Investigation Generator:** produces evidence-rich scenes with one concrete suspense manifestation per scene")
#         st.markdown("- **Narrator:** turns the investigation into a connected mystery instead of a dry case summary")

#     tab1, tab2, tab3 = st.tabs(["📝 Generate Novel", "🔍 View Hidden Story DB", "📈 Coverage & Suspense"])

#     with tab1:
#         st.write(
#             "Click below to generate a mystery. This version uses one persistent suspense beat that should stay relevant throughout the story instead of switching between multiple suspense systems."
#         )

#         if st.button("Generate Mystery Novel 📖"):
#             with st.spinner("Meta-Controller is directing the story components..."):
#                 ground_truth, final_story, final_state = run_meta_controller(yield_updates=True)

#                 if ground_truth and final_story and final_state:
#                     st.session_state["ground_truth"] = ground_truth.model_dump_json(indent=2)
#                     st.session_state["final_story"] = final_story
#                     st.session_state["final_state_summary"] = compact_state_summary(ground_truth, final_state)
#                     st.success("Generation Complete!")
#                     st.markdown("### The Final Novel")
#                     st.write(final_story)

#     with tab2:
#         if "ground_truth" in st.session_state:
#             st.write(
#                 "Behind the scenes, the Crime Creator generated these constraints. The planner and persistent suspense system then forced the investigation to keep returning to the same suspense thread."
#             )
#             st.code(st.session_state["ground_truth"], language="json")
#         else:
#             st.info("The Hidden Story DB will appear here after generation.")

#     with tab3:
#         if "final_state_summary" in st.session_state:
#             st.write("Final coverage and suspense state:")
#             st.code(st.session_state["final_state_summary"], language="json")
#         else:
#             st.info("Generate a story to view the final coverage and suspense state.")
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
# 10. Streamlit Frontend
# ==========================================
# User interface for running the full system.

if __name__ == "__main__":
    st.set_page_config(
        page_title="Suspense Generation - CS7634",
        layout="wide",
        page_icon="🕵️‍♂️"
    )

    st.title("Blueberry Gorilla Suspense Generator")
    st.subheader("AI Storytelling Phase 1 • CS7634")

    # Sidebar contains config + architecture summary
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Lets the user paste their API key directly into the app
        user_api_key = st.text_input("OpenAI API Key", type="password")
        if user_api_key:
            os.environ["OPENAI_API_KEY"] = user_api_key
            st.success("API Key loaded into environment.")

        st.markdown("---")
        st.markdown("### Architecture")
        st.markdown("- **Crime Creator:** fixed hidden truth")
        st.markdown("- **Planner:** chooses scenes based on coverage + one persistent suspense beat")
        st.markdown("- **State Tracker:** tracks suspects, clues, motive, weapon, timeline, red herrings")
        st.markdown("- **Persistent Suspense Beat:** one recurring suspense thread used across the whole story")
        st.markdown("- **Investigation Generator:** produces evidence-rich scenes with one concrete suspense manifestation per scene")
        st.markdown("- **Narrator:** turns the investigation into a connected mystery instead of a dry case summary")

    # Main app tabs
    tab1, tab2, tab3 = st.tabs(["📝 Generate Novel", "🔍 View Hidden Story DB", "📈 Coverage & Suspense"])

    # Tab 1: generate the story
    with tab1:
        st.write(
            "Click below to generate a mystery. This version uses one persistent suspense beat that should stay relevant throughout the story instead of switching between multiple suspense systems."
        )

        if st.button("Generate Mystery Novel 📖"):
            with st.spinner("Meta-Controller is directing the story components..."):
                ground_truth, final_story, final_state = run_meta_controller(yield_updates=True)

                if ground_truth and final_story and final_state:
                    # Save results in session state for the other tabs
                    st.session_state["ground_truth"] = ground_truth.model_dump_json(indent=2)
                    st.session_state["final_story"] = final_story
                    st.session_state["final_state_summary"] = compact_state_summary(ground_truth, final_state)

                    st.success("Generation Complete!")
                    st.markdown("### The Final Novel")
                    st.write(final_story)

    # Tab 2: show the hidden crime data
    with tab2:
        if "ground_truth" in st.session_state:
            st.write(
                "Behind the scenes, the Crime Creator generated these constraints. The planner and persistent suspense system then forced the investigation to keep returning to the same suspense thread."
            )
            st.code(st.session_state["ground_truth"], language="json")
        else:
            st.info("The Hidden Story DB will appear here after generation.")

    # Tab 3: show the final investigation state
    with tab3:
        if "final_state_summary" in st.session_state:
            st.write("Final coverage and suspense state:")
            st.code(st.session_state["final_state_summary"], language="json")
        else:
            st.info("Generate a story to view the final coverage and suspense state.")
