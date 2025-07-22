# StoryForge: End-to-End Korean Manga Generation Pipeline

This system takes a natural language story and produces high-quality Korean manga pages, with robust intermediate outputs and quality assurance.

---

## 🚀 Workflow Overview

1. **Input Natural Story** (`examples/ryan_story.txt`)
2. **Scene Segmentation** (`manga_sty_parser.py`)
   - Segments the story into key visual scenes.
   - Outputs: `output/segmented_scenes.json`
3. **NPC & Schedule Parsing** (`examples/ryan_npc.yaml`)
   - Defines all NPCs, their available actions, and daily schedules.
4. **Action List Generation** (`action_list_parser.py`)
   - Reads `segmented_scenes.json` and `ryan_npc.yaml`
   - Outputs:
     - `output/daily.yaml`
     - `output/dramaCfg.json`
5. **Illustration Generation (Runway)** (`illustration_gen_runway.py`)
   - For each scene, generates a main illustration using the Runway API.
   - Outputs: `output/main_illustration_X_runway.png` (or similar for each scene)
6. **Manga Page Generation** (`manga_framer.py`)
   - Uses the panel analysis(crucial), segmented scenes, drama config, and generated illustrations to create final manga pages.
7. **QA Agent Step** (`qa_agent.py`)
   - Checks all outputs for consistency and completeness.
   - Uses both code-based checks and an OpenAI-based vision QA agent for illustrations and manga pages.
   - Retries up to 3 times and is tolerant (not overly strict).

---

## 🛠️ How to Run the Full Pipeline

1. **Segment the story:**
   ```bash
   python3 StoryForge/src/manga_sty_parser.py
   ```
2. **Generate action lists:**
   ```bash
   python3 StoryForge/src/action_list_parser.py
   ```
3. **Generate illustrations (Runway):**
   ```bash
   python3 StoryForge/src/illustration_gen_runway.py
   ```
4. **Generate manga pages:**
   ```bash
   python3 StoryForge/src/manga_framer.py
   ```
5. **Run QA agent:**
   ```bash
   python3 StoryForge/src/qa_agent.py
   ```

Or run the entire pipeline with:
```bash
python3 StoryForge/src/main.py
```

---

## 🧩 File Structure

```
StoryForge/
├── src/
│   ├── manga_sty_parser.py      # Scene segmentation (story → segmented_scenes.json)
│   ├── action_list_parser.py    # Action list generation (segmented_scenes.json + npc.yaml → daily.yaml, dramaCfg.json)
│   ├── illustration_gen_runway.py # Illustration generation (Runway)
│   ├── manga_framer.py          # Manga page generation
│   ├── qa_agent.py              # QA agent for output validation (code + OpenAI vision checks)
│   └── main.py                  # Master pipeline script
├── examples/
│   ├── ryan_story.txt           # Input story
│   └── ryan_npc.yaml            # NPC definitions
├── output/
│   ├── segmented_scenes.json
│   ├── daily.yaml
│   ├── dramaCfg.json
│   ├── main_illustration_X_runway.png
│   └── manga_pages/
```

---

## 🧑‍💻 QA Agent Details

- **Checks:**
  - Segmented scenes: required fields, valid structure
  - daily.yaml: all NPCs present
  - dramaCfg.json: all actions valid for NPCs
  - Illustrations: all files exist and are not empty
  - Manga pages: all files exist and are not empty
- **OpenAI Vision QA:**
  - For each illustration and manga page, sends the image and a tolerant but professional prompt to OpenAI
  - Checks for layout, style, and content issues (not overly strict)
  - Retries up to 3 times if needed
- **How to configure API key:**
  - Set the `OPENAI_API_KEY` environment variable or edit the config file as needed

---

## 💡 Tips

- The illustration generation step is essential for visual consistency and quality.
- If you change the story or scene segmentation, always rerun the illustration generation before manga page generation.
- The QA agent helps catch subtle or visual issues that code alone might miss.

---

## ❓ FAQ

- **Q: How do I add a new NPC or action?**
  - Edit `examples/ryan_npc.yaml` and rerun the pipeline.
- **Q: How do I ensure output quality?**
  - Use the QA agent step to automatically check for errors or inconsistencies, including visual checks with OpenAI.
- **Q: Can I use a different story?**
  - Edit `examples/ryan_story.txt` and rerun the pipeline.