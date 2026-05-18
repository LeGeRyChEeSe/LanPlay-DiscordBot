#!/usr/bin/env python3
import os
import subprocess
import time
import sys
from pathlib import Path

# Configuration
PROJECT_DIR = Path("/home/kilian/bots/LanPlay-DiscordBot")
STORIES_DIR = PROJECT_DIR / "docs" / "stories"
CLAUDE_CODE_CMD = "claude"  # Claude Code CLI
MAX_REVIEW_ATTEMPTS = 3
COMMIT_BASELINE_MSG = "chore: baseline before story {}"
COMMIT_FEAT_MSG = "feat: implement story {} - {}"

# Ensure we are in the project directory
os.chdir(PROJECT_DIR)

def run_command(cmd, cwd=None, check=True, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd or PROJECT_DIR,
            capture_output=capture_output, text=True, check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}")
        print(f"Error: {e}")
        if check:
            raise
        return e

def get_story_files():
    """Return a sorted list of story markdown files."""
    story_files = sorted(STORIES_DIR.glob("STORY-*.md"))
    return story_files

def get_story_id_and_title(story_path):
    """Extract story ID and title from the story file."""
    # Story ID is the filename without extension
    story_id = story_path.stem
    # Try to read the first line as title (assuming markdown header)
    try:
        with open(story_path, 'r') as f:
            first_line = f.readline().strip()
            # If it's a markdown header, extract the title
            if first_line.startswith('#'):
                title = first_line.lstrip('#').strip()
            else:
                title = story_id
    except Exception:
        title = story_id
    return story_id, title

def commit_baseline(story_id):
    """Commit current state as baseline for the story."""
    # Check if there are changes to commit
    result = run_command("git diff-index --quiet HEAD --", check=False)
    if result.returncode != 0:
        # There are changes, commit them
        run_command("git add -A")
        msg = COMMIT_BASELINE_MSG.format(story_id)
        run_command(f'git commit -m "{msg}"')
        print(f"Committed baseline for story {story_id}")
    else:
        print(f"No changes to commit for baseline of story {story_id}")

def commit_feature(story_id, title):
    """Commit the feature implementation."""
    run_command("git add -A")
    msg = COMMIT_FEAT_MSG.format(story_id, title)
    run_command(f'git commit -m "{msg}"')
    print(f"Committed feature for story {story_id}: {title}")

def reset_to_baseline():
    """Reset the current branch to the last commit (discarding uncommitted changes)."""
    run_command("git reset --hard HEAD")
    print("Reset to baseline (last commit)")

def ask_claude(prompt):
    """Ask Claude Code to perform a task and return the output."""
    # We use --print for non-interactive output, --permission-mode bypassPermissions to allow edits,
    # and --add-dir to give access to the project directory.
    cmd = f'{CLAUDE_CODE_CMD} --print --permission-mode bypassPermissions --add-dir "{PROJECT_DIR}" "{prompt}"'
    print(f"Running Claude Code with prompt (first 100 chars): {prompt[:100]}...")
    result = run_command(cmd, capture_output=True, check=False)
    return result.stdout

def implement_story(story_path):
    """Implement a single story using Claude Code."""
    story_id, title = get_story_id_and_title(story_path)
    print(f"\n=== Processing story {story_id} ===")
    
    # Read the story content
    with open(story_path, 'r') as f:
        story_content = f.read()
    
    # Step 1: Commit baseline
    commit_baseline(story_id)
    
    # Step 2: Loop for implementation and review
    review_feedback = ""
    for attempt in range(1, MAX_REVIEW_ATTEMPTS + 1):
        print(f"Attempt {attempt} of {MAX_REVIEW_ATTEMPTS}")
        
        if attempt == 1:
            # First attempt: ask for implementation
            prompt = f"""Implement the following story according to the acceptance criteria.
When you have finished implementing and are ready for review, output the string 'IMPLEMENTATION_COMPLETE' on its own line.

Story ID: {story_id}
Title: {title}

Acceptance Criteria:
{story_content}
"""
        else:
            # Subsequent attempts: ask to fix issues based on review feedback
            prompt = f"""Please fix the issues identified in the review.
After making the fixes and are ready for review, output the string 'IMPLEMENTATION_COMPLETE' on its own line.

Review feedback:
{review_feedback}

Original story acceptance criteria:
{story_content}
"""
        
        # Ask Claude Code to implement/fix
        output = ask_claude(prompt)
        print(f"Claude Code implementation output (first 200 chars): {output[:200]}")
        
        # Check if implementation signaled completion
        if "IMPLEMENTATION_COMPLETE" not in output:
            print("Warning: Implementation did not signal completion. Proceeding to review anyway.")
        
        # Now ask for review
        review_prompt = f"""Please review the implementation against the acceptance criteria of the story.
Check that all acceptance criteria are met.
If there are issues, describe them clearly.
If the implementation is satisfactory, output the string 'REVIEW_PASSED' on its own line.

Story acceptance criteria:
{story_content}
"""
        
        review_output = ask_claude(review_prompt)
        print(f"Claude Code review output (first 200 chars): {review_output[:200]}")
        
        # Check if review passed
        if "REVIEW_PASSED" in review_output:
            print(f"Review passed on attempt {attempt}.")
            # Commit the feature implementation
            commit_feature(story_id, title)
            return True
        else:
            print(f"Review attempt {attempt} failed.")
            review_feedback = review_output
            # If we have more attempts, we'll loop and ask for fixes
            if attempt < MAX_REVIEW_ATTEMPTS:
                print("Will attempt to fix issues...")
            else:
                print(f"Exhausted {MAX_REVIEW_ATTEMPTS} attempts for story {story_id}.")
    
    # If we get here, all attempts failed
    print(f"Review failed after {MAX_REVIEW_ATTEMPTS} attempts for story {story_id}. Resetting to baseline.")
    reset_to_baseline()
    return False

def main():
    """Main loop over all stories."""
    story_files = get_story_files()
    if not story_files:
        print("No story files found in", STORIES_DIR)
        return 1
    
    print(f"Found {len(story_files)} story files.")
    
    for story_file in story_files:
        success = implement_story(story_file)
        if not success:
            print(f"Story {story_file.stem} failed after max attempts. Moving on.")
    
    print("\nAll stories processed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())