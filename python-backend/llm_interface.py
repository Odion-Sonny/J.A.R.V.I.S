import json
import logging
import os
import asyncio
import signal
from typing import Dict, Any
from gpt4all import GPT4All
from settings_manager import settings

class LLMInterface:
    def __init__(self, model_name: str = None):
        # Get model from settings, fallback to parameter or default
        self.model_name = model_name or settings.get_ai_model()
        self.model = None
        self.model_initialized = False
        self.use_mock_responses = settings.is_mock_mode()
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

    async def reload_settings(self):
        """Reload settings and reinitialize model if needed"""
        old_model_name = self.model_name
        old_mock_mode = self.use_mock_responses
        
        # Reload settings
        settings.load_settings()
        new_model_name = settings.get_ai_model()
        new_mock_mode = settings.is_mock_mode()
        
        # Check if model or mock mode changed
        if (old_model_name != new_model_name or old_mock_mode != new_mock_mode):
            logging.info(f"Settings changed: model {old_model_name} -> {new_model_name}, mock {old_mock_mode} -> {new_mock_mode}")
            
            self.model_name = new_model_name
            self.use_mock_responses = new_mock_mode
            
            # Reset model if we're switching to/from mock mode or different model
            if old_mock_mode != new_mock_mode or old_model_name != new_model_name:
                self.model = None
                self.model_initialized = False
                logging.info("Model will be reinitialized on next request")

    async def initialize(self):
        """Initialize the GPT4All model (assumes model is already downloaded)"""
        if self.model_initialized:
            return True
            
        # Check if we should use mock mode
        if self.use_mock_responses:
            logging.info("Using mock mode - no model initialization needed")
            self.model_initialized = True
            return True
            
        logging.info(f"Loading GPT4All model {self.model_name}...")
        
        try:
            # Run the model initialization in a thread (should be fast now since model is pre-downloaded)
            def init_model():
                return GPT4All(self.model_name, allow_download=False)
            
            # Use asyncio to run in executor with shorter timeout since model should exist
            loop = asyncio.get_event_loop()
            self.model = await asyncio.wait_for(
                loop.run_in_executor(None, init_model),
                timeout=60.0  # 1 minute timeout for loading existing model
            )
            
            self.model_initialized = True
            logging.info(f"GPT4All model {self.model_name} loaded successfully")
            return True
            
        except asyncio.TimeoutError:
            logging.error("Model loading timed out after 1 minute")
            self.model_initialized = False
            return False
        except Exception as e:
            logging.error(f"Failed to load GPT4All model: {e}")
            logging.error("Model may not be downloaded. Try running the startup script again.")
            self.model_initialized = False
            return False

    async def generate_response(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """Generate response from the LLM"""
        # Use mock responses if enabled (for testing without model download)
        if self.use_mock_responses:
            return self._generate_mock_response(user_input)
            
        if not self.model_initialized:
            success = await self.initialize()
            if not success:
                return {
                    "response": "I'm sorry, I'm having trouble initializing my AI model. You can try setting JARVIS_USE_MOCK=true for testing without the full model.",
                    "action": None,
                    "params": {}
                }
        
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
    
    def _generate_mock_response(self, user_input: str) -> Dict[str, Any]:
        """Generate mock responses for testing without model download"""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ["create", "make", "write", "file", "document"]):
            return {
                "response": "I'll create a document for you using mock mode.",
                "action": "create_document",
                "params": {"name": "test_document.txt", "content": "This is a test document created in mock mode."}
            }
        elif any(word in user_lower for word in ["find", "search", "look"]):
            return {
                "response": "I'll search for files using mock mode.",
                "action": "find_files", 
                "params": {"extension": "txt", "folder": "."}
            }
        elif any(word in user_lower for word in ["alarm", "reminder", "remind"]):
            return {
                "response": "I'll set a reminder for you using mock mode.",
                "action": "set_alarm",
                "params": {"minutes": 5, "message": "Test reminder"}
            }
        elif any(word in user_lower for word in ["system", "info", "status"]):
            return {
                "response": "Here's your system information in mock mode.",
                "action": "get_system_info",
                "params": {}
            }
        elif any(word in user_lower for word in ["open", "launch", "start"]):
            return {
                "response": "I'll open an application for you using mock mode.",
                "action": "open_app",
                "params": {"app_name": "calculator"}
            }
        else:
            return {
                "response": f"I understand you said: '{user_input}'. I'm running in mock mode for testing. Try asking me to create a file, set a reminder, or get system info!",
                "action": None,
                "params": {}
            }