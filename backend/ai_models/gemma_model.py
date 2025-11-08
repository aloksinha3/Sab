import os
import json
from typing import List, Optional
import yaml

# Try to import torch and transformers, but make them optional
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    AutoTokenizer = None
    AutoModelForCausalLM = None

class FineTunedMedGemmaAI:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.model_name = self.config.get("ai", {}).get("model_name", "google/gemma-2b-it")
        self.use_cpu = self.config.get("ai", {}).get("use_cpu", True)
        self.max_length = self.config.get("ai", {}).get("max_length", 512)
        
        self.device = "cpu" if self.use_cpu else ("cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self._load_model()
        self._load_training_data()
    
    def _load_config(self, config_path: str) -> dict:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_training_data(self):
        """Load pregnancy care training data"""
        training_data_path = "medgemma_training_data.json"
        if os.path.exists(training_data_path):
            with open(training_data_path, 'r') as f:
                self.training_data = json.load(f)
        else:
            # Default training data structure
            self.training_data = {
                "topics": {
                    "weekly_checkin": "Weekly pregnancy check-in messages",
                    "medication_reminder": "Medication reminder messages",
                    "appointment_notification": "Appointment notification messages",
                    "high_risk_monitoring": "High-risk pregnancy monitoring messages"
                },
                "risk_categories": {
                    "low": "Low-risk pregnancy messaging",
                    "medium": "Medium-risk pregnancy messaging",
                    "high": "High-risk pregnancy messaging"
                }
            }
    
    def _load_model(self):
        """Load the Gemma model"""
        if not TORCH_AVAILABLE:
            print("⚠️ PyTorch and transformers not installed. Using fallback text generation.")
            print("⚠️ Install AI dependencies with: pip install -r requirements-ai.txt")
            self.model = None
            self.tokenizer = None
            return
        
        try:
            print(f"Loading model {self.model_name} on {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if not self.use_cpu else torch.float32,
                device_map="auto" if not self.use_cpu else None
            )
            if self.use_cpu:
                self.model = self.model.to(self.device)
            self.model.eval()
            print("✅ Model loaded successfully")
        except Exception as e:
            print(f"⚠️ Could not load model: {e}")
            print("⚠️ Using fallback text generation")
            self.model = None
            self.tokenizer = None
    
    def generate_personalized_ivr_message(
        self,
        topic: str,
        patient_name: str,
        gestational_age_weeks: int,
        risk_factors: List[str] = None,
        risk_category: str = "low",
        medications: List[str] = None
    ) -> str:
        """Generate a personalized IVR message for a patient"""
        
        risk_factors = risk_factors or []
        medications = medications or []
        
        # Build the prompt
        prompt = self._build_prompt(
            topic, patient_name, gestational_age_weeks,
            risk_factors, risk_category, medications
        )
        
        # Generate message
        if self.model and self.tokenizer:
            try:
                message = self._generate_with_model(prompt)
            except Exception as e:
                print(f"⚠️ Model generation failed: {e}, using fallback")
                message = self._generate_fallback_message(
                    topic, patient_name, gestational_age_weeks,
                    risk_factors, risk_category, medications
                )
        else:
            message = self._generate_fallback_message(
                topic, patient_name, gestational_age_weeks,
                risk_factors, risk_category, medications
            )
        
        # Add "Press 1" functionality
        message += "\n\nPress 1 if you'd like to leave a message for our medical team."
        
        return message
    
    def _build_prompt(
        self,
        topic: str,
        patient_name: str,
        gestational_age_weeks: int,
        risk_factors: List[str],
        risk_category: str,
        medications: List[str]
    ) -> str:
        """Build a prompt for the AI model"""
        
        prompt = f"""Generate a personalized, warm, and medically accurate IVR message for a pregnant patient.

Patient Information:
- Name: {patient_name}
- Gestational Age: {gestational_age_weeks} weeks
- Risk Category: {risk_category}
- Risk Factors: {', '.join(risk_factors) if risk_factors else 'None'}
- Medications: {', '.join(medications) if medications else 'None'}

Message Type: {topic}

Guidelines:
- Use a warm, supportive, and professional tone
- Be concise (2-3 sentences maximum)
- Include relevant medical information
- Personalize based on gestational age and risk factors
- Ensure medical accuracy

Generate the IVR message:"""
        
        return prompt
    
    def _generate_with_model(self, prompt: str) -> str:
        """Generate message using the Gemma model"""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=self.max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the generated part (after the prompt)
        if prompt in generated_text:
            generated_text = generated_text[len(prompt):].strip()
        
        return generated_text
    
    def _generate_fallback_message(
        self,
        topic: str,
        patient_name: str,
        gestational_age_weeks: int,
        risk_factors: List[str],
        risk_category: str,
        medications: List[str]
    ) -> str:
        """Generate a fallback message when model is not available"""
        
        if topic == "weekly_checkin":
            message = f"Hello {patient_name}, this is your week {gestational_age_weeks} pregnancy check-in. "
            if gestational_age_weeks < 12:
                message += "During your first trimester, it's important to take your prenatal vitamins and get plenty of rest."
            elif gestational_age_weeks < 28:
                message += "You're in your second trimester. Continue with regular prenatal care and maintain a healthy diet."
            else:
                message += "You're in your third trimester. Monitor for any signs of labor and stay in close contact with your healthcare provider."
        
        elif topic == "medication_reminder":
            if medications:
                med_list = ", ".join(medications)
                message = f"Hello {patient_name}, this is your reminder to take your medications: {med_list}. "
            else:
                message = f"Hello {patient_name}, this is your medication reminder. "
            message += "Please take your medications as prescribed by your healthcare provider."
        
        elif topic == "appointment_notification":
            message = f"Hello {patient_name}, this is a reminder about your upcoming prenatal appointment. "
            message += "Please arrive 15 minutes early and bring your insurance card and a list of any questions you have."
        
        elif topic == "high_risk_monitoring":
            message = f"Hello {patient_name}, this is your high-risk pregnancy monitoring call. "
            if risk_factors:
                message += f"Given your risk factors including {', '.join(risk_factors)}, "
            message += "it's important to monitor your symptoms closely and contact your healthcare provider immediately if you experience any concerns."
        
        else:
            message = f"Hello {patient_name}, this is a message from your pregnancy care team. "
            message += "Please stay in touch with your healthcare provider regarding your pregnancy care."
        
        if risk_category == "high":
            message += " Given your high-risk status, please be extra vigilant about any changes in your condition."
        
        return message
    
    def process_patient_message(self, transcript: str, patient_context: dict) -> str:
        """Process a patient's voice message and generate a response"""
        
        prompt = f"""A pregnant patient left the following voice message: "{transcript}"

Patient Context:
- Name: {patient_context.get('name', 'Patient')}
- Gestational Age: {patient_context.get('gestational_age_weeks', 'Unknown')} weeks
- Risk Category: {patient_context.get('risk_category', 'low')}
- Risk Factors: {', '.join(patient_context.get('risk_factors', []))}

Generate a compassionate, medically appropriate response that:
1. Acknowledges their concern
2. Provides helpful guidance
3. Recommends when to contact healthcare provider if needed
4. Is concise and clear for an IVR callback

Response:"""
        
        if self.model and self.tokenizer:
            try:
                response = self._generate_with_model(prompt)
            except Exception as e:
                print(f"⚠️ Model generation failed: {e}")
                response = self._generate_fallback_response(transcript, patient_context)
        else:
            response = self._generate_fallback_response(transcript, patient_context)
        
        return response
    
    def _generate_fallback_response(self, transcript: str, patient_context: dict) -> str:
        """Generate a fallback response when model is not available"""
        response = f"Thank you for your message, {patient_context.get('name', 'Patient')}. "
        response += "We have received your message and a member of our medical team will review it. "
        response += "If this is an emergency, please contact your healthcare provider immediately or go to the nearest emergency room. "
        response += "Otherwise, we will get back to you within 24 hours."
        return response

