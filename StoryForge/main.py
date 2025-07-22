import subprocess
import sys
import os

PIPELINE_STEPS = [
    ("Scene segmentation", "manga_sty_parser.py"),
    ("Action list generation", "action_list_parser.py"),
    ("Illustration generation (Runway)", "illustration_gen_runway.py"),
    # Uncomment the next line if you add a QA agent script
    # ("QA agent", "qa_agent.py"),
    ("Manga page generation", "manga_framer.py"),
]

SRC_DIR = os.path.dirname(os.path.abspath(__file__))

for step_name, script in PIPELINE_STEPS:
    script_path = os.path.join(SRC_DIR, script)
    print(f"\n=== {step_name}: {script} ===")
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"❌ Step failed: {step_name} ({script})")
        sys.exit(result.returncode)
    print(f"✅ Step completed: {step_name}")

print("\n🎉 All pipeline steps completed successfully!") 