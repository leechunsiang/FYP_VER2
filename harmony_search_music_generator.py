import os
import random
import numpy as np
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import mido
from mido import Message, MidiFile, MidiTrack
import pygame
from PIL import Image, ImageTk
from functools import partial
import webbrowser

# Constants for music theory
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]  # Major scale intervals
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]  # Minor scale intervals
PENTATONIC_SCALE = [0, 2, 4, 7, 9]    # Major pentatonic scale intervals
BLUES_SCALE = [0, 3, 5, 6, 7, 10]     # Blues scale intervals

# Common chord progressions (in scale degrees)
CHORD_PROGRESSIONS = {
    'pop': [[1, 5, 6, 4], [1, 4, 5, 4], [1, 6, 4, 5]],  # Popular progressions
    'jazz': [[2, 5, 1, 6], [1, 6, 2, 5], [3, 6, 2, 5, 1]],  # Jazz progressions
    'classical': [[1, 4, 5, 1], [1, 6, 4, 5, 1], [1, 2, 5, 1]]  # Classical progressions
}

# Rhythmic patterns (1 = note, 0 = rest)
RHYTHMIC_PATTERNS = {
    'simple': [1, 0, 1, 0, 1, 0, 1, 0],
    'syncopated': [1, 0, 0, 1, 0, 1, 0, 0],
    'complex': [1, 1, 0, 1, 0, 0, 1, 0],
    'waltz': [1, 0, 0, 1, 0, 0],
    'swing': [1, 0, 1, 0, 0, 1, 0, 0],
}

# Melody contour patterns (direction of melodic movement)
CONTOUR_PATTERNS = [
    [1, 1, -1, -1],  # Up, up, down, down
    [1, -1, 1, -1],  # Up, down, up, down
    [1, 1, 1, -1, -1, -1],  # Ascending and then descending
    [-1, 1, 1, 1, -1],  # Down, up, up, up, down
]

class HarmonySearchMusic:
    def __init__(self):
        # Default algorithm parameters
        self.HMS = 20  # Harmony Memory Size
        self.HMCR = 0.9  # Harmony Memory Consideration Rate
        self.PAR = 0.3  # Pitch Adjustment Rate
        self.max_improvisations = 100  # Maximum number of improvisations
        
        # Default music parameters
        self.key = 'C'  # Music key
        self.scale_type = 'major'  # Scale type
        self.tempo = 120  # BPM
        self.measures = 4  # Number of measures
        self.time_signature = (4, 4)  # Time signature
        self.complexity = 0.5  # Complexity factor (0-1)
        self.progression_style = 'pop'  # Style of chord progression
        self.rhythm_style = 'simple'  # Style of rhythm
        self.instrument = 0  # Default instrument (piano)
        self.note_duration = 0.25  # Default note duration (quarter note)
        self.velocity_range = (60, 100)  # MIDI velocity range
        
        # Internal variables
        self.harmony_memory = []  # Harmony memory
        self.best_harmony = None  # Best harmony found
        self.scale = []  # Current scale
        self.base_note = self._note_to_midi(self.key)  # Base MIDI note
        self.chord_progression = []  # Current chord progression
        self._generate_scale()
        self._select_chord_progression()
        
    def _note_to_midi(self, note):
        """Convert a note name to MIDI note number"""
        notes = {'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63,
                'E': 64, 'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68,
                'Ab': 68, 'A': 69, 'A#': 70, 'Bb': 70, 'B': 71}
        return notes.get(note, 60)
        
    def _generate_scale(self):
        """Generate a scale based on key and scale type"""
        base = self._note_to_midi(self.key)
        
        # Choose intervals based on scale type
        if self.scale_type == 'major':
            intervals = MAJOR_SCALE
        elif self.scale_type == 'minor':
            intervals = MINOR_SCALE
        elif self.scale_type == 'pentatonic':
            intervals = PENTATONIC_SCALE
        elif self.scale_type == 'blues':
            intervals = BLUES_SCALE
        else:
            intervals = MAJOR_SCALE
            
        # Generate scale across multiple octaves
        self.scale = []
        for octave in range(-1, 3):  # Generate notes across 4 octaves
            for interval in intervals:
                note = base + interval + (octave * 12)
                if 0 <= note < 128:  # Ensure note is in valid MIDI range
                    self.scale.append(note)
                    
    def _select_chord_progression(self):
        """Select a chord progression based on style"""
        if self.progression_style in CHORD_PROGRESSIONS:
            # Randomly select a progression from the chosen style
            progression = random.choice(CHORD_PROGRESSIONS[self.progression_style])
            self.chord_progression = progression
        else:
            # Default to a simple I-IV-V-I progression
            self.chord_progression = [1, 4, 5, 1]
            
    def _get_chord_notes(self, degree, octave=0):
        """Get chord notes for a given scale degree"""
        if self.scale_type == 'major':
            intervals = [0, 2, 4]  # Triad: Root, 3rd, 5th
        else:
            intervals = [0, 2, 4]  # Default to major triad structure
            
        # Adjust for scale degree
        degree = (degree - 1) % len(self.scale)
        root_idx = degree * 2  # Assuming diatonic scale with 7 notes
        
        chord_notes = []
        for interval in intervals:
            idx = (root_idx + interval) % len(self.scale)
            note = self.scale[idx] + (octave * 12)
            if 0 <= note < 128:  # Check MIDI range
                chord_notes.append(note)
                
        return chord_notes
    
    def _generate_initial_harmony_memory(self):
        """Generate initial harmony memory"""
        self.harmony_memory = []
        for _ in range(self.HMS):
            # Create a new harmony
            harmony = self._generate_random_harmony()
            self.harmony_memory.append({
                'melody': harmony,
                'fitness': self._evaluate_fitness(harmony)
            })
            
        # Sort harmony memory by fitness (descending)
        self.harmony_memory.sort(key=lambda x: x['fitness'], reverse=True)
        
    def _generate_random_harmony(self):
        """Generate a random harmony (melody)"""
        total_beats = self.measures * self.time_signature[0]
        beats_per_measure = self.time_signature[0]
        notes_per_beat = int(1 / self.note_duration)
        total_notes = total_beats * notes_per_beat
        
        melody = []
        
        # Select a rhythm pattern
        if self.rhythm_style in RHYTHMIC_PATTERNS:
            rhythm = RHYTHMIC_PATTERNS[self.rhythm_style]
        else:
            rhythm = RHYTHMIC_PATTERNS['simple']
            
        # Select a melodic contour pattern
        contour = random.choice(CONTOUR_PATTERNS)
        contour_idx = 0
        
        # Current note (start in the middle of the scale)
        current_note_idx = len(self.scale) // 2
        
        for i in range(total_notes):
            # Determine if this beat should have a note or rest based on rhythm pattern
            current_measure = i // (beats_per_measure * notes_per_beat)
            current_beat_in_measure = (i // notes_per_beat) % beats_per_measure
            rhythm_idx = i % len(rhythm)
            
            if rhythm[rhythm_idx] == 1:
                # Apply contour to create more musical movement
                direction = contour[contour_idx % len(contour)]
                contour_idx += 1
                
                # Adjust note index based on contour direction and complexity
                step = max(1, int(random.random() * 3 * self.complexity))
                current_note_idx += direction * step
                
                # Keep index within scale bounds
                current_note_idx = max(0, min(current_note_idx, len(self.scale) - 1))
                
                # Select note from scale
                note = self.scale[current_note_idx]
                
                # Adjust for chord context - higher probability of chord tones
                current_chord_degree = self.chord_progression[current_measure % len(self.chord_progression)]
                chord_notes = self._get_chord_notes(current_chord_degree)
                
                # 60% chance to use a chord tone if complexity is low
                if random.random() > self.complexity and random.random() < 0.6:
                    if chord_notes:
                        note = random.choice(chord_notes)
                
                # Add note with velocity variation
                velocity = random.randint(*self.velocity_range)
                
                # Add articulation variation (duration adjustment)
                duration_factor = 0.8 + (random.random() * 0.4)
                duration = self.note_duration * duration_factor
                
                melody.append({
                    'note': note,
                    'velocity': velocity,
                    'duration': duration,
                    'is_rest': False
                })
            else:
                # Add rest
                melody.append({
                    'note': 0,
                    'velocity': 0,
                    'duration': self.note_duration,
                    'is_rest': True
                })
                
        return melody
        
    def _evaluate_fitness(self, melody):
        """Evaluate the fitness of a melody"""
        if not melody:
            return 0
            
        fitness = 0
        total_notes = sum(1 for note in melody if not note['is_rest'])
        
        if total_notes == 0:
            return 0
            
        # Analyze melodic features
        non_rest_notes = [note['note'] for note in melody if not note['is_rest']]
        
        # 1. Pitch Range - reward reasonable range (not too narrow, not too wide)
        if non_rest_notes:
            pitch_range = max(non_rest_notes) - min(non_rest_notes)
            # Ideal range around 12-24 semitones (1-2 octaves)
            if pitch_range > 0:
                range_score = 1.0 - abs(pitch_range - 18) / 36
                fitness += range_score * 10
            
        # 2. Melodic Contour - reward interesting contours
        contour_changes = 0
        direction = 0
        prev_direction = 0
        
        for i in range(1, len(non_rest_notes)):
            if non_rest_notes[i] > non_rest_notes[i-1]:
                direction = 1
            elif non_rest_notes[i] < non_rest_notes[i-1]:
                direction = -1
            else:
                direction = 0
                
            if direction != 0 and direction != prev_direction and prev_direction != 0:
                contour_changes += 1
                
            prev_direction = direction if direction != 0 else prev_direction
            
        # Reward appropriate number of contour changes
        contour_score = min(contour_changes / (total_notes / 5), 1.0)
        fitness += contour_score * 15
        
        # 3. Chord Tone Alignment - reward notes that align with chord progression
        chord_alignment = 0
        total_beats = self.measures * self.time_signature[0]
        notes_per_beat = int(1 / self.note_duration)
        
        for i, note in enumerate(melody):
            if note['is_rest']:
                continue
                
            beat_position = i / notes_per_beat
            measure = int(beat_position / self.time_signature[0])
            chord_degree = self.chord_progression[measure % len(self.chord_progression)]
            chord_notes = self._get_chord_notes(chord_degree)
            
            # Check if note is in chord
            if note['note'] in chord_notes:
                chord_alignment += 1
                
        chord_score = chord_alignment / total_notes
        fitness += chord_score * 25
        
        # 4. Rhythmic Interest - reward balanced use of notes and rests
        notes_count = sum(1 for note in melody if not note['is_rest'])
        rests_count = len(melody) - notes_count
        rhythm_ratio = notes_count / (notes_count + rests_count)
        
        # Favor ratios between 0.6 and 0.8 (more notes than rests, but not all notes)
        rhythm_score = 1.0 - abs(rhythm_ratio - 0.7) / 0.7
        fitness += rhythm_score * 20
        
        # 5. Repetition and Variation - reward some repetition but not too much
        note_counts = {}
        for note in melody:
            if not note['is_rest']:
                if note['note'] in note_counts:
                    note_counts[note['note']] += 1
                else:
                    note_counts[note['note']] = 1
                    
        # Count unique notes and calculate diversity
        unique_notes = len(note_counts)
        max_repeats = max(note_counts.values()) if note_counts else 0
        diversity_score = min(unique_notes / 12, 1.0)  # Reward having at least 12 unique notes
        repetition_penalty = min(max_repeats / total_notes, 0.5)  # Penalize excessive repetition
        
        fitness += diversity_score * 20 - repetition_penalty * 10
        
        # 6. Penalize dissonance - check for unpleasant intervals
        dissonance_count = 0
        dissonant_intervals = [1, 2, 11, 13]  # Semitones that are generally dissonant
        
        for i in range(1, len(non_rest_notes)):
            interval = abs(non_rest_notes[i] - non_rest_notes[i-1]) % 12
            if interval in dissonant_intervals:
                # Allow some dissonance based on complexity factor
                if random.random() > self.complexity:
                    dissonance_count += 1
                    
        dissonance_penalty = min(dissonance_count / total_notes, 1.0)
        fitness -= dissonance_penalty * 15
        
        # 7. Reward melodic patterns and motifs
        # Check for repeated motifs of 3-5 notes
        motifs = {}
        max_motif_len = min(5, total_notes // 3)
        
        for motif_len in range(3, max_motif_len + 1):
            for i in range(len(non_rest_notes) - motif_len + 1):
                motif = tuple(non_rest_notes[i:i+motif_len])
                if motif in motifs:
                    motifs[motif] += 1
                else:
                    motifs[motif] = 1
                    
        # Reward having 2-3 repeated motifs
        repeated_motifs = sum(1 for count in motifs.values() if count > 1)
        motif_score = min(repeated_motifs / 3, 1.0)
        fitness += motif_score * 10
        
        return fitness
        
    def _improvise_new_harmony(self):
        """Create a new harmony based on harmony memory and random improvisation"""
        total_beats = self.measures * self.time_signature[0]
        notes_per_beat = int(1 / self.note_duration)
        total_notes = total_beats * notes_per_beat
        
        new_melody = []
        
        for i in range(total_notes):
            # Decide whether to use harmony memory or random value
            if random.random() < self.HMCR:
                # Use harmony memory
                random_harmony = random.choice(self.harmony_memory)
                note_data = random_harmony['melody'][i].copy()
                
                # Decide whether to adjust pitch
                if random.random() < self.PAR and not note_data['is_rest']:
                    # Adjust pitch
                    current_idx = self.scale.index(note_data['note']) if note_data['note'] in self.scale else 0
                    adjustment = random.choice([-2, -1, 1, 2])  # Allow bigger jumps for variety
                    new_idx = max(0, min(current_idx + adjustment, len(self.scale) - 1))
                    note_data['note'] = self.scale[new_idx]
                    
                    # Also adjust velocity slightly for expressiveness
                    velocity_change = random.randint(-5, 5)
                    note_data['velocity'] = max(self.velocity_range[0], 
                                               min(note_data['velocity'] + velocity_change, 
                                                   self.velocity_range[1]))
                    
                    # Adjust duration slightly
                    duration_change = 0.05 * random.choice([-1, 1])
                    note_data['duration'] = max(0.1, min(note_data['duration'] + duration_change, 0.5))
            else:
                # Generate a new random note
                measure_idx = (i // notes_per_beat) // self.time_signature[0]
                chord_degree = self.chord_progression[measure_idx % len(self.chord_progression)]
                
                # Decide if this should be a note or rest
                if random.random() < 0.8:  # 80% chance of a note
                    if random.random() < 0.7:  # 70% chance to use a note from the scale
                        note = random.choice(self.scale)
                    else:  # 30% chance to use a chord tone
                        chord_notes = self._get_chord_notes(chord_degree)
                        note = random.choice(chord_notes) if chord_notes else random.choice(self.scale)
                        
                    velocity = random.randint(*self.velocity_range)
                    duration = self.note_duration * (0.8 + random.random() * 0.4)
                    
                    note_data = {
                        'note': note,
                        'velocity': velocity,
                        'duration': duration,
                        'is_rest': False
                    }
                else:
                    # Create a rest
                    note_data = {
                        'note': 0,
                        'velocity': 0,
                        'duration': self.note_duration,
                        'is_rest': True
                    }
            
            new_melody.append(note_data)
            
        return new_melody
        
    def generate_music(self):
        """Main function to generate music using harmony search"""
        # Prepare scale and chord progression
        self._generate_scale()
        self._select_chord_progression()
        
        # Generate initial harmony memory
        self._generate_initial_harmony_memory()
        
        # Improvisation process
        for _ in range(self.max_improvisations):
            # Create new harmony by improvisation
            new_harmony = self._improvise_new_harmony()
            new_fitness = self._evaluate_fitness(new_harmony)
            
            # Check if new harmony should replace worst harmony
            if new_fitness > self.harmony_memory[-1]['fitness']:
                self.harmony_memory[-1] = {
                    'melody': new_harmony,
                    'fitness': new_fitness
                }
                
                # Sort harmony memory by fitness (descending)
                self.harmony_memory.sort(key=lambda x: x['fitness'], reverse=True)
                
        # Select best harmony
        self.best_harmony = self.harmony_memory[0]['melody']
        return self.best_harmony
        
    def generate_midi(self):
        """Generate MIDI file from best harmony"""
        mid = MidiFile()
        
        # Create track for melody
        melody_track = MidiTrack()
        mid.tracks.append(melody_track)
        
        # Set tempo
        tempo_in_us = mido.bpm2tempo(self.tempo)
        melody_track.append(mido.MetaMessage('set_tempo', tempo=tempo_in_us))
        
        # Set instrument
        melody_track.append(Message('program_change', program=self.instrument, time=0))
        
        # Add notes from best harmony
        current_time = 0
        
        for note_data in self.best_harmony:
            if not note_data['is_rest']:
                # Ensure note is in valid MIDI range
                midi_note = int(note_data['note'])
                if midi_note < 0 or midi_note > 127:
                    midi_note = 60  # Default to middle C if out of range
                
                # Note on
                melody_track.append(Message('note_on', note=midi_note, 
                                        velocity=note_data['velocity'], 
                                        time=current_time))
                current_time = 0
                
                # Calculate note duration in ticks
                duration_ticks = int(note_data['duration'] * mid.ticks_per_beat * 4)
                
                # Note off
                melody_track.append(Message('note_off', note=midi_note, 
                                        velocity=0, 
                                        time=duration_ticks))
                current_time = 0
            else:
                # For rests, just advance time
                current_time += int(note_data['duration'] * mid.ticks_per_beat * 4)
        
        # Create a second track for chords/accompaniment
        chord_track = MidiTrack()
        mid.tracks.append(chord_track)
        
        # Set instrument for chords (e.g., piano)
        chord_track.append(Message('program_change', program=0, time=0))
        
        # Add chords
        current_time = 0
        measures = self.measures
        beats_per_measure = self.time_signature[0]
        
        for measure in range(measures):
            chord_degree = self.chord_progression[measure % len(self.chord_progression)]
            chord_notes = self._get_chord_notes(chord_degree, octave=-1)  # Lower octave for chords
            
            # Play chord at the beginning of each measure
            for note in chord_notes:
                if 0 <= note <= 127:  # Ensure note is in valid MIDI range
                    chord_track.append(Message('note_on', note=note, 
                                         velocity=70, 
                                         time=current_time))
                    current_time = 0
            
            # Calculate measure duration in ticks
            measure_duration = beats_per_measure * mid.ticks_per_beat
            
            # Note off at the end of measure
            for note in chord_notes:
                if 0 <= note <= 127:
                    chord_track.append(Message('note_off', note=note, 
                                         velocity=0, 
                                         time=measure_duration if current_time == 0 else 0))
                    current_time = 0
                    
        # Save MIDI file to temp location
        output_file = 'generated_music.mid'
        mid.save(output_file)
        return output_file
        
    def set_parameters(self, **kwargs):
        """Update algorithm parameters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
        # Recalculate dependent parameters
        if 'key' in kwargs or 'scale_type' in kwargs:
            self._generate_scale()
            
        if 'progression_style' in kwargs:
            self._select_chord_progression()


class MusicGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Harmony Search Music Generator")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        self.harmony_search = HarmonySearchMusic()
        self.current_midi_file = None
        self.is_playing = False
        self.generation_thread = None
        
        # Initialize Pygame mixer
        pygame.mixer.init()
        
        self._create_gui()
        
    def _create_gui(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create tabs
        algorithm_tab = ttk.Frame(notebook)
        music_tab = ttk.Frame(notebook)
        output_tab = ttk.Frame(notebook)
        
        notebook.add(algorithm_tab, text="Algorithm Settings")
        notebook.add(music_tab, text="Music Settings")
        notebook.add(output_tab, text="Generated Music")
        
        # Algorithm Settings Tab
        self._create_algorithm_tab(algorithm_tab)
        
        # Music Settings Tab
        self._create_music_tab(music_tab)
        
        # Output Tab
        self._create_output_tab(output_tab)
        
        # Create bottom controls
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        generate_button = ttk.Button(bottom_frame, text="Generate Music", 
                                    command=self.start_generation)
        generate_button.pack(side=tk.LEFT, padx=5)
        
        play_button = ttk.Button(bottom_frame, text="Play/Stop", 
                                command=self.toggle_play)
        play_button.pack(side=tk.LEFT, padx=5)
        
        save_button = ttk.Button(bottom_frame, text="Save MIDI File", 
                                command=self.save_midi)
        save_button.pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(bottom_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT, padx=5)
        
    def _create_algorithm_tab(self, parent):
        # Create frame with padding
        frame = ttk.Frame(parent, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Harmony Search Algorithm Parameters", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # HMS Slider
        ttk.Label(frame, text="Harmony Memory Size (HMS):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.hms_var = tk.IntVar(value=self.harmony_search.HMS)
        hms_slider = ttk.Scale(frame, from_=5, to=50, variable=self.hms_var, 
                              orient=tk.HORIZONTAL, length=200)
        hms_slider.grid(row=1, column=1, sticky=tk.W)
        ttk.Label(frame, textvariable=self.hms_var).grid(row=1, column=2)
        
        # HMCR Slider
        ttk.Label(frame, text="Harmony Memory Consideration Rate:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.hmcr_var = tk.DoubleVar(value=self.harmony_search.HMCR)
        hmcr_slider = ttk.Scale(frame, from_=0.1, to=1.0, variable=self.hmcr_var, 
                               orient=tk.HORIZONTAL, length=200)
        hmcr_slider.grid(row=2, column=1, sticky=tk.W)
        self.hmcr_label = ttk.Label(frame, text=f"{self.hmcr_var.get():.2f}")
        self.hmcr_label.grid(row=2, column=2)
        hmcr_slider.configure(command=lambda v: self.hmcr_label.configure(text=f"{float(v):.2f}"))
        
        # PAR Slider
        ttk.Label(frame, text="Pitch Adjustment Rate:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.par_var = tk.DoubleVar(value=self.harmony_search.PAR)
        par_slider = ttk.Scale(frame, from_=0.1, to=0.9, variable=self.par_var, 
                              orient=tk.HORIZONTAL, length=200)
        par_slider.grid(row=3, column=1, sticky=tk.W)
        self.par_label = ttk.Label(frame, text=f"{self.par_var.get():.2f}")
        self.par_label.grid(row=3, column=2)
        par_slider.configure(command=lambda v: self.par_label.configure(text=f"{float(v):.2f}"))
        
        # Max Improvisations Slider
        ttk.Label(frame, text="Maximum Improvisations:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.max_imp_var = tk.IntVar(value=self.harmony_search.max_improvisations)
        max_imp_slider = ttk.Scale(frame, from_=50, to=500, variable=self.max_imp_var, 
                                  orient=tk.HORIZONTAL, length=200)
        max_imp_slider.grid(row=4, column=1, sticky=tk.W)
        ttk.Label(frame, textvariable=self.max_imp_var).grid(row=4, column=2)
        
        # Complexity Slider
        ttk.Label(frame, text="Music Complexity:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.complexity_var = tk.DoubleVar(value=self.harmony_search.complexity)
        complexity_slider = ttk.Scale(frame, from_=0.1, to=1.0, variable=self.complexity_var, 
                                     orient=tk.HORIZONTAL, length=200)
        complexity_slider.grid(row=5, column=1, sticky=tk.W)
        self.complexity_label = ttk.Label(frame, text=f"{self.complexity_var.get():.2f}")
        self.complexity_label.grid(row=5, column=2)
        complexity_slider.configure(command=lambda v: self.complexity_label.configure(text=f"{float(v):.2f}"))
        
        # Explanation
        explanation_text = (
            "HMS: Higher values provide more memory but slow down convergence\n"
            "HMCR: Higher values favor using existing patterns from memory\n"
            "PAR: Higher values introduce more variations in pitch\n"
            "Improvisations: More iterations can improve quality but take longer\n"
            "Complexity: Higher values create more adventurous, less predictable music"
        )
        explanation = ttk.Label(frame, text=explanation_text, wraplength=400, 
                              justify=tk.LEFT, padding=(20, 20))
        explanation.grid(row=6, column=0, columnspan=3, pady=20, sticky=tk.W)
        
    def _create_music_tab(self, parent):
        # Create frame with padding
        frame = ttk.Frame(parent, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Music Parameters", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Key Selection
        ttk.Label(frame, text="Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        keys = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
        self.key_var = tk.StringVar(value=self.harmony_search.key)
        key_combo = ttk.Combobox(frame, textvariable=self.key_var, values=keys, width=10)
        key_combo.grid(row=1, column=1, sticky=tk.W)
        
        # Scale Type
        ttk.Label(frame, text="Scale Type:").grid(row=2, column=0, sticky=tk.W, pady=5)
        scales = ['major', 'minor', 'pentatonic', 'blues']
        self.scale_type_var = tk.StringVar(value=self.harmony_search.scale_type)
        scale_combo = ttk.Combobox(frame, textvariable=self.scale_type_var, values=scales, width=10)
        scale_combo.grid(row=2, column=1, sticky=tk.W)
        
        # BPM
        ttk.Label(frame, text="Tempo (BPM):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.tempo_var = tk.IntVar(value=self.harmony_search.tempo)
        tempo_slider = ttk.Scale(frame, from_=60, to=180, variable=self.tempo_var, 
                                orient=tk.HORIZONTAL, length=200)
        tempo_slider.grid(row=3, column=1, sticky=tk.W)
        ttk.Label(frame, textvariable=self.tempo_var).grid(row=3, column=2)
        
        # Measures
        ttk.Label(frame, text="Number of Measures:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.measures_var = tk.IntVar(value=self.harmony_search.measures)
        measures_slider = ttk.Scale(frame, from_=4, to=16, variable=self.measures_var, 
                                   orient=tk.HORIZONTAL, length=200)
        measures_slider.grid(row=4, column=1, sticky=tk.W)
        ttk.Label(frame, textvariable=self.measures_var).grid(row=4, column=2)
        
        # Instrument
        ttk.Label(frame, text="Instrument:").grid(row=5, column=0, sticky=tk.W, pady=5)
        instruments = [
            "Piano", "Acoustic Guitar", "Electric Guitar", "Bass", "Violin", 
            "Cello", "Flute", "Trumpet", "Saxophone", "Synth Lead"
        ]
        instrument_values = [0, 24, 27, 32, 40, 42, 73, 56, 66, 80]  # MIDI program numbers
        self.instrument_var = tk.StringVar(value=instruments[self.harmony_search.instrument])
        instrument_combo = ttk.Combobox(frame, textvariable=self.instrument_var, 
                                       values=instruments, width=15)
        instrument_combo.grid(row=5, column=1, sticky=tk.W)
        
        # Note Duration
        ttk.Label(frame, text="Note Duration:").grid(row=6, column=0, sticky=tk.W, pady=5)
        durations = ["Whole (1)", "Half (1/2)", "Quarter (1/4)", "Eighth (1/8)", "Sixteenth (1/16)"]
        duration_values = [1.0, 0.5, 0.25, 0.125, 0.0625]
        current_duration = self.harmony_search.note_duration
        current_idx = duration_values.index(current_duration) if current_duration in duration_values else 2
        self.duration_var = tk.StringVar(value=durations[current_idx])
        duration_combo = ttk.Combobox(frame, textvariable=self.duration_var, 
                                     values=durations, width=15)
        duration_combo.grid(row=6, column=1, sticky=tk.W)
        
        # Progression Style
        ttk.Label(frame, text="Chord Progression Style:").grid(row=7, column=0, sticky=tk.W, pady=5)
        progression_styles = ["pop", "jazz", "classical"]
        self.progression_var = tk.StringVar(value=self.harmony_search.progression_style)
        progression_combo = ttk.Combobox(frame, textvariable=self.progression_var, 
                                        values=progression_styles, width=15)
        progression_combo.grid(row=7, column=1, sticky=tk.W)
        
        # Rhythm Style
        ttk.Label(frame, text="Rhythm Style:").grid(row=8, column=0, sticky=tk.W, pady=5)
        rhythm_styles = ["simple", "syncopated", "complex", "waltz", "swing"]
        self.rhythm_var = tk.StringVar(value=self.harmony_search.rhythm_style)
        rhythm_combo = ttk.Combobox(frame, textvariable=self.rhythm_var, 
                                   values=rhythm_styles, width=15)
        rhythm_combo.grid(row=8, column=1, sticky=tk.W)
        
        # Explanation
        explanation_text = (
            "These settings control the musical qualities of the generated piece.\n"
            "Experiment with different combinations to create diverse musical styles."
        )
        explanation = ttk.Label(frame, text=explanation_text, wraplength=400, 
                              justify=tk.LEFT, padding=(20, 20))
        explanation.grid(row=9, column=0, columnspan=3, pady=20, sticky=tk.W)
        
    def _create_output_tab(self, parent):
        # Create frame with padding
        frame = ttk.Frame(parent, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Generated Music", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status area
        self.output_text = tk.Text(frame, height=10, width=60, wrap=tk.WORD)
        self.output_text.grid(row=1, column=0, columnspan=2, pady=10)
        self.output_text.insert(tk.END, "Click 'Generate Music' to create a new piece using harmony search.")
        self.output_text.config(state=tk.DISABLED)
        
        # Progress bar
        ttk.Label(frame, text="Generation Progress:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, 
                                          orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress_bar.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Stats
        self.stats_frame = ttk.LabelFrame(frame, text="Music Statistics", padding=10)
        self.stats_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=tk.W+tk.E)
        
        self.stats_labels = {}
        stats = [
            ("Fitness Score", "fitness"), 
            ("Unique Notes", "unique_notes"),
            ("Chord Alignment", "chord_alignment"),
            ("Note/Rest Ratio", "note_rest_ratio")
        ]
        
        for i, (label, key) in enumerate(stats):
            ttk.Label(self.stats_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            self.stats_labels[key] = ttk.Label(self.stats_frame, text="--")
            self.stats_labels[key].grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            
    def update_output_text(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state=tk.DISABLED)
        self.root.update()
        
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update()
        
    def update_stats(self, stats):
        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].config(text=str(value))
        
    def start_generation(self):
        # Update parameters from UI
        self.update_parameters()
        
        # Reset progress
        self.progress_var.set(0)
        self.update_output_text("Generating music using harmony search algorithm...")
        
        # Start generation in a separate thread
        self.generation_thread = threading.Thread(target=self.run_generation)
        self.generation_thread.daemon = True
        self.generation_thread.start()
        
    def update_parameters(self):
        # Get values from UI and update harmony search object
        self.harmony_search.set_parameters(
            HMS=self.hms_var.get(),
            HMCR=self.hmcr_var.get(),
            PAR=self.par_var.get(),
            max_improvisations=self.max_imp_var.get(),
            key=self.key_var.get(),
            scale_type=self.scale_type_var.get(),
            tempo=self.tempo_var.get(),
            measures=self.measures_var.get(),
            complexity=self.complexity_var.get(),
            progression_style=self.progression_var.get(),
            rhythm_style=self.rhythm_var.get()
        )
        
        # Handle instrument
        instruments = ["Piano", "Acoustic Guitar", "Electric Guitar", "Bass", "Violin", 
                     "Cello", "Flute", "Trumpet", "Saxophone", "Synth Lead"]
        instrument_values = [0, 24, 27, 32, 40, 42, 73, 56, 66, 80]
        selected_instrument = self.instrument_var.get()
        if selected_instrument in instruments:
            idx = instruments.index(selected_instrument)
            self.harmony_search.instrument = instrument_values[idx]
            
        # Handle note duration
        durations = ["Whole (1)", "Half (1/2)", "Quarter (1/4)", "Eighth (1/8)", "Sixteenth (1/16)"]
        duration_values = [1.0, 0.5, 0.25, 0.125, 0.0625]
        selected_duration = self.duration_var.get()
        if selected_duration in durations:
            idx = durations.index(selected_duration)
            self.harmony_search.note_duration = duration_values[idx]
        
    def run_generation(self):
        try:
            # Generate music
            for i in range(10):  # Simulate progress updates
                self.update_progress((i+1) * 10)
                time.sleep(0.1)
                
            # Generate the actual music
            self.harmony_search.generate_music()
            
            # Generate MIDI
            self.current_midi_file = self.harmony_search.generate_midi()
            
            # Calculate stats
            if self.harmony_search.best_harmony:
                melody = self.harmony_search.best_harmony
                non_rest_notes = [note['note'] for note in melody if not note['is_rest']]
                unique_notes = len(set(non_rest_notes))
                note_rest_ratio = sum(1 for note in melody if not note['is_rest']) / len(melody)
                
                stats = {
                    "fitness": f"{self.harmony_search.harmony_memory[0]['fitness']:.2f}",
                    "unique_notes": str(unique_notes),
                    "chord_alignment": "Good" if self.harmony_search.harmony_memory[0]['fitness'] > 50 else "Average",
                    "note_rest_ratio": f"{note_rest_ratio:.2f}"
                }
                
                self.root.after(0, lambda: self.update_stats(stats))
            
            # Update UI
            self.root.after(0, lambda: self.status_var.set("Generation Complete"))
            self.root.after(0, lambda: self.update_output_text(
                "Music generation complete!\n\n"
                "The harmony search algorithm created music based on your parameters.\n"
                "Click 'Play/Stop' to listen or 'Save MIDI File' to export."
            ))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: self.update_output_text(f"Error during generation: {str(e)}"))
            
    def toggle_play(self):
        if self.current_midi_file and os.path.exists(self.current_midi_file):
            if not self.is_playing:
                try:
                    pygame.mixer.music.load(self.current_midi_file)
                    pygame.mixer.music.play()
                    self.is_playing = True
                    self.status_var.set("Playing...")
                except Exception as e:
                    messagebox.showerror("Playback Error", f"Error playing MIDI: {str(e)}")
            else:
                pygame.mixer.music.stop()
                self.is_playing = False
                self.status_var.set("Stopped")
        else:
            messagebox.showinfo("No Music", "Please generate music first.")
            
    def save_midi(self):
        if self.current_midi_file and os.path.exists(self.current_midi_file):
            save_path = filedialog.asksaveasfilename(
                defaultextension=".mid",
                filetypes=[("MIDI files", "*.mid"), ("All files", "*.*")],
                title="Save MIDI File"
            )
            
            if save_path:
                try:
                    # Copy the file to the chosen location
                    with open(self.current_midi_file, 'rb') as src_file:
                        with open(save_path, 'wb') as dest_file:
                            dest_file.write(src_file.read())
                    messagebox.showinfo("Success", f"MIDI file saved to {save_path}")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Error saving MIDI file: {str(e)}")
        else:
            messagebox.showinfo("No Music", "Please generate music first.")


def main():
    root = tk.Tk()
    app = MusicGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()