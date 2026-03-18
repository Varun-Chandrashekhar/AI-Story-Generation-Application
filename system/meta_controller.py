import streamlit as st
from system.schema import HiddenStoryDB, StateTracker, SceneOutcome
from system.modules import run_crime_creator, get_scene_action_obstacle, run_investigation_generator, run_narrator
from typing import Tuple

def run_meta_controller(yield_updates=True) -> Tuple[HiddenStoryDB, str]:
    """
    Module 4: Meta-Controller
    The director loop ensuring suspense and story logic.
    Architecture map: iterative control loop -> feed prompts to Investigation Generator -> check StateTracker.
    """
    
    if yield_updates:
        st.write("🕵️ **Step 1:** Initializing Crime Creator (generating the hidden murder)...")
        
    ground_truth = run_crime_creator()
    
    if not ground_truth:
        return None, "Error generating crime."
        
    if yield_updates:
        st.success(f"Crime generated! The killer is secretly: {ground_truth.killer}")
        st.write("⏱️ **Step 2:** Starting investigation loop...")
        
    # Initialize the ongoing investigation
    state = StateTracker()
    
    # We must hit at least 15 plot points before a conclusion is permitted
    MIN_PLOT_POINTS = 15
    while state.current_plot_count < MIN_PLOT_POINTS:
        state.current_plot_count += 1
        
        # 1. Action/Obstacle generation
        scene_input = get_scene_action_obstacle(state)
        action_hint = scene_input.action_hint if scene_input else "Detective uncovers a new trace."
        obstacle_hint = scene_input.obstacle_hint if scene_input else "Time is running out."
        
        if yield_updates:
            st.info(f"**Plot Point {state.current_plot_count}/{MIN_PLOT_POINTS}:** {action_hint} (Obstacle: {obstacle_hint})")
        
        # 2. Investigation Generator
        outcome = run_investigation_generator(state.current_plot_count, ground_truth, state, action_hint, obstacle_hint)
        
        # Add the completed scene to the history
        if outcome:
            state.completed_scenes.append(outcome)
            
            # Simple simulation tracking updates 
            if "clue" in outcome.outcome.lower():
                state.known_clues.append(f"Clue found in scene {state.current_plot_count}")
            
            if yield_updates:
                with st.expander(f"Scene {state.current_plot_count} Outcome"):
                    st.write(f"**Action:** {outcome.action_taken}")
                    st.write(f"**Outcome:** {outcome.outcome}")
                    st.write(f"**Stakes:** {outcome.suspense_element}")
        
        # Tick down the clock (suspense element)
        state.remaining_time -= 1
        
    if yield_updates:
        st.write("✍️ **Step 3:** Investigation complete! Passing raw events to the Narrator...")
        
    final_story = run_narrator(state.completed_scenes)
    
    return ground_truth, final_story
