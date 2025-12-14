"""
Audio service for ASR (Speech-to-Text) and TTS (Text-to-Speech).
Supports OpenAI APIs, Google Cloud Speech/TTS, with fallback to mock for development.
"""

import logging
import os
from typing import Any

import httpx
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioService:
    """Service for audio transcription and synthesis."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.audio_provider = getattr(settings, "audio_provider", "openai").lower()
        self.google_project_id = getattr(settings, "google_cloud_project_id", None)
        self.google_credentials_path = getattr(settings, "google_application_credentials", None)
        self.google_credentials_json = getattr(settings, "google_credentials_json", None)
        self.logger = logger
        self._temp_credentials_file = None  # Track temp file for cleanup
        
        # Initialize Google clients if credentials are available
        self._google_speech_client = None
        self._google_tts_client = None
        if self.audio_provider == "google" and self._init_google_clients():
            self.logger.info("Google Cloud Speech and TTS clients initialized")
        elif self.audio_provider == "google":
            self.logger.warning("Google Cloud credentials not found, falling back to mock")
    
    def _init_google_clients(self) -> bool:
        """Initialize Google Cloud Speech and TTS clients."""
        try:
            credentials_path = None
            
            # Priority 1: Use JSON string from environment variable
            if self.google_credentials_json:
                try:
                    import json
                    import tempfile
                    
                    # Parse JSON to validate it
                    credentials_data = json.loads(self.google_credentials_json)
                    
                    # Create temporary file with credentials
                    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                    json.dump(credentials_data, temp_file)
                    temp_file.close()
                    
                    credentials_path = temp_file.name
                    self._temp_credentials_file = credentials_path
                    self.logger.info("Using Google credentials from GOOGLE_CREDENTIALS_JSON environment variable")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
                    return False
                except Exception as e:
                    self.logger.error(f"Error creating temp credentials file: {e}")
                    return False
            
            # Priority 2: Use file path (legacy support)
            elif self.google_credentials_path and os.path.exists(self.google_credentials_path):
                credentials_path = self.google_credentials_path
                self.logger.info(f"Using Google credentials from file: {credentials_path}")
            
            # Set credentials environment variable
            if credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            
            # Only import if we have project ID
            if not self.google_project_id:
                self.logger.warning("Google Cloud project ID not configured")
                return False
            
            # Lazy import to avoid errors if package not installed
            try:
                from google.cloud import speech, texttospeech
                
                self._google_speech_client = speech.SpeechClient()
                self._google_tts_client = texttospeech.TextToSpeechClient()
                return True
            except ImportError:
                self.logger.warning("google-cloud-speech or google-cloud-texttospeech not installed")
                return False
        except Exception as e:
            self.logger.error(f"Error initializing Google clients: {e}", exc_info=True)
            return False
    
    def __del__(self):
        """Clean up temporary credentials file if created."""
        if self._temp_credentials_file and os.path.exists(self._temp_credentials_file):
            try:
                os.unlink(self._temp_credentials_file)
            except Exception:
                pass  # Ignore cleanup errors

    async def transcribe_audio(self, audio_url: str) -> str:
        """
        Transcribe audio from URL to text (ASR).

        Args:
            audio_url: URL of the audio file

        Returns:
            Transcribed text

        Raises:
            Exception: If transcription fails
        """
        # Try Google Cloud first if configured
        if self.audio_provider == "google" and self._google_speech_client:
            try:
                return await self._transcribe_with_google(audio_url)
            except Exception as e:
                self.logger.error(f"Error with Google transcription: {e}", exc_info=True)
                # Fallback to OpenAI or mock
        
        # Try OpenAI if configured
        if self.audio_provider == "openai" and self.openai_client:
            try:
                return await self._transcribe_with_openai(audio_url)
            except Exception as e:
                self.logger.error(f"Error with OpenAI transcription: {e}", exc_info=True)
        
        # Fallback to mock
        self.logger.warning("No audio provider configured, using mock transcription")
        return await self._mock_transcribe(audio_url)
    
    async def _transcribe_with_openai(self, audio_url: str) -> str:
        """Transcribe using OpenAI Whisper API."""
        # Download audio file - try to get presigned URL if it's an R2/S3 URL
        download_url = await self._get_download_url(audio_url)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url, timeout=30.0)
            response.raise_for_status()
            audio_data = response.content

        # Use OpenAI Whisper API
        import asyncio
        from io import BytesIO

        def _transcribe_sync() -> str:
            audio_file = BytesIO(audio_data)
            audio_file.name = "audio.webm"
            transcript = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",
            )
            return transcript.text

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _transcribe_sync)
    
    async def _transcribe_with_google(self, audio_url: str) -> str:
        """Transcribe using Google Cloud Speech-to-Text API."""
        # Download audio file - try to get presigned URL if it's an R2/S3 URL
        download_url = await self._get_download_url(audio_url)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url, timeout=30.0)
            response.raise_for_status()
            audio_data = response.content

        import asyncio
        from google.cloud import speech

        def _transcribe_sync() -> str:
            # Use the initialized client
            client = self._google_speech_client
            
            # Configure recognition
            # Try different encodings - WebM Opus might need different config
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,  # Auto-detect
                sample_rate_hertz=48000,
                language_code="pt-BR",
                alternative_language_codes=["pt-PT"],  # Fallback
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            response = client.recognize(config=config, audio=audio)
            
            # Extract transcript
            if response.results:
                return response.results[0].alternatives[0].transcript
            return ""

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _transcribe_sync)

    async def synthesize_speech(self, text: str, locale: str = "pt-BR") -> bytes:
        """
        Synthesize text to speech (TTS).

        Args:
            text: Text to synthesize
            locale: Locale for voice (default: pt-BR)

        Returns:
            Audio data as bytes

        Raises:
            Exception: If synthesis fails
        """
        # Try Google Cloud first if configured
        if self.audio_provider == "google" and self._google_tts_client:
            try:
                return await self._synthesize_with_google(text, locale)
            except Exception as e:
                self.logger.error(f"Error with Google TTS: {e}", exc_info=True)
                # Fallback to OpenAI or mock
        
        # Try OpenAI if configured
        if self.audio_provider == "openai" and self.openai_client:
            try:
                return await self._synthesize_with_openai(text)
            except Exception as e:
                self.logger.error(f"Error with OpenAI TTS: {e}", exc_info=True)
        
        # Fallback to mock
        self.logger.warning("No audio provider configured, using mock TTS")
        return await self._mock_synthesize(text)
    
    async def _synthesize_with_openai(self, text: str) -> bytes:
        """Synthesize using OpenAI TTS API."""
        import asyncio

        def _synthesize_sync() -> bytes:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text,
            )
            return response.content

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _synthesize_sync)
    
    async def _synthesize_with_google(self, text: str, locale: str = "pt-BR") -> bytes:
        """Synthesize using Google Cloud Text-to-Speech API."""
        import asyncio
        from google.cloud import texttospeech

        def _synthesize_sync() -> bytes:
            # Use the initialized client
            client = self._google_tts_client
            
            # Configure synthesis
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Select voice (pt-BR female voice - "pt-BR-Wavenet-A" or "pt-BR-Neural2-A")
            voice = texttospeech.VoiceSelectionParams(
                language_code=locale,
                name="pt-BR-Neural2-A",  # High-quality Brazilian Portuguese voice
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
            )
            
            # Audio config
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
            
            return response.audio_content

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _synthesize_sync)

    async def _mock_transcribe(self, audio_url: str) -> str:
        """
        Mock transcription for development.

        Args:
            audio_url: URL of the audio file (ignored in mock)

        Returns:
            Mock transcribed text
        """
        # In development, return a placeholder
        # In production, this should never be called if OpenAI is configured
        self.logger.info(f"Mock transcription for {audio_url}")
        return "Esta é uma transcrição de exemplo. Em produção, configure a chave da API OpenAI."

    async def _get_download_url(self, audio_url: str) -> str:
        """
        Get download URL for audio file.
        If it's an R2/S3 URL that needs authentication, generate a presigned URL.
        
        Args:
            audio_url: Original audio URL
            
        Returns:
            Download URL (presigned if needed)
        """
        try:
            # Check if it's an R2/S3 URL that might need presigned access
            from urllib.parse import urlparse
            
            parsed = urlparse(audio_url)
            
            # If it's an R2 URL (contains .r2.cloudflarestorage.com) or S3 URL
            if '.r2.cloudflarestorage.com' in parsed.netloc or 's3.amazonaws.com' in parsed.netloc or 's3.' in parsed.netloc:
                # Try to extract file key from URL
                # URL format: https://bucket.account.r2.cloudflarestorage.com/user_id/filename
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    # Reconstruct file key (user_id/filename)
                    file_key = '/'.join(path_parts)
                    
                    # Get storage provider and generate presigned download URL
                    from app.modules.documents.storage import get_storage_provider
                    storage = get_storage_provider()
                    
                    # If it's S3StorageProvider, use get_file_url which generates presigned URLs
                    if hasattr(storage, 'client') and hasattr(storage, 'bucket_name'):
                        # It's S3StorageProvider - generate presigned URL for download
                        presigned_url = storage.client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': storage.bucket_name, 'Key': file_key},
                            ExpiresIn=3600,  # 1 hour
                        )
                        self.logger.info(f"Generated presigned download URL for R2/S3 file")
                        return presigned_url
        except Exception as e:
            self.logger.warning(f"Could not generate presigned URL, using original: {e}")
        
        # Fallback to original URL
        return audio_url

    async def _mock_synthesize(self, text: str) -> bytes:
        """
        Mock TTS for development.

        Args:
            text: Text to synthesize (ignored in mock)

        Returns:
            Mock audio data (empty bytes)
        """
        # In development, return empty audio
        # In production, this should never be called if OpenAI is configured
        self.logger.info(f"Mock TTS for text: {text[:50]}...")
        # Return empty audio file (frontend will fallback to text-to-speech)
        return b""
