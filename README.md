GenAI Create React App Scaffolder
This application uses OpenAI to help you generate React app scaffolding through a Streamlit interface.

Setup Instructions
1. Create a Virtual Environment
First, create a virtual environment to manage dependencies:

# Using venv (Python 3.3+)
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
2. Install Dependencies
Install the required packages:

pip install streamlit openai python-dotenv
or

pip install -r requirements.txt
3. Set Up Environment Variables
Create a .env file in the root directory of your project to store your OpenAI API key:

# Create .env file
touch .env
Add your OpenAI API key to the .env file:

OPENAI_API_KEY=your_openai_api_key_here
Note: Never commit your .env file to version control. Make sure to add it to your .gitignore file.

4. Running the Streamlit Application
Start the Streamlit app by running:

streamlit run chatbot.py
The application should now be running at http://localhost:8501

Usage
Enter your project specifications in the provided interface
The AI will generate React application scaffolding based on your requirements
Review and download the generated code
Requirements
Python 3.10+
OpenAI API key
Streamlit
python-dotenv
