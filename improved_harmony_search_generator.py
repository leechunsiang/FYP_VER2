import music21 as m21
import random
from typing import List, Dict, Union, Optional

class ImprovedHarmonySearch(HarmonySearchMusic):
    """Enhanced version of HarmonySearchMusic with improved musical output"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Additional rhythm patterns
        self.rhythm_patterns = {
            "basic": [1.0, 1.0, 1.0, 1.0],  # Quarter notes
            "waltz": [1.0, 0.5, 0.5, 1.0, 1.0],  # Basic waltz pattern
            "syncopated": [0.5, 0.25, 0.75, 0.5, 1.0, 1.0],  # Syncopated pattern
            "offbeat": [0.5, 1.0, 0.5, 1.0, 1.0],  # Emphasizing off-beats
            "dotted": [1.5, 0.5, 1.0, 1.0],  # Dotted rhythm
        }
        
    def create_music_stream(self, harmony: Dict) -> m21.stream.Score:
        """Create a music stream with more interesting rhythm patterns"""
        melody = harmony['melody']
        chord_progression = harmony['chord_progression']
        
        # Create a new score
        score = m21.stream.Score()
        
        # Add metadata
        score.insert(0, m21.metadata.Metadata())
        score.metadata.title = f"Harmony Search Composition in {self.key} {self.mode}"
        score.metadata.composer = "AI Composer (Harmony Search)"
        
        # Create parts
        melody_part = m21.stream.Part(id='Melody')
        chord_part = m21.stream.Part(id='Harmony')
        bass_part = m21.stream.Part(id='Bass')
        
        # Add time signature, key signature and tempo - CREATE SEPARATE INSTANCES
        melody_part.insert(0, m21.meter.TimeSignature(f'{self.beats_per_measure}/4'))
        melody_part.insert(0, m21.key.Key(self.key, self.mode))
        melody_part.insert(0, m21.tempo.MetronomeMark(number=self.tempo))
        
        chord_part.insert(0, m21.meter.TimeSignature(f'{self.beats_per_measure}/4'))
        chord_part.insert(0, m21.key.Key(self.key, self.mode))
        
        bass_part.insert(0, m21.meter.TimeSignature(f'{self.beats_per_measure}/4'))
        bass_part.insert(0, m21.key.Key(self.key, self.mode))
        
        # Add melody with improved articulation and phrasing
        self._add_improved_melody(melody_part, melody)
        
        # Add chords with varied rhythm patterns
        self._add_varied_chords(chord_part, chord_progression)
        
        # Add bass line
        self._add_bass_line(bass_part, chord_progression)
        
        # Add parts to score
        score.insert(0, melody_part)
        score.insert(0, chord_part)
        score.insert(0, bass_part)
        
        return score
        
    def _add_improved_melody(self, part, melody):
        """Add melody notes with better phrasing and articulation"""
        note_duration = 4.0 / self.notes_per_beat  # in quarter lengths
        current_offset = 0.0
        
        # Group notes into phrases (4-8 notes per phrase)
        phrase_length = random.randint(4, 8)
        current_phrase = []
        
        for i, note_idx in enumerate(melody):
            # Start new phrase if needed
            if i % phrase_length == 0 and current_phrase:
                # Add a slight articulation to the last note of the phrase
                if current_phrase[-1] != -1:  # Not a rest
                    # Make the last note slightly shorter for articulation
                    part.notes[-1].quarterLength *= 0.9
                
                # Possibly add a small rest between phrases
                if random.random() < 0.3:
                    rest = m21.note.Rest(quarterLength=note_duration * 0.25)
                    part.insert(current_offset, rest)
                    current_offset += note_duration * 0.25
                
                current_phrase = []
            
            # Add the note
            if note_idx == -1:
                # Rest
                rest = m21.note.Rest(quarterLength=note_duration)
                part.insert(current_offset, rest)
            else:
                # Convert scale degree to actual pitch
                scale_degree = note_idx % self.scale_degrees
                octave_shift = note_idx // self.scale_degrees
                
                # Get the pitch from the scale
                pitch = self.scale_pitches[scale_degree]
                
                # Create a new note to avoid any object sharing
                if octave_shift > 0:
                    midi_note = pitch.midi + (octave_shift * 12)
                    n = m21.note.Note(midi_note)
                else:
                    n = m21.note.Note(pitch.nameWithOctave)
                
                # Add dynamic variations
                if i % self.beats_per_measure == 0:
                    # Emphasize downbeats
                    n.volume.velocity = 90
                elif i % 2 == 0:
                    # Medium emphasis on some beats
                    n.volume.velocity = 75
                else:
                    # Softer for other notes
                    n.volume.velocity = 60
                
                # Occasionally make notes legato or staccato
                if random.random() < 0.2:
                    # Staccato (shorter)
                    n.quarterLength = note_duration * 0.7
                elif random.random() < 0.3:
                    # Legato (connected)
                    n.quarterLength = note_duration * 1.05
                else:
                    # Normal duration
                    n.quarterLength = note_duration
                
                part.insert(current_offset, n)
                current_phrase.append(note_idx)
            
            # Advance time position
            current_offset += note_duration
    
    def _add_varied_chords(self, part, chord_progression):
        """Add chords with varied rhythmic patterns and voicings"""
        current_offset = 0.0
        
        for measure, chord_degree in enumerate(chord_progression):
            # Select a rhythm pattern for this measure (or create a new one)
            if random.random() < 0.7:
                # Use one of the predefined patterns
                pattern_name = random.choice(list(self.rhythm_patterns.keys()))
                rhythm_pattern = self.rhythm_patterns[pattern_name].copy()
            else:
                # Create a random rhythm that adds up to beats_per_measure
                rhythm_pattern = self._generate_random_rhythm()
            
            # Convert integer degree to Roman numeral notation
            roman_numeral = self.int_to_roman(chord_degree)
            
            # Create Roman numeral chord
            rn = m21.roman.RomanNumeral(roman_numeral, self.key)
            
            # Vary chord voicings
            inversion = random.randint(0, min(2, len(rn.pitches)-1))
            rn.inversion(inversion)
            
            # Sometimes add 7th or other extensions
            if random.random() < 0.3:
                # Try to add a 7th extension if not already present
                if '7' not in roman_numeral and '9' not in roman_numeral:
                    if chord_degree in [1, 4]:  # I or IV
                        extended_rn = m21.roman.RomanNumeral(roman_numeral + 'M7', self.key)
                    elif chord_degree == 5:  # V
                        extended_rn = m21.roman.RomanNumeral(roman_numeral + '7', self.key)
                    else:
                        extended_rn = m21.roman.RomanNumeral(roman_numeral + '7', self.key)
                    
                    if extended_rn is not None:
                        extended_rn.inversion(inversion)
                        rn = extended_rn
            
            # Apply rhythm pattern
            measure_offset = current_offset
            for rhythm_value in rhythm_pattern:
                if rhythm_value > 0:  # Only add positive durations
                    if rhythm_value < 0.5 and random.random() < 0.3:
                        # Sometimes use a rest for very short note values
                        rest = m21.note.Rest(quarterLength=rhythm_value)
                        part.insert(measure_offset, rest)
                    else:
                        # Create chord with this duration
                        # Extract pitch names and create a fresh chord
                        pitch_names = [p.nameWithOctave for p in rn.pitches]
                        chord_obj = m21.chord.Chord(pitch_names)
                        chord_obj.quarterLength = rhythm_value
                        
                        # Add dynamic variation
                        if measure_offset == current_offset:  # First chord in measure
                            chord_obj.volume.velocity = 85
                        elif measure_offset % 1.0 == 0.0:  # On a beat
                            chord_obj.volume.velocity = 75
                        else:  # Off-beat
                            chord_obj.volume.velocity = 65
                        
                        # Add articulation occasionally
                        if random.random() < 0.2:
                            if random.random() < 0.5:
                                chord_obj.articulations.append(m21.articulations.Staccato())
                            else:
                                chord_obj.articulations.append(m21.articulations.Accent())
                        
                        # Add chord to part
                        part.insert(measure_offset, chord_obj)
                
                measure_offset += rhythm_value
            
            # Ensure we move to the next measure
            current_offset += self.beats_per_measure
    
    def _generate_random_rhythm(self):
        """Generate a random rhythm pattern that fills a measure"""
        beats_remaining = self.beats_per_measure
        rhythm_pattern = []
        
        # Common note lengths
        note_lengths = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
        
        while beats_remaining > 0:
            # For the last bit, just use remaining beats
            if beats_remaining <= 0.25:
                rhythm_pattern.append(beats_remaining)
                break
                
            # Otherwise choose a random length that fits
            valid_lengths = [l for l in note_lengths if l <= beats_remaining]
            if not valid_lengths:
                rhythm_pattern.append(beats_remaining)
                break
                
            length = random.choice(valid_lengths)
            rhythm_pattern.append(length)
            beats_remaining -= length
        
        return rhythm_pattern
    
    def _add_bass_line(self, part, chord_progression):
        """Add an interesting bass line based on the chord progression"""
        current_offset = 0.0
        
        for chord_degree in chord_progression:
            # Convert to Roman numeral and get the root note
            roman_numeral = self.int_to_roman(chord_degree)
            rn = m21.roman.RomanNumeral(roman_numeral, self.key)
            
            # Get the root note and lower it for bass
            root = rn.root()
            bass_note = m21.note.Note(root.nameWithOctave)
            bass_note.octave = max(2, bass_note.octave - 1)  # Lower by an octave but not below C2
            
            # Choose a bass pattern based on the style or randomly
            pattern_choice = random.choice(['simple', 'walking', 'arpeggiated'])
            
            if pattern_choice == 'simple':
                # Simple pattern: root on beat 1, fifth on beat 3
                if self.beats_per_measure >= 4:
                    # Root note
                    n1 = m21.note.Note(bass_note.pitch.nameWithOctave)
                    n1.quarterLength = 2.0
                    n1.volume.velocity = 90
                    part.insert(current_offset, n1)
                    
                    # Fifth
                    fifth = m21.interval.Interval('P5')
                    fifth_pitch = fifth.transposePitch(bass_note.pitch)
                    n2 = m21.note.Note(fifth_pitch.nameWithOctave)
                    n2.quarterLength = 2.0
                    n2.volume.velocity = 75
                    part.insert(current_offset + 2.0, n2)
                else:
                    # For 3/4 or 2/4, just use root for full measure
                    n = m21.note.Note(bass_note.pitch.nameWithOctave)
                    n.quarterLength = self.beats_per_measure
                    n.volume.velocity = 90
                    part.insert(current_offset, n)
            
            elif pattern_choice == 'walking':
                # Walking bass: quarter notes following scale degrees
                scale = self.scale_obj.getPitches(bass_note.pitch.nameWithOctave)
                
                # Determine scale degree of the root
                scale_degrees = self.scale_obj.getScaleDegreeFromPitch(root)
                current_scale_idx = scale_degrees[0] - 1
                
                for beat in range(self.beats_per_measure):
                    # Decide where to move in the scale
                    if beat == 0:
                        # First beat is the root
                        idx = current_scale_idx
                    else:
                        # Other beats move up or down by step, or stay
                        direction = random.choice([-1, 0, 1])
                        idx = (current_scale_idx + direction) % len(scale)
                    
                    n = m21.note.Note(scale[idx].nameWithOctave)
                    n.quarterLength = 1.0
                    n.volume.velocity = 85 if beat == 0 else 75
                    part.insert(current_offset + beat, n)
            
            elif pattern_choice == 'arpeggiated':
                # Arpeggiated pattern: play chord tones
                chord_tones = [p for p in rn.pitches]
                
                # Lower all pitches by an octave
                for i in range(len(chord_tones)):
                    chord_tones[i].octave = max(2, chord_tones[i].octave - 1)
                
                # Create a pattern from chord tones
                quarter_notes = min(4, self.beats_per_measure)
                for beat in range(quarter_notes):
                    # Select a chord tone (usually root first)
                    if beat == 0:
                        tone_idx = 0  # Root
                    else:
                        tone_idx = beat % len(chord_tones)
                    
                    n = m21.note.Note(chord_tones[tone_idx].nameWithOctave)
                    n.quarterLength = 1.0
                    n.volume.velocity = 85 if beat == 0 else 75
                    part.insert(current_offset + beat, n)
                
                # Fill any remaining beats with the root
                if self.beats_per_measure > quarter_notes:
                    n = m21.note.Note(chord_tones[0].nameWithOctave)
                    n.quarterLength = self.beats_per_measure - quarter_notes
                    n.volume.velocity = 70
                    part.insert(current_offset + quarter_notes, n)
            
            # Move to next measure
            current_offset += self.beats_per_measure