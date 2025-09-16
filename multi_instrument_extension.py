import music21 as m21
from harmony_search_music_generator import HarmonySearchMusic

class MultiInstrumentGenerator:
    """
    Extension for generating multi-instrument arrangements from harmony search results
    """
    
    # GM instrument program numbers
    INSTRUMENTS = {
        "piano": 0,
        "acoustic_guitar": 24,
        "electric_guitar": 27,
        "acoustic_bass": 32,
        "electric_bass": 33,
        "violin": 40,
        "cello": 42,
        "trumpet": 56,
        "saxophone": 65,
        "flute": 73,
        "drum_kit": 118  # Special case, uses channel 9
    }
    
    def __init__(self, harmony_search: HarmonySearchMusic):
        self.harmony_search = harmony_search
        
    def generate_arrangement(self, harmony: dict, instruments: list, filename: str = None):
        """Generate a multi-instrument arrangement from a harmony"""
        if filename is None:
            filename = f"multi_instrument_{self.harmony_search.key}_{self.harmony_search.mode}.mid"
        
        # Generate a clean arrangement with unique objects for each part
        arrangement = self._create_clean_arrangement(harmony, instruments)
            
        # Write to MIDI with error handling
        try:
            arrangement.write('midi', fp=filename)
            print(f"Multi-instrument MIDI file saved as: {filename}")
        except Exception as e:
            print(f"Error saving MIDI: {e}")
            # Try a different approach if the first one fails
            simplified = self._create_simplified_arrangement(harmony, instruments)
            simplified.write('midi', fp=filename)
            print(f"Multi-instrument MIDI file saved using alternative method: {filename}")
            
        return filename
    
    def _create_clean_arrangement(self, harmony: dict, instruments: list) -> m21.stream.Score:
        """Create a clean multi-instrument arrangement with unique objects for each part"""
        melody = harmony['melody']
        chord_progression = harmony['chord_progression']
        
        # Create a new score
        score = m21.stream.Score()
        
        # Add metadata
        metadata = m21.metadata.Metadata()
        metadata.title = f"Multi-instrument Arrangement in {self.harmony_search.key} {self.harmony_search.mode}"
        metadata.composer = "AI Composer (Harmony Search)"
        score.insert(0, metadata)
        
        # Create parts for each instrument
        parts = []
        for i, instrument_name in enumerate(instruments[:3]):  # Limit to 3 instruments
            part = m21.stream.Part()
            part.id = f'{instrument_name}_{i}'
            
            # Create new time signature and key for each part
            ts = m21.meter.TimeSignature(f'{self.harmony_search.beats_per_measure}/4')
            ks = m21.key.Key(self.harmony_search.key, self.harmony_search.mode)
            
            # Add to part at offset 0
            part.insert(0, ts)
            part.insert(0, ks)
            
            # Add tempo to first part only
            if i == 0:
                tempo = m21.tempo.MetronomeMark(number=self.harmony_search.tempo)
                part.insert(0, tempo)
            
            # Store part
            parts.append(part)
        
        # Fill in melody (first instrument)
        if len(parts) >= 1:
            self._add_melody_to_part(parts[0], melody)
            
        # Fill in chords (second instrument if available)
        if len(parts) >= 2:
            self._add_chords_to_part(parts[1], chord_progression)
            
        # Fill in bass (third instrument if available)
        if len(parts) >= 3:
            self._add_bass_to_part(parts[2], chord_progression)
        
        # Add all parts to the score
        for part in parts:
            score.append(part)
            
        return score
    
    def _add_melody_to_part(self, part: m21.stream.Part, melody: list):
        """Add melody notes to a part"""
        note_duration = 4.0 / self.harmony_search.notes_per_beat  # in quarter lengths
        current_offset = 0.0
        
        for note_idx in melody:
            if note_idx == -1:
                # Rest
                n = m21.note.Rest()
                n.quarterLength = note_duration
                part.insert(current_offset, n)
            else:
                # Convert scale degree to actual pitch
                scale_degree = note_idx % self.harmony_search.scale_degrees
                octave_shift = note_idx // self.harmony_search.scale_degrees
                
                # Get the pitch from the scale
                pitch = self.harmony_search.scale_pitches[scale_degree]
                
                # Create a new note with the correct pitch and octave
                if octave_shift > 0:
                    midi_note = pitch.midi + (octave_shift * 12)
                    n = m21.note.Note(midi_note)
                else:
                    # Create a completely new Note to avoid any object sharing
                    n = m21.note.Note(pitch.nameWithOctave)
                
                n.quarterLength = note_duration
                part.insert(current_offset, n)
            
            current_offset += note_duration
    
    def _add_chords_to_part(self, part: m21.stream.Part, chord_progression: list):
        """Add chords to a part"""
        current_offset = 0.0
        
        for chord_degree in chord_progression:
            # Convert integer degree to Roman numeral notation
            roman_numeral = self.harmony_search.int_to_roman(chord_degree)
            
            # Create Roman numeral chord
            rn = m21.roman.RomanNumeral(roman_numeral, self.harmony_search.key)
            
            # Extract pitch names and create a fresh chord to avoid object reuse
            pitch_names = [p.nameWithOctave for p in rn.pitches]
            chord_obj = m21.chord.Chord(pitch_names)
            chord_obj.quarterLength = self.harmony_search.beats_per_measure
            
            # Add to part
            part.insert(current_offset, chord_obj)
            current_offset += self.harmony_search.beats_per_measure
    
    def _add_bass_to_part(self, part: m21.stream.Part, chord_progression: list):
        """Add bass line to a part"""
        current_offset = 0.0
        
        for chord_degree in chord_progression:
            # Convert integer degree to Roman numeral notation
            roman_numeral = self.harmony_search.int_to_roman(chord_degree)
            
            # Create Roman numeral chord
            rn = m21.roman.RomanNumeral(roman_numeral, self.harmony_search.key)
            
            # Get the root note and lower it by an octave for bass
            root = rn.root()
            bass_note = m21.note.Note(root.nameWithOctave)
            bass_note.octave = max(2, bass_note.octave - 1)  # Lower by an octave but not below C2
            
            # For each beat in the measure
            beats_per_measure = self.harmony_search.beats_per_measure
            for beat in range(beats_per_measure):
                # Create a new bass note for each beat to avoid object sharing
                if beat == 0:
                    # Root note on first beat
                    n = m21.note.Note(bass_note.pitch.nameWithOctave)
                    n.quarterLength = 1.0
                elif beat % 2 == 0:
                    # Root note on even beats
                    n = m21.note.Note(bass_note.pitch.nameWithOctave)
                    n.quarterLength = 1.0
                else:
                    # Fifth on odd beats (if not the first beat)
                    fifth = m21.interval.Interval('P5')
                    fifth_pitch = fifth.transposePitch(bass_note.pitch)
                    n = m21.note.Note(fifth_pitch.nameWithOctave)
                    n.quarterLength = 1.0
                
                # Add the note
                part.insert(current_offset + beat, n)
            
            current_offset += beats_per_measure
    
    def _create_simplified_arrangement(self, harmony: dict, instruments: list) -> m21.stream.Score:
        """Create a simplified arrangement as a fallback"""
        # Create separate streams that don't share any objects
        score = m21.stream.Score()
        
        # Get basic musical elements from harmony
        melody = harmony['melody']
        chord_progression = harmony['chord_progression']
        
        # Create parts with unique IDs
        for i, instrument_name in enumerate(instruments[:3]):
            # Create a completely new part
            part = m21.stream.Part(id=f'{instrument_name}_{i}_simple')
            
            # Add unique time signature and key signature
            part.append(m21.meter.TimeSignature(f'{self.harmony_search.beats_per_measure}/4'))
            part.append(m21.key.Key(self.harmony_search.key, self.harmony_search.mode))
            
            # Add tempo to first part only
            if i == 0:
                part.append(m21.tempo.MetronomeMark(number=self.harmony_search.tempo))
                
                # Add melody to first part
                note_duration = 4.0 / self.harmony_search.notes_per_beat
                for note_idx in melody:
                    if note_idx == -1:
                        # Rest
                        part.append(m21.note.Rest(quarterLength=note_duration))
                    else:
                        # Create a note from scratch
                        scale_degree = note_idx % self.harmony_search.scale_degrees
                        octave_shift = note_idx // self.harmony_search.scale_degrees
                        
                        if scale_degree < len(self.harmony_search.scale_pitches):
                            pitch_name = self.harmony_search.scale_pitches[scale_degree].nameWithOctave
                            note = m21.note.Note(pitch_name)
                            if octave_shift > 0:
                                note.octave += octave_shift
                            note.quarterLength = note_duration
                            part.append(note)
            
            # Add chords to second part
            elif i == 1 and len(chord_progression) > 0:
                for chord_idx in chord_progression:
                    roman_numeral = self.harmony_search.int_to_roman(chord_idx)
                    rn = m21.roman.RomanNumeral(roman_numeral, self.harmony_search.key)
                    
                    # Create a new chord from scratch with pitch names
                    pitches = [p.nameWithOctave for p in rn.pitches]
                    chord = m21.chord.Chord(pitches)
                    chord.quarterLength = self.harmony_search.beats_per_measure
                    part.append(chord)
            
            # Add bass to third part
            elif i == 2 and len(chord_progression) > 0:
                for chord_idx in chord_progression:
                    roman_numeral = self.harmony_search.int_to_roman(chord_idx)
                    rn = m21.roman.RomanNumeral(roman_numeral, self.harmony_search.key)
                    
                    # Get the root and create a bass note
                    root = rn.root().nameWithOctave
                    bass_note = m21.note.Note(root)
                    bass_note.octave = 3  # Fixed octave for simplicity
                    bass_note.quarterLength = self.harmony_search.beats_per_measure
                    part.append(bass_note)
            
            # Add the part to the score
            score.append(part)
        
        return score
        
    def generate_full_arrangement(self, 
                                 harmony: dict = None, 
                                 style: str = 'classical',
                                 filename: str = None):
        """Generate a style-specific arrangement with appropriate instruments"""
        
        # Use best harmony if none provided
        if harmony is None:
            harmony = self.harmony_search.best_harmony
        
        # Define instrument combinations for different styles
        style_instruments = {
            'classical': ['violin', 'piano', 'cello'],
            'jazz': ['saxophone', 'piano', 'acoustic_bass'],
            'rock': ['electric_guitar', 'electric_guitar', 'electric_bass'],
            'pop': ['piano', 'acoustic_guitar', 'electric_bass']
        }
        
        # Select instruments based on style
        if style in style_instruments:
            instruments = style_instruments[style]
        else:
            instruments = ['piano', 'piano', 'acoustic_bass']  # Default
        
        # Generate the arrangement
        if filename is None:
            filename = f"{style}_arrangement_{self.harmony_search.key}_{self.harmony_search.mode}.mid"
            
        return self.generate_arrangement(harmony, instruments, filename)