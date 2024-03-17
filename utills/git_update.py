import os
import easygui as eg
from dotenv import load_dotenv

# Ask the user for the commit message using a pop-up dialog
commit_message = eg.enterbox("Enter a commit message:", "Git Commit")
load_dotenv()
FOLDER_PATH = os.getenv("FOLDER_PATH")
if commit_message:
    # Execute Git commands
    os.chdir(FOLDER_PATH)
    os.system('git add .')
    os.system(f'git commit -m "{commit_message}"')
    os.system('git push')
else:
    eg.msgbox("No commit message entered. Operation canceled.", "Git Commit")