
# Workflow for team project

## Software pre-requisites
1. Python 3.9.4
2. A PostgreSQL server install: https://www.postgresql.org/download
3. [Optional] A PostgreSQL GUI tool
    - Recommendations in (increasing) order of complexity/features: PostBird, Beekeeper, pgAdmin 4
4. Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
    - Validate installation with `heroku version`
5. Your preferred Python editor (I'll be using PyCharm: https://www.jetbrains.com/pycharm/)
6. [Optional] GitHub CLI (https://cli.github.com) or GitHub Desktop (https://desktop.github.com)

## Initial setup
1. Pull the initial project from GitHub (https://github.com/shirtandtieler/Job-Website-Project.git)
    - In PyCharm, close any open projects (File > Close Project) then click "Get From VCS" and paste in the .git URL
2. Create a new virtual environment and install the requirements
    - In PyCharm:
      - File > Settings > Project > Python Interpreter > Gear icon > Add > Virtualenv environment, Python 3.9 > OK
      - Open the 'requirements.txt' file. You should see a message that says "Package requires ..." at the top; click "install requirements" > Install
   
3. Run the command `heroku login` then follow the prompts
4. Download the initial database:
	- Navigate in your terminal (using `cd`) to a writable directory where the initial download can be (e.g., downloads)
	- To download the latest backup, run `heroku pg:backups:download -a jobsite-project`
	
5. Load the initial database into your local PostgreSQL instance:
	- Using the command line or your preferred PostgreSQL GUI tool, create a new empty database called "jobsite"
	- Run the command `pg_restore --verbose --clean --no-acl --no-owner -h localhost -U postgres -d jobsite latest.dump`
		- (Replace "postgres" with another user name if you have a different account setup)
		- There might be some warnings, but they should be safe to ignore
6. **Before starting development, skip to the "Running the website locally" section to make sure your setup is correct.**


## Working on the website & pushing changes
To avoid overlap or interferance when working on a part of the website, we will make use of "branches" to isolate our work (sometimes from each other, sometimes from different parts of the website being worked on). The default branch, called "main", is what will be reserved for the production-ready code that's pushed to the Heroku site. Protections will be placed on the "main" branch to make sure you cannot directly update that code. 

To work on the website, do the following:

1. Before anything else, perform a pull request to make sure the files you have are up to date.
	- In PyCharm: Git > Update Project
		- If it asks about merging or rebasing, select the option for merge and then click "Don't ask again"
2. If you want to branch off of "main", create a new branch. Give it a name based on what you're working on or your own name. 
	- In PyCharm: Git > New Branch...
3. Edit to your liking. Periodically, commit your changes; this will serve as a "checkpoint" that you can rollback to.
	- It's *very* important to write descriptive commit messages that briefly describe your changes (e.g., "Add endpoints for company profiles", "New columns in user model", "Update home template")
	- In PyCharm: Git > Commit
		- You can uncheck any files/folders not part of the current commit to split it up into multiple commits
4. When you are done coding or you believe your changes are complete and confirmed working, push the changes to GitHub
	- In PyCharm: Git > Push
5. When you are done with the branch and want to merge it into the main site, submit a Pull Request. 
	- In PyCharm: Git > GitHub > Create Pull Request
	- Describe your major changes
	- After submitting it, you can view your request on GitHub; it will be reviewed and most likely added to the main branch!


## Running the website locally
When the website needs to connect to the database, it attempts to check the system variable `DATABASE_URL`. When pushed to Heroku, the `DATABASE_URL` is setup to its internal database. If it's not set (the default local setup), it will use the credentials shown in `config.py` (connecting to the db "jobsite" with the username "user" and password of "password").  There are two ways for you to get this to work with your local system:
1. Create a new user in your local postgresql instance with these credentials
2. Before running the  website, set the `DATABASE_URL` system variable with the URL of your local database. Use the format mentioned in the config.py file.
	- The variable can be set with `export DATABASE_URL=...` (Mac/Linux) or `set DATABASE_URL=...` (Windows)
	- This will need to be done each time you re-open PyCharm
3. Alter the tables' permissions to give access to your user, then edit the config.py file (don't push this though)

-----

To launch the website:
1. Ensure the terminal you use is navigated to the project directory with the virtual environment activated. 
	- PyCharm has a built-in terminal which activates the virtual environment by default
2. Ensure the database url is correctly set (as described above)
3. Run `flask run`. It will report a local URL that it's running on (e.g., http://127.0.0.1:5000/)
4. If, inside the .flaskenv file, the variable `FLASK_ENV` is set to `development`, you can now make changes to the files and the website will refresh itself.