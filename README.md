# CS7634 Phase 1: AI Storytelling

**Team Name:** Blueberry Gorilla
**Team Members:** Rugved Rajendra, Varun Chandrashekhar, Keshav Garg
**Template:** Suspense Generation
**System Name:** Silverback Suspense Generation

## How to Test the System

### Method A: Live Deployment (Recommended)

You can directly test and interact with our system through our live Streamlit deployment:
**[https://blueberry-gorilla.streamlit.app/](https://blueberry-gorilla.streamlit.app/)**

Once on the deployed app, open the sidebar panel on the left to securely paste your OpenAI API Key, and then click "Generate Mystery Novel 📖" to begin.

---

### Method B: Running Locally

If you prefer to run the system on your own machine, follow these instructions:

#### 1. Installation

Ensure you have Python 3.9+ installed and running. Open a terminal in this directory and install the requirements:

```bash
pip install -r requirements.txt
```

#### 2. API Key Configuration

This system runs on OpenAI models (`gpt-4o-mini` and `gpt-4o`). To provide your API key, simply run the application and paste it directly into the secure sidebar panel on the left side of the screen.

#### 3. Launching the App

Run the following command to start the application:

```bash
streamlit run app.py
```

This will open a browser window to `http://localhost:8501`. Click "Generate Mystery Novel 📖" to begin!


Expected Runtime and Costs:
Expected Runtime and Costs:
Run Time: Generating the ground truth, 15 individual investigation loops, and the final narrative takes approximately 90 to 120 seconds to complete.
Cost: The system primarily uses `gpt-4o-mini` for the loops and `gpt-4o` for the final narration. The estimated cost per full story generation is roughly $0.06 - $0.15 depending on story length.


Successful Example Output Story:
It was a chilly autumn afternoon when Detective Sam Caldwell arrived at the crime scene, the smell of freshly fallen leaves mingling with the distant echoes of city life in the afternoon air. Elena Thompson, a bright young woman with her whole life ahead of her, lay lifeless in her apartment. The signs of a struggle were clear—a vase shattered on the floor, doors left ajar—but nothing was more telling than the small pool of blood next to the kitchen counter.

Caldwell surveyed the apartment with his sharp eyes, noting every detail before turning his attention to the kitchen. The first clue to catch his interest was a missing knife. It set his instincts alight with suspicion. This wasn’t a random crime, he thought.

Daniel Reed was the first name on their list. A quick visit to his apartment revealed a freshly washed kitchen knife on the drying rack. The meticulous cleanliness, the scent of recent bleach—it screamed a desperate attempt to erase something damning. Just as Caldwell considered his next move, footsteps echoing outside signaled Daniel’s return. The detectives hid, tense, and quickly decided on a strategic retreat with photos as evidence.

Meanwhile, Caldwell’s partner, Detective Mason Ryan, interrogated the second suspect, Mark Wilson, at his workplace. Mark was calm, but the revelation of a delivery receipt for flowers sent anonymously to Elena two days before her death aroused their interest. Mark claimed ignorance of the sender, his coworkers confirming his alibi. Despite his frustration over Daniel’s possessiveness toward Elena, his apprehension about losing a close friend was genuine, not sinister.

With suspicions redirected, they soon paid a visit to Tara Smith, Elena's best friend, drawing the lines of past entanglements into sharper focus. Hidden in her drawer was a note with peculiar details about the flower delivery, implying deeper involvement than she admitted. Her evasiveness and willingness to glance repeatedly at that very drawer set Detective Caldwell’s mind in motion.

Tara’s nervousness bore fruit to new paths. Caldwell and Ryan switched focus to Karen, Elena’s sister. Karen had voiced her concerns about Daniel’s increasingly controlling behavior, and her alibi at dinner with their parents during the time of the murder was rock-solid. While she harbored worry about what Daniel might do, it was far removed from involvement in the gruesome act.

Detectives soon received an anonymous tip prompting them back to Tara’s apartment. With urgency, they secured a warrant. Surveilling her hurried attempts to discard evidence, they intercepted a garbage bag containing a bloodied cloth in her car trunk. When confronted, her denials were paper thin, and with no substantive alibi, suspicions lingered.

Compelled by newfound evidence, they faced Daniel again, discovering a discarded bloodied kitchen towel under his sink, still faintly tainted with bleach. Daniel's defenses wavered under intense scrutiny, trying to steer blame towards Tara, further clouding the tumultuous relationships at play.

Then came a compelling clue—a hidden camera device at Daniel’s that hinted at surveillance over Elena’s last hours. Confrontation only yielded agitated excuses about personal protection, yet glitches on recordings suggested deliberate tampering to obscure critical details.

The narrative grew taut, and the detectives could almost feel the distorted timeline click into place. The brilliance of Daniel’s intended deceit began to unravel further when the detectives traced tampered footage to evidence showing Daniel arriving at the exact time Elena allegedly met her demise. Hidden compartments in Mark’s apartment bore blood traces, indicating a staging ground for false evidence.

Yet, it was the tumultuous, climactic raid on Daniel’s kitchen—the detectives finding him nervously rearranging items as though preparing for a hasty exit—that turned the tide. A kitchen knife, blood-streaked and concealed among innocuous papers, linked him inseparably to the murder.

Finally, faced with irrefutable evidence, Daniel’s intricate but fraying tapestry of misdirection came undone. The true story emerged like puzzle pieces finally snapped into place: enamored with Elena, frantic at her intention to leave him for Mark, Daniel snapped and, in a moment of desperate rage, reached for the nearest weapon.

From a café eavesdropping to her apartment in the evening, the plan simmered beneath a façade of reconciliation until it hit a boiling point. The murder concluded, Daniel feverishly attempted to clean, manipulate, create alibis, and implicate Mark with conniving deceit that included the strewn bloodied items later discovered.

Thus, the spectrum of tension, deceit, and obsession reached full spectrum, leaving the detectives, at last, free to take Daniel into custody—his illusions shattered by sheer evidence and unwavering investigative resolve, leaving no ambiguity about the tragic sequence. The reckoning, though bittersweet, culminated in justice for Elena, irrevocably sealing Daniel’s fate behind bars.

Plot points
Plot Point 1: Investigate Daniel Reed's apartment to search for the kitchen knife and gather evidence of his potential motives.

Plot Point 2: Interview Mark Wilson at his workplace to gather his alibi and see if he noticed anything suspicious relating to Elena or Daniel.

Plot Point 3: Interview Tara Smith at her home to gather insights on her relationship with Elena and any knowledge of Daniel's behavior.

Plot Point 4: Investigate Karen Thompson at her dinner with parents to establish her alibi and see if she had any concerns about Daniel.

Plot Point 5: Investigate the crumpled note found in Tara's drawer by securing a warrant to analyze its contents and any fingerprints that could tie it to her communication about the flowers.

Plot Point 6: Investigators decide to confront Daniel Reed about the crumpled note found in Tara's drawer which implicates him in potentially using her to frame Mark, setting up direct confrontation regarding his involvement with the knife.

Plot Point 7: Investigate Mark Wilson by confronting him about the knife found in Daniel's home and his potential involvement in the conflict between Daniel and Elena.

Plot Point 8: Investigate the kitchen of Daniel Reed to search for further evidence or signs of tampering related to the knife and any further manipulation of the murder narrative.

Plot Point 9: Search Tara Smith's house for more evidence related to Elena’s murder, focusing on her recent interactions with both the victim and Mark.

Plot Point 10: Conduct a follow-up interview with Daniel Reed, confronting him with the evidence of the bloodied cloth found in Tara's car, and pressing him about his whereabouts at the time of the murder.

Plot Point 11: Investigate Mark Wilson's work place for any connections to the knife and Daniel's interference.

Plot Point 12: The detectives confront Daniel Reed at his apartment to search for the kitchen knife he may have hidden in order to frame Mark, pressing him about the contents of his kitchen.

Plot Point 13: Investigate Daniel Reed's home for any further evidence of interference, particularly focusing on any additional items that could connect him to the murder or verify his intent to frame Mark.

Plot Point 14: Confront Daniel Reed again, this time about the hidden camera and any recordings it may have, suggesting that he could be tampering with evidence related to the murder.

Plot Point 15: Investigate the hidden camera recordings to gather evidence of Daniel's intentions around the time of the murder.

Plot Point 16: Investigate Daniel Reed's kitchen to search for the murder weapon and any evidence related to the tampering of the knife.

Plot Point 17: Investigate Mark Wilson's apartment to check for the hidden knife Daniel is allegedly trying to frame him with.

Plot Point 18: Investigate Daniel Reed's apartment again to confront him about traces of the knife and any further evidence tampering.
