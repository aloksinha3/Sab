import json
import os
from typing import List, Dict, Optional

# Try to import sentence transformers, but make it optional
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    np = None

class RAGSystem:
    def __init__(self, database_path: str = "pregnancy_rag_database.json"):
        self.database_path = database_path
        self.knowledge_base = self._load_knowledge_base()
        self.encoder = None
        self._initialize_encoder()
    
    def _load_knowledge_base(self) -> List[Dict]:
        """Load the pregnancy care knowledge base"""
        if os.path.exists(self.database_path):
            with open(self.database_path, 'r') as f:
                return json.load(f)
        else:
            # Default knowledge base
            return self._create_default_knowledge_base()
    
    def _create_default_knowledge_base(self) -> List[Dict]:
        """Create a default knowledge base if file doesn't exist"""
        return [
            {
                "topic": "first_trimester",
                "content": "During the first trimester (weeks 1-12), focus on taking prenatal vitamins, especially folic acid, and managing morning sickness. Avoid alcohol, smoking, and certain medications. Schedule your first prenatal appointment.",
                "keywords": ["first trimester", "prenatal vitamins", "folic acid", "morning sickness"]
            },
            {
                "topic": "second_trimester",
                "content": "The second trimester (weeks 13-27) is often the most comfortable period. Continue prenatal care, maintain a balanced diet, and stay active with doctor-approved exercise. You may start feeling your baby move.",
                "keywords": ["second trimester", "prenatal care", "diet", "exercise", "baby movement"]
            },
            {
                "topic": "third_trimester",
                "content": "In the third trimester (weeks 28-40), monitor for signs of labor, continue regular prenatal visits, and prepare for delivery. Watch for symptoms like severe headaches, vision changes, or decreased fetal movement.",
                "keywords": ["third trimester", "labor", "delivery", "prenatal visits", "fetal movement"]
            },
            {
                "topic": "high_risk_pregnancy",
                "content": "High-risk pregnancies require close monitoring. Factors include advanced maternal age, diabetes, hypertension, multiple pregnancies, or previous pregnancy complications. Follow your healthcare provider's recommendations closely.",
                "keywords": ["high risk", "diabetes", "hypertension", "monitoring", "complications"]
            },
            {
                "topic": "medications",
                "content": "Always consult your healthcare provider before taking any medications during pregnancy. Some medications are safe, while others can harm the developing baby. Never stop taking prescribed medications without medical supervision.",
                "keywords": ["medications", "prescription", "safe medications", "consult doctor"]
            },
            {
                "topic": "nutrition",
                "content": "A balanced diet during pregnancy should include fruits, vegetables, whole grains, lean proteins, and dairy. Avoid raw fish, unpasteurized dairy, and excessive caffeine. Stay hydrated and take prenatal vitamins.",
                "keywords": ["nutrition", "diet", "prenatal vitamins", "hydration", "food safety"]
            },
            {
                "topic": "exercise",
                "content": "Regular exercise during pregnancy is beneficial but should be approved by your healthcare provider. Low-impact activities like walking, swimming, and prenatal yoga are generally safe. Avoid contact sports and activities with a high risk of falling.",
                "keywords": ["exercise", "walking", "swimming", "yoga", "physical activity"]
            },
            {
                "topic": "warning_signs",
                "content": "Seek immediate medical attention for: severe abdominal pain, vaginal bleeding, severe headaches, vision changes, decreased fetal movement, persistent nausea/vomiting, or signs of preterm labor.",
                "keywords": ["warning signs", "emergency", "abdominal pain", "bleeding", "headaches"]
            }
        ]
    
    def _initialize_encoder(self):
        """Initialize the sentence transformer for semantic search"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("⚠️ Sentence transformers not installed. Using keyword-based search.")
            print("⚠️ Install AI dependencies with: pip install -r requirements-ai.txt")
            self.encoder = None
            return
        
        try:
            print("Loading sentence transformer model...")
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Encoder loaded successfully")
        except Exception as e:
            print(f"⚠️ Could not load encoder: {e}")
            self.encoder = None
    
    def retrieve_relevant_content(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant content from the knowledge base using semantic search"""
        
        if not self.encoder:
            # Fallback to keyword matching
            return self._keyword_search(query, top_k)
        
        # Encode query
        query_embedding = self.encoder.encode(query, convert_to_tensor=True)
        
        # Encode all knowledge base entries
        contents = [item.get("content", "") + " " + " ".join(item.get("keywords", [])) 
                   for item in self.knowledge_base]
        content_embeddings = self.encoder.encode(contents, convert_to_tensor=True)
        
        # Calculate similarities
        if np is None:
            return self._keyword_search(query, top_k)
        
        similarities = np.dot(content_embeddings, query_embedding.T).flatten()
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "topic": self.knowledge_base[idx].get("topic"),
                "content": self.knowledge_base[idx].get("content"),
                "relevance_score": float(similarities[idx])
            })
        
        return results
    
    def _keyword_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Fallback keyword-based search"""
        query_lower = query.lower()
        scored_items = []
        
        for item in self.knowledge_base:
            score = 0
            content = item.get("content", "").lower()
            keywords = [kw.lower() for kw in item.get("keywords", [])]
            
            # Check keyword matches
            for keyword in keywords:
                if keyword in query_lower:
                    score += 2
                if keyword in content:
                    score += 1
            
            # Check content matches
            words = query_lower.split()
            for word in words:
                if word in content:
                    score += 0.5
            
            if score > 0:
                scored_items.append((score, item))
        
        # Sort by score and return top k
        scored_items.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, item in scored_items[:top_k]:
            results.append({
                "topic": item.get("topic"),
                "content": item.get("content"),
                "relevance_score": score
            })
        
        return results
    
    def generate_contextual_response(self, query: str, patient_context: Dict = None) -> str:
        """Generate a contextual response using RAG"""
        
        # Retrieve relevant content
        relevant_content = self.retrieve_relevant_content(query, top_k=2)
        
        # Build context
        context = "\n".join([item["content"] for item in relevant_content])
        
        # Build response
        response = f"Based on medical guidelines: {context}\n\n"
        
        if patient_context:
            response += f"For {patient_context.get('name', 'you')} at {patient_context.get('gestational_age_weeks', 'your current')} weeks of pregnancy, "
        
        response += "please consult with your healthcare provider for personalized medical advice specific to your situation."
        
        return response
    
    def save_knowledge_base(self):
        """Save the knowledge base to file"""
        with open(self.database_path, 'w') as f:
            json.dump(self.knowledge_base, f, indent=2)
    
    def add_knowledge(self, topic: str, content: str, keywords: List[str] = None):
        """Add new knowledge to the database"""
        self.knowledge_base.append({
            "topic": topic,
            "content": content,
            "keywords": keywords or []
        })
        self.save_knowledge_base()

