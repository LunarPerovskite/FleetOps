"""Voice-to-Text Service using OpenAI Whisper

Handles phone calls, voice messages, and audio files.
"""

import os
import json
import tempfile
from typing import Optional, BinaryIO
import openai
from app.core.config import settings

class VoiceService:
    """Voice transcription and analysis"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")
        self.analysis_model = os.getenv("VOICE_ANALYSIS_MODEL", "gpt-4o-mini")
    
    async def transcribe(self, audio_file: BinaryIO, 
                        language: Optional[str] = None) -> dict:
        """Transcribe audio to text using Whisper"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(audio_file.read())
                tmp_path = tmp.name
            
            with open(tmp_path, "rb") as audio:
                transcript = self.client.audio.transcriptions.create(
                    model=self.whisper_model,
                    file=audio,
                    language=language
                )
            
            os.unlink(tmp_path)
            
            return {
                "text": transcript.text,
                "language": transcript.language if hasattr(transcript, 'language') else None,
                "status": "success"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment of transcribed text"""
        try:
            response = self.client.chat.completions.create(
                model=self.analysis_model,
                messages=[
                    {"role": "system", "content": "Analyze sentiment. Return JSON with: sentiment (positive/neutral/negative), urgency (1-10), needs_escalation (boolean), key_phrases (list), category (billing/support/sales/technical/other)"},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def process_voice_message(self, audio_file: BinaryIO, 
                                    call_id: str = None) -> dict:
        """Full voice processing pipeline"""
        # Transcribe
        transcript = await self.transcribe(audio_file)
        
        if transcript.get("status") == "error":
            return transcript
        
        # Analyze
        analysis = await self.analyze_sentiment(transcript["text"])
        
        return {
            "call_id": call_id,
            "transcript": transcript["text"],
            "analysis": analysis,
            "needs_escalation": analysis.get("needs_escalation", False),
            "urgency": analysis.get("urgency", 5),
            "status": "completed"
        }
