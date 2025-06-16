import pyttsx3
from typing import Optional, Tuple
import time
import logging
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import os
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        """Initialize the voice service with Vosk speech recognition and text-to-speech engines."""
        self.engine = pyttsx3.init()
        
        # Configure text-to-speech engine
        self.engine.setProperty('rate', 150)    # Speed of speech
        self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
        
        # Get available voices and set a default
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id)
        
        # Initialize Vosk model
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'vosk-model-small-en-us-0.15')
        if not os.path.exists(model_path):
            raise RuntimeError(
                "Please download the Vosk model from https://alphacephei.com/vosk/models "
                "and extract it to the 'models' directory as 'vosk-model-small-en-us-0.15'"
            )
        self.model = Model(model_path)
        
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.audio_queue = queue.Queue()

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        self.audio_queue.put(bytes(indata))

    def listen_for_command(self, timeout: int = 5, phrase_time_limit: int = 10) -> Tuple[Optional[str], bool]:
        """
        Listen for voice command and convert to text.
        
        Args:
            timeout (int): Time to wait for the start of a phrase
            phrase_time_limit (int): Maximum time for a phrase
            
        Returns:
            Tuple[Optional[str], bool]: (transcribed text, success status)
        """
        try:
            # Initialize recognizer
            rec = KaldiRecognizer(self.model, self.sample_rate)
            rec.SetWords(True)
            
            # Start audio stream
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,
                dtype='int16',
                channels=self.channels,
                callback=self._audio_callback
            ):
                logger.info("Listening for command...")
                self.speak("Listening for your command")
                
                start_time = time.time()
                text = ""
                silence_frames = 0
                max_silence_frames = int(phrase_time_limit * self.sample_rate / 8000)
                
                while (time.time() - start_time) < timeout:
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        if rec.AcceptWaveform(data):
                            result = json.loads(rec.Result())
                            if result.get("text", "").strip():
                                text = result["text"]
                                break
                        else:
                            partial = json.loads(rec.PartialResult())
                            if partial.get("partial", "").strip():
                                silence_frames = 0
                            else:
                                silence_frames += 1
                                if silence_frames > max_silence_frames:
                                    break
                    except queue.Empty:
                        continue
                
                # Get final result
                if not text:
                    final = json.loads(rec.FinalResult())
                    text = final.get("text", "").strip()
                
                if text:
                    logger.info(f"Recognized: {text}")
                    return text, True
                else:
                    logger.warning("No speech detected")
                    self.speak("No speech detected. Please try again.")
                    return None, False
                
        except Exception as e:
            logger.error(f"Error in voice recognition: {str(e)}")
            self.speak("An error occurred while processing your voice command.")
            return None, False

    def speak(self, text: str) -> None:
        """
        Convert text to speech.
        
        Args:
            text (str): Text to be spoken
        """
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            # Fallback to print if speech fails
            print(f"Speech output: {text}")

    def process_voice_query(self) -> Optional[str]:
        """
        Process a complete voice query interaction.
        
        Returns:
            Optional[str]: The processed query text or None if failed
        """
        # Listen for the query
        query, success = self.listen_for_command()
        
        if not success or not query:
            return None
            
        # Confirm the query
        self.speak(f"I heard: {query}. Is this correct?")
        
        # Listen for confirmation
        confirmation, success = self.listen_for_command(timeout=3, phrase_time_limit=5)
        
        if not success or not confirmation:
            return None
            
        # Check for confirmation keywords
        if any(word in confirmation.lower() for word in ['yes', 'correct', 'right', 'yeah', 'yep']):
            return query
        else:
            self.speak("Let's try that again.")
            return self.process_voice_query()

# Create a singleton instance
voice_service_instance = None

def get_voice_service() -> VoiceService:
    """Get or create the voice service instance."""
    global voice_service_instance
    if voice_service_instance is None:
        voice_service_instance = VoiceService()
    return voice_service_instance 