PELEC ATM Simulator

A Django-based ATM Simulator application.

--Follow these exact steps from top to bottom to get the project working on your local machine.---

1. Download and Clone the Repository
Open your Terminal (Mac) or Command Propmt / Powershell (Windows) and run: 

```bash
git clone [https://github.com/nicolejaneabing5-sudo/PELEC1_atm-simulator.git](https://github.com/nicolejaneabing5-sudo/PELEC1_atm-simulator.git)
cd PELEC1_atm-simulator

2. Set Up Your Virtual Environment (venv)

On Windows:

python -m venv venv
venv\Scripts\activate

On Mac / Linux:

python3 -m venv venv
source venv/bin/activate

3. Install Django & Dependencies
Make sure your virtual environment (venv) is active, then run:

pip install django

4. Initialize the Database (not necessary)
Run the initial migrations to set up your local database:

python manage.py makemigrations
python manage.py migrate

5. Start the Development Server

python manage.py runserver

--Open your browser and visit: http://127.0.0.1:8000/ to confirm if works!

--Daily Git Workflow for Team Members---

Team Workflow: Feature Branches

To keep our codebase clean and prevent conflicts, never push directly to dev or main, same ka sir Raph nga gitudlo. Every team member must work on their own assigned feature branch.

Step 1: Switch to dev and Get Latest Updates
-Before Starting any new work, switch to the dev branch and pull the latest changes.

git checkout dev
git pull origin dev

Step 2: Create Your own Feature Branch
-Create and switch to a new branch names after your assigned feature or task:

git checkout -b feature-your-task-name

example:
git checkout -b feature-html-desgin
git checkout -b feature-login-page
git checkout -b feature-deposit-view

Step 3: Write Code and Commit Changes
-Do your assigned work in VS Code, then stage and commit your changes with a clear message:

git add .
git commit -m "Add HTML Layout for ATM dashboard"

Step 4: Push Your Feature Branch to Github
-Push your local feature  branch up  to Github:

git push -u origin feature-your-task-name

Step 5: Open a Pull Request (PR)
Go to the repository page on GitHub: https://github.com/nicolejaneabing5-sudo/PELEC1_atm-simulator

Click the Compare & pull request banner that appears.

Set the base branch to dev and the compare branch to feature-your-task-name (dev ← feature-your-task-name).

Add a short title and description of your changes, then click Create pull request.

Notify the project leader to review and merge your Pull Request into dev..