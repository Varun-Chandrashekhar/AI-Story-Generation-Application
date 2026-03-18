import json
import os
from app import StateTracker, SceneOutcome
from app import run_crime_creator, run_investigation_generator, run_narrator

def generate_failed_story():
    print("Generating Failed Story...")
    os.environ["ST_MODE"] = "headless"
    
    ground_truth = run_crime_creator()
    state = StateTracker()
    
    # Intentionally bad loop: Detective gives up and falsely accuses someone immediately.
    action_hint = "The detective completely ignores all evidence, gets tired, and arrests the first person they see, claiming the case is closed."
    obstacle_hint = "The suspect cries and says they are innocent, but the detective doesn't care."
    
    outcome = run_investigation_generator(1, ground_truth, state, action_hint, obstacle_hint)
    
    if outcome:
        state.completed_scenes.append(outcome)
        state.current_plot_count = 1
        
    final_story = run_narrator(state.completed_scenes)
    
    with open("exemplar_fail.txt", "w") as f:
        f.write("=== GROUND TRUTH ===\n" + ground_truth.model_dump_json(indent=2) + "\n\n")
        f.write("=== FAILED NOVEL (Crime solved without clues/suspense) ===\n" + final_story)
        
    print("Saved to exemplar_fail.txt")

if __name__ == "__main__":
    generate_failed_story()
