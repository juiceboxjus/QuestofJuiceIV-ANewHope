"""
Music Manager for Quest of Juice IV
Handles background music with mood-based track switching.
Runs in a separate thread to avoid blocking the game loop.
"""
import os
import json
import threading
import time
import random
from typing import Optional

# Try importing pygame for audio
try:
    import pygame.mixer as mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not installed. Music disabled.")
    print("Install with: pip install pygame")


class MusicManager:
    """Manages background music with mood-based switching."""
    
    def __init__(self, music_dir: str = "music", volume: float = 0.5):
        """Initialize the music manager.
        
        Args:
            music_dir: Directory containing music files and moods.json
            volume: Volume level from 0.0 to 1.0
        """
        self.music_dir: str = music_dir
        self.volume: float = volume
        self.enabled: bool = PYGAME_AVAILABLE
        self.current_mood: str = ""
        self.target_mood: str = ""
        self.fading: bool = False
        self.fade_start: float = 0.0
        self.fade_duration: float = 1.0
        self.thread: Optional[threading.Thread] = None
        self.running: bool = False
        self.lock: threading.Lock = threading.Lock()
        
        # Load mood configuration
        self.moods: dict = {}
        self.tracks: dict = {}
        self._load_moods()
        
        # Initialize mixer if available
        if self.enabled:
            try:
                mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                mixer.set_num_channels(8)
            except Exception as e:
                print(f"Warning: Could not initialize audio mixer: {e}")
                self.enabled = False
    
    def _load_moods(self) -> None:
        """Load mood configuration from JSON file."""
        moods_path: str = os.path.join(self.music_dir, "moods.json")
        try:
            with open(moods_path, 'r', encoding='utf-8') as f:
                self.moods = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Warning: Could not load {moods_path}. Using empty mood map.")
            self.moods = {}
        
        # Scan for available audio files
        self.tracks = {}
        if os.path.isdir(self.music_dir):
            for filename in os.listdir(self.music_dir):
                if filename.endswith(('.wav', '.ogg', '.mp3')):
                    mood_name: str = filename.rsplit('.', 1)[0]
                    self.tracks[mood_name] = os.path.join(self.music_dir, filename)
    
    def _get_track_for_mood(self, mood: str) -> Optional[str]:
        """Get a track file path for a given mood.
        
        Args:
            mood: The mood name to find a track for
        
        Returns:
            Path to audio file or None if not found
        """
        if not self.tracks:
            return None
        
        # Direct match
        if mood in self.tracks:
            return self.tracks[mood]
        
        # Try with _1, _2 suffixes for variation
        variations: list = [k for k in self.tracks if k.startswith(mood)]
        if variations:
            return self.tracks[random.choice(variations)]
        
        return None
    
    def _music_loop(self) -> None:
        """Main music playback loop. Runs in a separate thread."""
        current_track: Optional[str] = None
        current_channel: Optional[any] = None
        
        while self.running:
            with self.lock:
                target: str = self.target_mood
                fading: bool = self.fading
            
            # Determine which mood to play
            play_mood: str = target if target else "calm_explore"
            
            # Get track for this mood
            track_path: Optional[str] = self._get_track_for_play_mood(play_mood)
            
            if track_path and track_path != current_track:
                # Load and play new track
                try:
                    if current_channel:
                        current_channel.fadeout(500)
                    
                    sound = mixer.Sound(track_path)
                    sound.set_volume(self.volume)
                    current_channel = sound.play(loops=-1, fade_ms=800)
                    current_track = track_path
                except Exception as e:
                    print(f"Warning: Could not play {track_path}: {e}")
                    current_track = None
            
            elif not track_path and current_channel:
                # No track available, stop current
                current_channel.fadeout(500)
                current_channel = None
                current_track = None
            
            # Adjust volume if enabled setting changed
            if current_channel:
                current_channel.set_volume(self.volume if self.enabled else 0.0)
            
            time.sleep(0.5)  # Check for mood changes every half second
    
    def start(self) -> None:
        """Start the music manager thread."""
        if not self.enabled:
            return
        
        if self.thread and self.thread.is_alive():
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._music_loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the music manager thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        
        if self.enabled:
            try:
                mixer.stop()
                mixer.quit()
            except Exception:
                pass
    
    def set_mood(self, mood: str) -> None:
        """Change the current music mood.
        
        Args:
            mood: The mood to switch to (calm_explore, tense_explore, combat, etc.)
        """
        with self.lock:
            self.target_mood = mood
    
    def set_room_mood(self, room_name: str) -> None:
        """Set mood based on room name using the mood map.
        
        Args:
            room_name: Name of the current room
        """
        mood: str = self.moods.get(room_name, "calm_explore")
        self.set_mood(mood)
    
    def set_combat(self, is_boss: bool = False) -> None:
        """Switch to combat music.
        
        Args:
            is_boss: If True, play boss combat music
        """
        mood: str = "combat_boss" if is_boss else "combat_normal"
        self.set_mood(mood)
    
    def toggle(self) -> bool:
        """Toggle music on/off. Returns new state."""
        self.enabled = not self.enabled
        return self.enabled
    
    def set_volume(self, volume: float) -> None:
        """Set music volume.
        
        Args:
            volume: Volume level from 0.0 to 1.0
        """
        self.volume = max(0.0, min(1.0, volume))
    
    def get_mood_for_room(self, room_name: str) -> str:
        """Get the mood associated with a room.
        
        Args:
            room_name: Name of the room
        
        Returns:
            Mood name string
        """
        return self.moods.get(room_name, "calm_explore")