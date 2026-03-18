# Phase I Final Presentation Script & Slide Outline

## Team Name: Blueberry Gorilla
**Members:** Rugved Rajendra, Varun Chandrashekhar, Keshav Garg

---

### Slide 1: Introduction & System Overview
- **Speaker:** "Welcome to our CS7634 Phase 1 presentation. We are team Blueberry Gorilla, and our system is called the *Detective's Dilemma Simulator*."
- **Content:** "We selected the **Suspense Generation** template. Our system leverages a "Meta-Controller" architecture to generate a thrilling murder mystery."
- **Key Point:** "To make the mystery non-trivial, we employed a **Double Story** method. First, we generate the 'Hidden Crime Story' (the ground truth), and second, we generate the active 'Solving Story' (the detective's investigation in real time). We introduced elements like red herrings, lying suspects, and time limits to heighten the tension."

### Slide 2: Architecture Walkthrough (Visual Diagram)
- **Speaker:** "Here is how our architecture works in practice."
- *(Point to Crime Creator)* "First, our **Crime Creator (LLM)** synthesizes the constraints: killer, motive, timeline. This feeds into our **Hidden Story DB**."
- *(Point to Meta-Controller)* "The **Meta-Controller** acts as the director. It takes these constraints and actively prompts the **Investigation Generator (LLM)**, injecting an action and an obstacle to ensure suspense."
- *(Point to State Tracker)* "The generated scene outcome is saved in the **State Tracker**. The Meta-Controller loops this exact cycle until we hit 15 plot points, checking consistency against the Hidden DB at each step."
- *(Point to Narrator)* "Finally, the raw history of events is passed to the **Narrator (LLM)**, which translates it into our final fluent mystery novel."

### Slide 3: Potential Pitfalls & How We Addressed Them
- **Speaker:** "We anticipated two major technical pitfalls."
- **Pitfall 1 (Suspense placement):** "The suspense could accidentally occur in the backstory rather than the actual investigation. By separating the Crime Creator from the Investigation Generator, we ensured the backstory was static, forcing all the suspense to happen only during the detective's active pursuit."
- **Pitfall 2 (Contradictions):** "LLMs tend to hallucinate contrary facts across long contexts. We addressed this by implementing the **State Tracker** and **Hidden Story DB**, ensuring that every prompt sent to the LLM during the 15-loop sequence included the strict ground-truth constraints."

### Slide 4: Template-Specific Questions
- **Speaker:** "To answer the specific questions for the Suspense template regarding pre-generation vs dynamic generation:"
- **Answer:** "We chose to *pre-generate* the crime details heavily upfront. To adapt our iterative technique to use these details without losing the thread, we consolidated the pre-generated story into a strict JSON dictionary. This dictionary, acting as our 'Ground Truth', was fed into every single subsequent prompt in the solving story, ensuring the detective's timeline always aligned with the predetermined murder facts."

### Slide 5 & 6: Exemplar Output Review
- **Speaker:** "Let's look at the output our system produces."
- **Successful Story Showcase:** Show an excerpt of `exemplar_success.txt`, explicitly pointing out the numbered plot points (1-15). "Here you can see the detective overcoming obstacles, uncovering clues, and dealing with red herrings before arresting the true killer identified in the DB."
- **Mis-Spun Story Showcase:** Show an excerpt of `exemplar_fail.txt`. "Here is an unsuccessful run. In this scenario, the system failed because the detective bypassed all evidence and arrested the first person without gathering clues. This is caused by the LLM ignoring the structural prompt constraints, overriding the investigation logic to close the story early. Our Meta-Controller limits this by enforcing a hard 15-loop count, but semantic failures can still occur."

### Slide 7: Conclusion & QA
- **Speaker:** "Thank you for watching."
