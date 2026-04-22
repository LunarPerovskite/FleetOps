"""Multi-language Translation Service for FleetOps

Features:
- Auto-detect customer language
- Translate agent responses
- Multi-language support for customer service
- Maintain context across translations
"""

from typing import Optional, Dict, List
import openai
from app.core.config import settings

class TranslationService:
    """Translation and language detection"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.detect_model = os.getenv("TRANSLATION_DETECT_MODEL", "gpt-4o-mini")
        self.translate_model = os.getenv("TRANSLATION_MODEL", "gpt-4o-mini")
    
    async def detect_language(self, text: str) -> Dict:
        """Detect language of text"""
        try:
            response = self.client.chat.completions.create(
                model=self.detect_model,
                messages=[
                    {"role": "system", "content": "Detect language. Return JSON with: language_code, language_name, confidence (0-1)"},
                    {"role": "user", "content": text[:500]}  # Use first 500 chars
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "language_code": result.get("language_code", "en"),
                "language_name": result.get("language_name", "English"),
                "confidence": result.get("confidence", 0.5),
                "supported": result.get("language_code", "en") in self.SUPPORTED_LANGUAGES
            }
        except Exception as e:
            return {"language_code": "en", "language_name": "English", "confidence": 0, "error": str(e)}
    
    async def translate(self, text: str, target_language: str, 
                       source_language: Optional[str] = None) -> Dict:
        """Translate text to target language"""
        if target_language not in self.SUPPORTED_LANGUAGES:
            return {"error": f"Unsupported target language: {target_language}"}
        
        try:
            prompt = f"Translate to {self.SUPPORTED_LANGUAGES[target_language]}."
            if source_language:
                prompt += f" Source language: {self.SUPPORTED_LANGUAGES.get(source_language, source_language)}."
            
            response = self.client.chat.completions.create(
                model=self.translate_model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ]
            )
            
            return {
                "original_text": text,
                "translated_text": response.choices[0].message.content,
                "target_language": target_language,
                "target_language_name": self.SUPPORTED_LANGUAGES[target_language],
                "source_language": source_language or "auto",
                "status": "success"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def translate_agent_response(self, response: str, 
                                       customer_language: str) -> Dict:
        """Translate agent response to customer language"""
        if customer_language == "en":
            return {
                "translated": response,
                "original": response,
                "language": "en",
                "translated": False
            }
        
        result = await self.translate(response, customer_language)
        return {
            "translated": result.get("translated_text", response),
            "original": response,
            "language": customer_language,
            "translated": True
        }
