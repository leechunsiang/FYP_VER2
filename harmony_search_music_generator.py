import random
import numpy as np
import music21 as m21
from typing import List, Dict, Tuple, Union, Optional


class HarmonySearchMusic:
    """
    Harmony Search Algorithm for music generation using music21
    """
    
    def __init__(self, 
                 key: str = 'C',
                 mode: str = 'major',
                 measures: int = 8,
                 beats_per_measure: int = 4,
                 tempo: int = 120,
                 hms: int = 30,         # Harmony Memory Size
                 hmcr: float = 0.9,     # Harmony Memory Considering Rate
                 par: float = 0.3,      # Pitch Adjustment Rate
                 bw: float = 0.1,       # Bandwidth
                 max_iter: int = 1000): # Maximum Iterations
        
        # Music parameters
        self.key = key
        self.mode = mode
        self.measures = measures
        self.beats_per_measure = beats_per_measure
        self.tempo = tempo
        self.notes_per_beat = 2  # Default: eighth notes
        self.total_notes = measures * beats_per_measure * self.notes_per_beat
        
        # Algorithm parameters
        self.hms = hms
        self.hmcr = hmcr
        self.par = par
        self.bw = bw
        self.max_iter = max_iter
        
        # Initialize music theory objects
        if mode == 'major':
            self.scale_obj = m21.scale.MajorScale(key)
        else:
            self.scale_obj = m21.scale.MinorScale(key)
            
        self.scale_pitches = self.scale_obj.getPitches()
        self.scale_degrees = len(self.scale_pitches)
        
        # Range for melody notes (in scale degrees)
        # -1 represents a rest
        self.melody_range = (-1, self.scale_degrees * 2 - 1)  # Two octaves + rest
        
        # Range for chord degrees (1-based, as in music theory)
        self.chord_range = (1, 7)
        
        # Roman numeral mapping based on mode
        if mode == 'major':
            # In major: I, ii, iii, IV, V, vi, viiº
            self.roman_numerals = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'viio']
        else:
            # In minor: i, iio, III, iv, v, VI, VII (natural minor)
            self.roman_numerals = ['i', 'iio', 'III', 'iv', 'v', 'VI', 'VII']
        
        # Harmony memory and best solution
        self.harmony_memory = []
        self.best_harmony = None
        self.best_fitness = -float('inf')
    
    def int_to_roman(self, degree: int) -> str:
        """Convert integer scale degree (1-7) to Roman numeral notation"""
        if 1 <= degree <= 7:
            return self.roman_numerals[degree - 1]
        return 'I'  # Default to I if out of range
        
    def initialize_harmony_memory(self):
        """Initialize the harmony memory with random solutions"""
        self.harmony_memory = []
        
        for _ in range(self.hms):
            # Generate random melody (collection of scale degrees)
            melody = []
            for _ in range(self.total_notes):
                # -1 represents a rest with 10% probability
                if random.random() < 0.1:
                    melody.append(-1)
                else:
                    # Random scale degree within range
                    degree = random.randint(0, self.melody_range[1])
                    melody.append(degree)
            
            # Generate random chord progression
            chord_progression = []
            for _ in range(self.measures):
                # Random chord degree (1-7)
                chord = random.randint(self.chord_range[0], self.chord_range[1])
                chord_progression.append(chord)
            
            # Create harmony object
            harmony = {
                'melody': melody,
                'chord_progression': chord_progression
            }
            
            # Evaluate fitness
            harmony['fitness'] = self.evaluate_fitness(harmony)
            self.harmony_memory.append(harmony)
            
            # Update best harmony if needed
            if harmony['fitness'] > self.best_fitness:
                self.best_harmony = harmony.copy()
                self.best_fitness = harmony['fitness']
    
    def improvise_new_harmony(self) -> Dict:
        """Generate a new harmony through improvisation"""
        new_melody = []
        new_chord_progression = []
        
        # Improvise melody
        for i in range(self.total_notes):
            if random.random() < self.hmcr:
                # Memory consideration: pick from existing harmonies
                rand_harmony = random.choice(self.harmony_memory)
                note = rand_harmony['melody'][i]
                
                # Pitch adjustment with PAR probability
                if random.random() < self.par:
                    # Skip adjustment for rests
                    if note != -1:
                        # Apply bandwidth (BW) to adjust note
                        adjustment = int(random.uniform(-self.bw, self.bw) * self.scale_degrees)
                        note = max(0, min(self.melody_range[1], note + adjustment))
            else:
                # Random selection
                if random.random() < 0.1:  # 10% chance of rest
                    note = -1
                else:
                    note = random.randint(0, self.melody_range[1])
            
            new_melody.append(note)
        
        # Improvise chord progression
        for i in range(self.measures):
            if random.random() < self.hmcr:
                # Memory consideration: pick from existing harmonies
                rand_harmony = random.choice(self.harmony_memory)
                chord = rand_harmony['chord_progression'][i]
                
                # Pitch adjustment with PAR probability
                if random.random() < self.par:
                    # Apply bandwidth to adjust chord
                    adjustment = random.choice([-1, 1])  # Simpler adjustment for chords
                    chord = max(self.chord_range[0], min(self.chord_range[1], chord + adjustment))
            else:
                # Random selection with weighted probabilities
                # More weight to I, IV, V chords in common practice music
                weights = [0.25, 0.1, 0.1, 0.2, 0.2, 0.1, 0.05]  # I, ii, iii, IV, V, vi, viiº
                chord = random.choices(range(1, 8), weights=weights)[0]
            
            new_chord_progression.append(chord)
        
        # Create new harmony
        new_harmony = {
            'melody': new_melody,
            'chord_progression': new_chord_progression
        }
        
        # Evaluate fitness
        new_harmony['fitness'] = self.evaluate_fitness(new_harmony)
        
        return new_harmony
    
    def evaluate_fitness(self, harmony: Dict) -> float:
        """
        Evaluate musical fitness using music21 analysis tools
        """
        melody = harmony['melody']
        chord_progression = harmony['chord_progression']
        
        # Create music21 stream for analysis
        score = m21.stream.Score()
        melody_part = m21.stream.Part()
        chord_part = m21.stream.Part()
        
        # Set metadata
        score.insert(0, m21.metadata.Metadata())
        score.metadata.title = "Harmony Search Composition"
        score.metadata.composer = "AI Composer"
        
        # Add time signature and key - DIFFERENT INSTANCES FOR EACH PART
        melody_part.append(m21.meter.TimeSignature(f'{self.beats_per_measure}/4'))
        melody_part.append(m21.key.Key(self.key, self.mode))
        
        # Add tempo marking
        melody_part.append(m21.tempo.MetronomeMark(number=self.tempo))
        
        # Add different time signature and key objects to chord part
        chord_part.append(m21.meter.TimeSignature(f'{self.beats_per_measure}/4'))
        chord_part.append(m21.key.Key(self.key, self.mode))
        
        # Convert melody to music21 notes
        note_duration = 4.0 / self.notes_per_beat  # in quarter lengths
        
        for note_idx in melody:
            if note_idx == -1:
                # Rest
                n = m21.note.Rest()
                n.quarterLength = note_duration
                melody_part.append(n)
            else:
                # Convert scale degree to actual pitch
                scale_degree = note_idx % self.scale_degrees
                octave_shift = note_idx // self.scale_degrees
                
                # Get the pitch from the scale
                pitch = self.scale_pitches[scale_degree]
                
                # Adjust octave if needed
                if octave_shift > 0:
                    pitch.octave += octave_shift
                
                # Create note
                n = m21.note.Note(pitch)
                n.quarterLength = note_duration
                melody_part.append(n)
        
        # Convert chord progression to music21 chords
        for chord_degree in chord_progression:
            # Convert integer degree to Roman numeral notation
            roman_numeral = self.int_to_roman(chord_degree)
            
            # Create Roman numeral chord
            rn = m21.roman.RomanNumeral(roman_numeral, self.key)
            
            # Create chord from Roman numeral - fixed the writeAsChord issue
            chord_obj = m21.chord.Chord(rn.pitches)
            chord_obj.quarterLength = self.beats_per_measure
            chord_part.append(chord_obj)
        
        score.append(melody_part)
        score.append(chord_part)
        
        # Initialize fitness
        fitness = 0.0
        
        # ---- Evaluate melodic qualities ----
        
        # 1. Melodic contour analysis
        intervals = melody_part.melodicIntervals()
        for interval in intervals:
            if interval is None:
                continue
                
            semitones = abs(interval.semitones)
            
            # Reward stepwise motion and small skips
            if semitones <= 2:  # Stepwise motion
                fitness += 0.5
            elif semitones <= 4:  # Small skip
                fitness += 0.2
            else:  # Large leap
                fitness -= 0.2
                
            # Reward direction changes (more interesting contour)
            if len(intervals) >= 3 and interval.direction != intervals[-2].direction:
                fitness += 0.2
        
        # 2. Phrase endings analysis
        # Reward if final note is tonic
        if len(melody) > 0 and melody[-1] % self.scale_degrees == 0:
            fitness += 1.0
            
        # ---- Evaluate harmonic qualities ----
        
        # 3. Common chord progression patterns
        common_progressions = [
            [1, 4, 5, 1],      # I-IV-V-I
            [1, 6, 4, 5],      # I-vi-IV-V
            [1, 5, 6, 4],      # I-V-vi-IV
            [2, 5, 1],         # ii-V-I
        ]
        
        for prog in common_progressions:
            for i in range(len(chord_progression) - len(prog) + 1):
                if chord_progression[i:i+len(prog)] == prog:
                    fitness += 2.0
        
        # 4. Cadence analysis
        if len(chord_progression) >= 2:
            # Perfect cadence (V-I)
            if chord_progression[-2:] == [5, 1]:
                fitness += 2.0
            # Plagal cadence (IV-I)
            elif chord_progression[-2:] == [4, 1]:
                fitness += 1.5
                
        # 5. Melody-harmony relationship
        # Map each note to its corresponding chord
        notes_per_chord = self.beats_per_measure * self.notes_per_beat
        for i, note_idx in enumerate(melody):
            if note_idx == -1:  # Skip rests
                continue
                
            # Find which chord this note belongs to
            chord_idx = i // notes_per_chord
            if chord_idx >= len(chord_progression):
                continue
                
            chord_degree = chord_progression[chord_idx]
            roman_numeral = self.int_to_roman(chord_degree)
            
            # Create Roman numeral chord
            rn = m21.roman.RomanNumeral(roman_numeral, self.key)
            chord_pitches = [p.name for p in rn.pitches]
            
            # Get the actual pitch for this note
            scale_degree = note_idx % self.scale_degrees
            pitch_name = self.scale_pitches[scale_degree].name
            
            # Check if note belongs to the chord
            if pitch_name in chord_pitches:
                fitness += 0.5
                
                # Extra reward if it's on a strong beat
                if i % self.notes_per_beat == 0:
                    fitness += 0.3
        
        return fitness
    
    def update_harmony_memory(self, new_harmony: Dict) -> bool:
        """
        Update harmony memory with new harmony if better than worst
        Returns True if harmony memory was updated
        """
        # Find worst harmony in memory
        worst_idx = min(range(len(self.harmony_memory)), 
                      key=lambda i: self.harmony_memory[i]['fitness'])
        
        # Replace if new harmony is better
        if new_harmony['fitness'] > self.harmony_memory[worst_idx]['fitness']:
            self.harmony_memory[worst_idx] = new_harmony.copy()
            
            # Update best harmony if needed
            if new_harmony['fitness'] > self.best_fitness:
                self.best_harmony = new_harmony.copy()
                self.best_fitness = new_harmony['fitness']
                
            return True
        
        return False
    
    def optimize(self, verbose: bool = True) -> Dict:
        """Run the harmony search optimization process"""
        # Initialize harmony memory
        self.initialize_harmony_memory()
        
        if verbose:
            print(f"Initialized harmony memory with {self.hms} solutions")
            print(f"Starting optimization with {self.max_iter} iterations...")
        
        # Iteration counter
        for iteration in range(self.max_iter):
            # Improvise new harmony
            new_harmony = self.improvise_new_harmony()
            
            # Update harmony memory
            updated = self.update_harmony_memory(new_harmony)
            
            # Report progress
            if verbose and (iteration % 100 == 0 or updated and iteration % 10 == 0):
                print(f"Iteration {iteration}, Best fitness: {self.best_fitness:.2f}")
        
        if verbose:
            print(f"Optimization complete. Final fitness: {self.best_fitness:.2f}")
            
        return self.best_harmony
    
    def create_music_stream(self, harmony: Dict) -> m21.stream.Score:
        """Convert harmony to a complete music21 stream"""
        melody = harmony['melody']
        chord_progression = harmony['chord_progression']
        
        # Create a new score
        score = m21.stream.Score()
        
        # Add metadata
        score.insert(0, m21.metadata.Metadata())
        score.metadata.title = f"Harmony Search Composition in {self.key} {self.mode}"
        score.metadata.composer = "AI Composer (Harmony Search)"
        
        # Create parts
        melody_part = m21.stream.Part()
        melody_part.id = 'Melody'
        
        chord_part = m21.stream.Part()
        chord_part.id = 'Harmony'
        
        # Add time signature, key signature and tempo - CREATE SEPARATE INSTANCES
        # For melody part
        melody_part.append(m21.meter.TimeSignature(f'{self.beats_per_measure}/4'))
        melody_part.append(m21.key.Key(self.key, self.mode))
        melody_part.append(m21.tempo.MetronomeMark(number=self.tempo))
        
        # For chord part - separate instances
        chord_part.append(m21.meter.TimeSignature(f'{self.beats_per_measure}/4'))
        chord_part.append(m21.key.Key(self.key, self.mode))
        
        # Add melody notes
        note_duration = 4.0 / self.notes_per_beat  # in quarter lengths
        
        for note_idx in melody:
            if note_idx == -1:
                # Rest
                n = m21.note.Rest()
                n.quarterLength = note_duration
                melody_part.append(n)
            else:
                # Convert scale degree to actual pitch
                scale_degree = note_idx % self.scale_degrees
                octave_shift = note_idx // self.scale_degrees
                
                # Get the pitch from the scale
                pitch = self.scale_pitches[scale_degree]
                
                # Adjust octave if needed
                if octave_shift > 0:
                    pitch.octave += octave_shift
                
                # Create note
                n = m21.note.Note(pitch)
                n.quarterLength = note_duration
                melody_part.append(n)
        
        # Add chord progression
        for chord_degree in chord_progression:
            # Convert integer degree to Roman numeral notation
            roman_numeral = self.int_to_roman(chord_degree)
            
            # Create Roman numeral chord
            rn = m21.roman.RomanNumeral(roman_numeral, self.key)
            
            # Create chord from pitches directly
            chord_obj = m21.chord.Chord(rn.pitches)
            chord_obj.quarterLength = self.beats_per_measure
            chord_part.append(chord_obj)
        
        # Add parts to score
        score.append(melody_part)
        score.append(chord_part)
        
        return score
    
    def generate_music(self, output_format: str = 'midi', filename: str = None) -> Union[str, m21.stream.Score]:
        """Generate music and export to desired format"""
        # Run optimization to get best harmony
        best_harmony = self.optimize()
        
        # Create music21 stream
        score = self.create_music_stream(best_harmony)
        
        # Output options
        if output_format == 'midi':
            if filename is None:
                filename = f"harmony_search_{self.key}_{self.mode}.mid"
            
            try:
                # Write MIDI file
                score.write('midi', fp=filename)
                print(f"MIDI file saved as: {filename}")
            except Exception as e:
                print(f"Error saving MIDI file: {e}")
                # Try a workaround by creating a new clean score
                new_score = self.create_clean_score_for_export(best_harmony)
                new_score.write('midi', fp=filename)
                print(f"MIDI file saved using alternative method: {filename}")
                
            return filename
            
        elif output_format == 'musicxml':
            if filename is None:
                filename = f"harmony_search_{self.key}_{self.mode}.musicxml"
            
            # Write MusicXML file
            score.write('musicxml', fp=filename)
            print(f"MusicXML file saved as: {filename}")
            return filename
            
        else:
            # Return the music21 stream
            return score
    
    def create_clean_score_for_export(self, harmony: Dict) -> m21.stream.Score:
        """Create a clean score for export, avoiding potential object reuse issues"""
        melody = harmony['melody']
        chord_progression = harmony['chord_progression']
        
        # Create a completely new score
        score = m21.stream.Score()
        
        # Add metadata
        score.insert(0, m21.metadata.Metadata())
        score.metadata.title = f"Harmony Search Composition in {self.key} {self.mode}"
        score.metadata.composer = "AI Composer (Harmony Search)"
        
        # Create parts with different IDs to avoid collision
        melody_part = m21.stream.Part(id='Melody1')
        chord_part = m21.stream.Part(id='Harmony1')
        
        # Add time signature, key signature and tempo with new instances
        melody_part.insert(0, m21.meter.TimeSignature(f'{self.beats_per_measure}/4'))
        melody_part.insert(0, m21.key.Key(self.key, self.mode))
        melody_part.insert(0, m21.tempo.MetronomeMark(number=self.tempo))
        
        chord_part.insert(0, m21.meter.TimeSignature(f'{self.beats_per_measure}/4'))
        chord_part.insert(0, m21.key.Key(self.key, self.mode))
        
        # Add melody notes
        note_duration = 4.0 / self.notes_per_beat  # in quarter lengths
        current_time = 0.0
        
        for note_idx in melody:
            if note_idx == -1:
                # Rest
                n = m21.note.Rest(quarterLength=note_duration)
                melody_part.insert(current_time, n)
            else:
                # Convert scale degree to actual pitch
                scale_degree = note_idx % self.scale_degrees
                octave_shift = note_idx // self.scale_degrees
                
                # Create a new pitch object
                if octave_shift > 0:
                    midi_note = self.scale_pitches[scale_degree].midi + (octave_shift * 12)
                    n = m21.note.Note(midi_note, quarterLength=note_duration)
                else:
                    n = m21.note.Note(self.scale_pitches[scale_degree], quarterLength=note_duration)
                
                melody_part.insert(current_time, n)
            
            current_time += note_duration
        
        # Add chord progression
        current_time = 0.0
        for chord_degree in chord_progression:
            # Convert integer degree to Roman numeral notation
            roman_numeral = self.int_to_roman(chord_degree)
            
            # Create Roman numeral chord
            rn = m21.roman.RomanNumeral(roman_numeral, self.key)
            
            # Create a new chord object
            pitches = [p.nameWithOctave for p in rn.pitches]
            chord_obj = m21.chord.Chord(pitches)
            chord_obj.quarterLength = self.beats_per_measure
            
            chord_part.insert(current_time, chord_obj)
            current_time += self.beats_per_measure
        
        # Add parts to score using insert instead of append
        score.insert(0, melody_part)
        score.insert(0, chord_part)
        
        return score


def main():
    """Example usage"""
    # Create a music generator with default parameters
    hs = HarmonySearchMusic(
        key='D',
        mode='major',
        measures=8,
        beats_per_measure=4,
        tempo=120,
        hms=30,
        hmcr=0.9,
        par=0.3,
        bw=0.1,
        max_iter=500
    )
    
    # Generate music
    midi_file = hs.generate_music(output_format='midi')
    
    print(f"Music generation complete!")
    print(f"Best fitness score: {hs.best_fitness:.2f}")


if __name__ == "__main__":
    main()