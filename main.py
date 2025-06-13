from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
import os
import subprocess

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Tool Definitions ---
def run_command(cmd: str):
    """Executes shell commands safely with output capture"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        return result.stdout if result.returncode == 0 else f"Error (code {result.returncode}): {result.stderr}"
    except Exception as e:
        return f"Command execution failed: {str(e)}"

def get_weather(city: str):
    """Fetches weather data"""
    url = f"https://wttr.in/{city}?format=%C+%t"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return f"Weather in {city}: {response.text.strip()}"
    except requests.RequestException:
        return "Weather service unavailable"

def read_file(file_path: str):
    """Reads file content"""
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        if os.path.getsize(file_path) > 1000000:
            return "File too large (max 1MB)"
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Read error: {str(e)}"

def write_file(file_path: str, content: str):
    """Writes to file"""
    try:
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return f"File written: {file_path}"
    except Exception as e:
        return f"Write error: {str(e)}"

# --- Available Tools ---
TOOLS = {
    "get_weather": get_weather,
    "run_command": run_command,
    "read_file": read_file,
    "write_file": write_file
}

# --- System Prompt ---
SYSTEM_PROMPT = """
You are a React expert assistant with three modes:
1. SCAFFOLDING: Guides through app creation
2. TOOLS: Uses available functions
3. QA: Answers React questions

Respond in strict JSON format:
{
  "mode": "SCAFFOLDING|TOOLS|QA",
  "response": "User message",
  "function": "Tool name (if TOOLS)",
  "parameters": {"key": "value"} 
}

Scaffolding Flow:
1. Ask framework (React, React-SWC, Preact)
2. Ask variant (JavaScript/TypeScript)
3. Ask project name
4. Generate command

Tool Parameters:
- get_weather: {"city": "New York"}
- run_command: {"cmd": "ls -la"}
- read_file: {"file_path": "src/App.js"}
- write_file: {"file_path": "test.txt", "content": "Hello"}

Examples:
User: Create React app
→ {"mode": "SCAFFOLDING", "response": "Which framework? (React, React-SWC, Preact)"}

User: React
→ {"mode": "SCAFFOLDING", "response": "JavaScript or TypeScript?"}

User: TypeScript
→ {"mode": "SCAFFOLDING", "response": "Project name?"}

User: my-app
→ {"mode": "TOOLS", "function": "run_command", "parameters": {"cmd": "npm create vite@latest my-app --template react-ts"}, "response": "Creating app..."}
"""

# --- Scaffolding State ---
class ScaffoldingState:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.active = False
        self.framework = None
        self.variant = None
        self.project_name = None
        
    def start(self):
        self.active = True
        self.reset()
        return "Which framework? (React, React-SWC, Preact)"
    
    def set_framework(self, value):
        self.framework = value.lower()
        return "JavaScript or TypeScript?"
    
    def set_variant(self, value):
        self.variant = value.lower()
        return "Project name?"
    
    def set_name(self, value):
        self.project_name = value
        self.active = False
        return self.generate_command()
    
    def generate_command(self):
        templates = {
            ("react", "javascript"): "react",
            ("react", "typescript"): "react-ts",
            ("react-swc", "javascript"): "react-swc",
            ("react-swc", "typescript"): "react-swc-ts",
        }
        template = templates.get((self.framework, self.variant), "react")
        return f"npm create vite@latest {self.project_name} --template {template}"

# --- Main Execution ---
def main():
    scaffold = ScaffoldingState()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    print("⚛️ React Assistant: How can I help with React today?")
    print("Type 'exit' to quit or 'new' to create app\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
                
            # Handle special commands
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            if user_input.lower() == "new":
                print(f"Assistant: {scaffold.start()}")
                continue
                
            # Handle scaffolding flow
            if scaffold.active:
                if not scaffold.framework:
                    print(f"Assistant: {scaffold.set_framework(user_input)}")
                elif not scaffold.variant:
                    print(f"Assistant: {scaffold.set_variant(user_input)}")
                elif not scaffold.project_name:
                    command = scaffold.set_name(user_input)
                    print(f"🛠️ Executing: {command}")
                    result = run_command(command)
                    print(f"✅ Result: {result[:200]}{'...' if len(result) > 200 else ''}")
                continue
                
            # Add user message to history
            messages.append({"role": "user", "content": user_input})
            
            # Get AI response
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=messages,
                temperature=0.3
            )
            
            # Parse response
            ai_content = response.choices[0].message.content
            try:
                ai_response = json.loads(ai_content)
            except json.JSONDecodeError:
                print("⚠️ Invalid response format")
                continue
                
            # Add to message history
            messages.append({"role": "assistant", "content": ai_content})
            
            # Process response
            mode = ai_response.get("mode", "QA")
            response_text = ai_response.get("response", "I can help with React questions")
            
            # Print assistant response
            print(f"Assistant: {response_text}")
            
            # Execute tools if requested
            if mode == "TOOLS":
                tool_name = ai_response.get("function")
                params = ai_response.get("parameters", {})
                
                if tool_name and tool_name in TOOLS:
                    tool_fn = TOOLS[tool_name]
                    try:
                        # Special handling for write_file
                        if tool_name == "write_file":
                            result = tool_fn(
                                params.get("file_path", ""), 
                                params.get("content", "")
                            )
                        # Handle other tools
                        else:
                            param = list(params.values())[0] if params else ""
                            result = tool_fn(param)
                            
                        print(f"🔧 Tool result: {result[:200]}{'...' if len(result) > 200 else ''}")
                    except Exception as e:
                        print(f"⚠️ Tool error: {str(e)}")
                else:
                    print("⚠️ Invalid tool request")
                    
        except KeyboardInterrupt:
            print("\nSession ended")
            break
        except Exception as e:
            print(f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    main()