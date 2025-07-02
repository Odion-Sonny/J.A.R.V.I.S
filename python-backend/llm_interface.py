import json
import logging
from typing import Dict, Any
from gpt4all import GPT4All

class LLMInterface:
    def __init__(self, model_name: str = "orca-mini-3b-gguf2-q4_0.gguf"):
        self.model_name = model_name
        self.model = None
        self.system_prompt = """You are JARVIS, a helpful AI assistant. You help users with various tasks.

IMPORTANT: You must respond with ONLY a JSON object in this exact format:
{
    "response": "Your helpful response to the user",
    "action": "action_name or null",
    "params": {"param": "value"}
}

Available actions:
- create_document: Create files. Params: {"name": "filename.txt", "content": "file content"}
- find_files: Search files. Params: {"extension": "txt", "folder": "."}
- set_alarm: Set reminders. Params: {"minutes": 5, "message": "reminder text"}
- open_app: Open applications. Params: {"app_name": "calculator"}
- get_system_info: Get system info. Params: {}
- read_document: Read files. Params: {"name": "filename.txt"}

Examples:
User: "Create a file called hello.txt"
Response: {"response": "I'll create a file called hello.txt for you.", "action": "create_document", "params": {"name": "hello.txt", "content": "Hello World!"}}

User: "What can you do?"
Response: {"response": "I can help you create files, set reminders, open apps, and get system information. What would you like me to do?", "action": null, "params": {}}

RESPOND ONLY WITH THE JSON OBJECT - NO OTHER TEXT."""

    async def initialize(self):
        """Initialize the GPT4All model"""
        try:
            self.model = GPT4All(self.model_name)
            logging.info(f"GPT4All model {self.model_name} loaded successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to load GPT4All model: {e}")
            return False

    async def generate_response(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """Generate response from the LLM"""
        if not self.model:
            await self.initialize()
        
        try:
            # Improved prompt with better structure
            prompt = f"""You are JARVIS, a helpful AI assistant. You help users with various tasks.

IMPORTANT: You must respond with ONLY a JSON object in this exact format:
{{"response": "Your helpful response to the user", "action": "action_name or null", "params": {{"param": "value"}}}}

Available actions:
- create_document: Create files. Params: {{"name": "filename.txt", "content": "file content"}}
- find_files: Search files. Params: {{"extension": "txt", "folder": "."}}
- set_alarm: Set reminders. Params: {{"minutes": 5, "message": "reminder text"}}
- open_app: Open applications. Params: {{"app_name": "calculator"}}
- get_system_info: Get system info. Params: {{}}
- read_document: Read files. Params: {{"name": "filename.txt"}}

Examples:
User: "Create a file called hello.txt"
JARVIS: {{"response": "I'll create a file called hello.txt for you.", "action": "create_document", "params": {{"name": "hello.txt", "content": "Hello World!"}}}}

User: "What can you do?"
JARVIS: {{"response": "I can help you create files, set reminders, open apps, and get system information. What would you like me to do?", "action": null, "params": {{}}}}

User: {user_input}
JARVIS:"""
            
            # Generate with better parameters for JSON output
            response = self.model.generate(
                prompt,
                max_tokens=256,
                temp=0.3,
                top_p=0.8,
                repeat_penalty=1.1
            )
            
            # Clean the response
            response = response.strip()
            
            # Extract JSON if wrapped in other text
            if response.startswith('```'):
                response = response.split('```')[1]
            if response.startswith('json'):
                response = response[4:].strip()
            
            # Try to parse JSON response
            try:
                parsed_response = json.loads(response)
                
                # Validate structure
                if not isinstance(parsed_response, dict):
                    raise ValueError("Response is not a dictionary")
                
                if "response" not in parsed_response:
                    parsed_response["response"] = "I understand your request."
                
                if "action" not in parsed_response:
                    parsed_response["action"] = None
                    
                if "params" not in parsed_response:
                    parsed_response["params"] = {}
                
                return parsed_response
                
            except (json.JSONDecodeError, ValueError) as e:
                logging.warning(f"JSON parsing failed: {e}, raw response: {response}")
                
                # Try to extract meaningful response
                if "create" in user_input.lower() and ("file" in user_input.lower() or "document" in user_input.lower()):
                    return {
                        "response": "I'll create a document for you.",
                        "action": "create_document", 
                        "params": {"name": "document.txt", "content": "Sample content"}
                    }
                elif "reminder" in user_input.lower() or "alarm" in user_input.lower():
                    return {
                        "response": "I'll set a reminder for you.",
                        "action": "set_alarm",
                        "params": {"minutes": 5, "message": "Reminder"}
                    }
                elif "find" in user_input.lower() or "search" in user_input.lower():
                    return {
                        "response": "I'll search for files.",
                        "action": "find_files",
                        "params": {"extension": "txt", "folder": "."}
                    }
                elif "system" in user_input.lower() or "info" in user_input.lower():
                    return {
                        "response": "Here's your system information.",
                        "action": "get_system_info",
                        "params": {}
                    }
                else:
                    return {
                        "response": response if len(response) < 200 else "I understand your request and will help you with that.",
                        "action": None,
                        "params": {}
                    }
                
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return {
                "response": "I'm sorry, I encountered an error processing your request.",
                "action": None,
                "params": {}
            }