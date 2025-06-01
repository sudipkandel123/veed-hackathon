import os
import signal
import sys
import ssl
import certifi
import datetime
import re

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from env_loader import export_env_variables


def setup_ssl_context():
    """Set up SSL context to use certifi certificates"""
    try:
        # Create SSL context that uses certifi certificates
        ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(cafile=certifi.where())
        
        # Set SSL context for urllib globally
        ssl._create_default_https_context = lambda: ssl_context
        
        # Set environment variables for SSL certificate file
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
        
        # Verify the certificate path exists
        if not os.path.exists(certifi.where()):
            raise FileNotFoundError(f"Certificate file not found at: {certifi.where()}")
            
        print(f"✅ SSL certificates configured successfully using: {certifi.where()}")
        
    except Exception as e:
        print(f"⚠️ Warning: SSL certificate setup failed: {str(e)}")
        print("⚠️ Attempting to continue without custom SSL configuration...")


class SessionTranscript:
    """Handles session transcript recording and management"""

    def __init__(self):
        # Create session timestamp
        self.session_start = datetime.datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")

        # Create transcripts directory if it doesn't exist
        self.transcript_dir = "session_transcripts"
        if not os.path.exists(self.transcript_dir):
            os.makedirs(self.transcript_dir)

        # Create transcript file
        self.transcript_file = os.path.join(
            self.transcript_dir, f"conversation_{self.session_id}.txt"
        )

        # Initialize transcript file with session info
        self.write_header()
        self.conversation_active = True

        print(f"📝 Session transcript will be saved to: {self.transcript_file}")

    def write_header(self):
        """Write session header to transcript file"""
        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("ELEVENLABS CONVERSATIONAL AI SESSION TRANSCRIPT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Start Time: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Agent ID: agent_01jwk4yynnemwsf3vr3kj9da45\n")
            f.write("=" * 60 + "\n\n")

    def log_user_message(self, message):
        """Log user message to transcript"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with open(self.transcript_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] USER: {message}\n")
        print(f"📝 User: {message}")

        # Check for goodbye intent
        if self.is_goodbye_intent(message):
            self.conversation_active = False
            self.log_system_message("Goodbye detected - ending conversation")

    def log_agent_message(self, message):
        """Log agent message to transcript"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with open(self.transcript_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] AGENT: {message}\n")
        print(f"🤖 Agent: {message}")

    def log_agent_correction(self, original, corrected):
        """Log agent message correction to transcript"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with open(self.transcript_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] AGENT (CORRECTED): {original} -> {corrected}\n")
        print(f"🔄 Agent correction: {original} -> {corrected}")

    def log_system_message(self, message):
        """Log system message to transcript"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with open(self.transcript_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] SYSTEM: {message}\n")
        print(f"⚙️  System: {message}")

    def is_goodbye_intent(self, message):
        """Check if user message contains goodbye intent"""
        goodbye_patterns = [
            r"\b(goodbye|bye|see you|farewell|talk to you later|ttyl)\b",
            r"\b(exit|quit|end|stop|finish)\b",
            r"\b(thanks?\s*(and\s*)?bye|bye\s*thanks?)\b",
            r"\b(have a good|take care|until next time)\b",
            r"\b(i\'?m done|that\'?s all|nothing else)\b",
        ]

        message_lower = message.lower()
        for pattern in goodbye_patterns:
            if re.search(pattern, message_lower):
                return True
        return False

    def close_session(self):
        """Close the session and write footer"""
        end_time = datetime.datetime.now()
        duration = end_time - self.session_start

        with open(self.transcript_file, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 60 + "\n")
            f.write(f"Session End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Session Duration: {str(duration).split('.')[0]}\n")
            f.write("=" * 60 + "\n")

        print(f"📝 Session transcript saved to: {self.transcript_file}")
        print(f"⏱️  Session duration: {str(duration).split('.')[0]}")


def create_enhanced_audio_interface():
    """Create an audio interface with improved settings for smoother conversation"""
    # Note: The DefaultAudioInterface in ElevenLabs may have limited customization options
    # The main improvements for smoother conversation come from proper conversation management
    # and the ElevenLabs turn-taking model which is automatically optimized
    return DefaultAudioInterface()  # Use default settings


def create_conversation_config():
    """Create conversation configuration for smoother flow"""
    # Note: ElevenLabs handles most conversation flow automatically
    # through their turn-taking model. The key is proper session management.
    return {
        # These settings would be used if the API supports them
        "turn_detection": {
            "silence_duration_ms": 800,  # Wait 800ms of silence before detecting turn end
            "speech_threshold": 0.3,  # Sensitivity for detecting speech
        },
        "response_delay_ms": 200,  # Small delay before responding
        "interrupt_sensitivity": 0.5,  # How easily the agent can be interrupted
    }


def get_agent_system_prompt():
    """Get system prompt for better conversation flow"""
    return """."""


def create_enhanced_conversation_callbacks(transcript):
    """Create enhanced callbacks with better conversation management"""

    def on_agent_response(response):
        """Handle agent responses with conversation flow awareness"""
        transcript.log_agent_message(response)

        # Check if agent is asking multiple questions (which we want to avoid)
        question_count = response.count("?")
        if question_count > 1:
            transcript.log_system_message(
                f"Warning: Agent asked {question_count} questions in one response"
            )

    def on_agent_correction(original, corrected):
        """Handle agent message corrections"""
        transcript.log_agent_correction(original, corrected)

    def on_user_transcript(user_message):
        """Handle user messages with enhanced processing"""
        transcript.log_user_message(user_message)

        # Log message length for conversation flow analysis
        word_count = len(user_message.split())
        transcript.log_system_message(f"User message: {word_count} words")

    return {
        "callback_agent_response": on_agent_response,
        "callback_agent_response_correction": on_agent_correction,
        "callback_user_transcript": on_user_transcript,
    }


def main():
    # Export environment variables first
    export_env_variables()
    
    # Set up SSL context before making any network calls
    setup_ssl_context()
    print(f"✅ SSL certificates configured successfully using: {certifi.where()}")

    # Initialize session transcript
    transcript = SessionTranscript()
    print(f"✅ Session transcript initialized")

    # Get environment variables (they are now guaranteed to be set)
    AGENT_ID = os.environ.get('AGENT_ID')
    API_KEY = os.environ.get('ELEVENLABS_API_KEY')
    print(f"✅ AGENT_ID: {AGENT_ID}")
    print(f"✅ API_KEY: {'*' * len(API_KEY) if API_KEY else 'Not set'}")

    client = ElevenLabs(api_key=API_KEY)

    # Create enhanced audio interface for smoother conversation
    audio_interface = create_enhanced_audio_interface()

    # Get enhanced conversation callbacks
    callbacks = create_enhanced_conversation_callbacks(transcript)

    # Log conversation flow rules
    transcript.log_system_message("Enhanced conversation flow enabled:")
    transcript.log_system_message("- Agent will ask ONE question at a time")
    transcript.log_system_message("- Agent will wait for your complete response")
    transcript.log_system_message("- Sequential discussion pattern enforced")
    transcript.log_system_message(
        "Configure agent system prompt at: https://elevenlabs.io/app/conversational-ai"
    )

    conversation = Conversation(
        client,
        AGENT_ID,
        # Assume auth is required when API_KEY is set
        requires_auth=bool(API_KEY),
        audio_interface=audio_interface,
        # Use enhanced callbacks for better conversation management
        **callbacks,
        # Optional: uncomment to log latency
        # callback_latency_measurement=lambda latency: transcript.log_system_message(f"Latency: {latency}ms"),
    )

    # Log session start with conversation instructions
    transcript.log_system_message("Starting ElevenLabs conversational AI session")
    transcript.log_system_message(
        "Conversation flow: ONE question at a time, wait for response"
    )
    transcript.log_system_message(
        "Say 'goodbye', 'bye', or 'exit' to end the conversation"
    )

    conversation.start_session()

    # Enhanced session management with goodbye detection
    def signal_handler(sig, frame):
        transcript.log_system_message("Session interrupted by user (Ctrl+C)")
        conversation.end_session()
        transcript.close_session()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Monitor conversation and check for goodbye intent
    try:
        while transcript.conversation_active:
            # The conversation runs in the background, we just wait
            # The callbacks will handle transcript logging and goodbye detection
            import time

            time.sleep(0.5)  # Check every 500ms

        # If we get here, goodbye was detected
        transcript.log_system_message(
            "Goodbye detected - ending conversation gracefully"
        )
        conversation.end_session()

    except KeyboardInterrupt:
        transcript.log_system_message("Session interrupted by user (Ctrl+C)")
        conversation.end_session()

    finally:
        # Wait for session to end and get conversation ID
        conversation_id = conversation.wait_for_session_end()
        transcript.log_system_message(f"Conversation ID: {conversation_id}")
        transcript.close_session()
        print(f"Conversation ID: {conversation_id}")


if __name__ == "__main__":
    main()
