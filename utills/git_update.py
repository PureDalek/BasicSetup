import os
import sys
import easygui as eg
from dotenv import load_dotenv

def execute_git_commands(commit_message):
    """Execute git commands to add, commit, and push changes."""
    load_dotenv()
    folder_path = os.getenv("FOLDER_PATH")
    if folder_path:
        os.chdir(folder_path)
        os.system('git add .')
        os.system(f'git commit -m "{commit_message}"')
        os.system('git push')
    else:
        print("FOLDER_PATH environment variable is not set. Operation canceled.")

def main():
    # Check if a commit message is provided as a command-line argument
    if len(sys.argv) > 2 and sys.argv[1] == "-m":
        commit_message = sys.argv[2]
    else:
        # Ask the user for the commit message using a pop-up dialog
        commit_message = eg.enterbox("Enter a commit message:", "Git Commit")
    
    if commit_message:
        execute_git_commands(commit_message)
    else:
        eg.msgbox("No commit message entered. Operation canceled.", "Git Commit")

if __name__ == "__main__":
    main()
