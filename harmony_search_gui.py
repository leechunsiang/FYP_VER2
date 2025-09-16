import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import time
from harmony_search_music_generator import HarmonySearchMusic
from multi_instrument_extension import MultiInstrumentGenerator

class HarmonySearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Harmony Search Music Generator")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Set theme
        style = ttk.Style()
        try:
            root.tk.call("source", "azure.tcl")
            style.theme_use("azure")
        except tk.TclError:
            style.theme_use("clam")  # Fallback theme
            
        # Main container
        main_container = ttk.Frame(root, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_control = ttk.Notebook(main_container)
        
        # Basic tab
        self.basic_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.basic_tab, text="Basic Generation")
        
        # Advanced tab
        self.advanced_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.advanced_tab, text="Advanced Settings")
        
        # Multi-instrument tab
        self.multi_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.multi_tab, text="Multi-Instrument")
        
        self.tab_control.pack(expand=True, fill=tk.BOTH)
        
        # Initialize variables
        self.init_variables()
        
        # Setup UI components
        self.setup_basic_tab()
        self.setup_advanced_tab()
        self.setup_multi_instrument_tab()
        
        # Status bar at the bottom
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=2)
        
        # Instance variables
        self.hs_instance = None
        self.current_harmony = None
        
    def init_variables(self):
        # Musical parameters
        self.key_var = tk.StringVar(value="C")
        self.mode_var = tk.StringVar(value="major")
        self.measures_var = tk.IntVar(value=8)
        self.beats_per_measure_var = tk.IntVar(value=4)
        self.tempo_var = tk.IntVar(value=120)
        
        # Algorithm parameters
        self.hms_var = tk.IntVar(value=30)
        self.hmcr_var = tk.DoubleVar(value=0.9)
        self.par_var = tk.DoubleVar(value=0.3)
        self.bw_var = tk.DoubleVar(value=0.1)
        self.max_iter_var = tk.IntVar(value=500)
        
        # Output options
        self.output_format_var = tk.StringVar(value="midi")
        self.output_dir_var = tk.StringVar(value=os.path.expanduser("~"))
        
        # Multi-instrument options
        self.style_var = tk.StringVar(value="classical")
        
    def setup_basic_tab(self):
        # Create frame with some padding
        frame = ttk.LabelFrame(self.basic_tab, text="Musical Parameters", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Key selection
        ttk.Label(frame, text="Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        keys = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
        key_dropdown = ttk.Combobox(frame, textvariable=self.key_var, values=keys, width=5)
        key_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Mode selection
        ttk.Label(frame, text="Mode:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20,0))
        modes = ["major", "minor"]
        mode_dropdown = ttk.Combobox(frame, textvariable=self.mode_var, values=modes, width=8)
        mode_dropdown.grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Measures
        ttk.Label(frame, text="Measures:").grid(row=1, column=0, sticky=tk.W, pady=5)
        measures_scale = ttk.Scale(frame, from_=4, to=32, variable=self.measures_var, 
                                   orient=tk.HORIZONTAL, length=200)
        measures_scale.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(frame, textvariable=self.measures_var).grid(row=1, column=3, sticky=tk.W)
        
        # Time signature
        ttk.Label(frame, text="Beats per measure:").grid(row=2, column=0, sticky=tk.W, pady=5)
        time_signatures = [2, 3, 4, 6, 9, 12]
        time_sig_dropdown = ttk.Combobox(frame, textvariable=self.beats_per_measure_var, 
                                        values=time_signatures, width=5)
        time_sig_dropdown.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Tempo
        ttk.Label(frame, text="Tempo:").grid(row=3, column=0, sticky=tk.W, pady=5)
        tempo_scale = ttk.Scale(frame, from_=40, to=200, variable=self.tempo_var, 
                               orient=tk.HORIZONTAL, length=200)
        tempo_scale.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(frame, textvariable=self.tempo_var).grid(row=3, column=3, sticky=tk.W)
        
        # Generation frame
        gen_frame = ttk.LabelFrame(self.basic_tab, text="Generation", padding=10)
        gen_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Output directory
        ttk.Label(gen_frame, text="Output directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(gen_frame, textvariable=self.output_dir_var, width=40).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Button(gen_frame, text="Browse...", command=self.browse_output_dir).grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        
        # Output format
        ttk.Label(gen_frame, text="Output format:").grid(row=1, column=0, sticky=tk.W, pady=5)
        formats = ["midi", "musicxml"]
        format_dropdown = ttk.Combobox(gen_frame, textvariable=self.output_format_var, values=formats, width=10)
        format_dropdown.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Generate button
        generate_btn = ttk.Button(gen_frame, text="Generate Music", command=self.generate_music)
        generate_btn.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.basic_tab, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results text area
        self.results_text = tk.Text(results_frame, wrap=tk.WORD, height=10)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar to results
        results_scrollbar = ttk.Scrollbar(self.results_text, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def setup_advanced_tab(self):
        # Algorithm parameters frame
        algo_frame = ttk.LabelFrame(self.advanced_tab, text="Harmony Search Algorithm Parameters", padding=10)
        algo_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Harmony Memory Size (HMS)
        ttk.Label(algo_frame, text="Harmony Memory Size (HMS):").grid(row=0, column=0, sticky=tk.W, pady=5)
        hms_scale = ttk.Scale(algo_frame, from_=10, to=100, variable=self.hms_var, 
                             orient=tk.HORIZONTAL, length=200)
        hms_scale.grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(algo_frame, textvariable=self.hms_var).grid(row=0, column=2, sticky=tk.W)
        
        # Harmony Memory Considering Rate (HMCR)
        ttk.Label(algo_frame, text="Harmony Memory Considering Rate (HMCR):").grid(row=1, column=0, sticky=tk.W, pady=5)
        hmcr_scale = ttk.Scale(algo_frame, from_=0.1, to=1.0, variable=self.hmcr_var, 
                              orient=tk.HORIZONTAL, length=200)
        hmcr_scale.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(algo_frame, textvariable=self.hmcr_var).grid(row=1, column=2, sticky=tk.W)
        
        # Pitch Adjusting Rate (PAR)
        ttk.Label(algo_frame, text="Pitch Adjusting Rate (PAR):").grid(row=2, column=0, sticky=tk.W, pady=5)
        par_scale = ttk.Scale(algo_frame, from_=0.1, to=1.0, variable=self.par_var, 
                             orient=tk.HORIZONTAL, length=200)
        par_scale.grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Label(algo_frame, textvariable=self.par_var).grid(row=2, column=2, sticky=tk.W)
        
        # Bandwidth (BW)
        ttk.Label(algo_frame, text="Bandwidth (BW):").grid(row=3, column=0, sticky=tk.W, pady=5)
        bw_scale = ttk.Scale(algo_frame, from_=0.01, to=0.5, variable=self.bw_var, 
                            orient=tk.HORIZONTAL, length=200)
        bw_scale.grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Label(algo_frame, textvariable=self.bw_var).grid(row=3, column=2, sticky=tk.W)
        
        # Max Iterations
        ttk.Label(algo_frame, text="Maximum Iterations:").grid(row=4, column=0, sticky=tk.W, pady=5)
        iter_scale = ttk.Scale(algo_frame, from_=100, to=2000, variable=self.max_iter_var, 
                              orient=tk.HORIZONTAL, length=200)
        iter_scale.grid(row=4, column=1, sticky=tk.W, pady=5)
        ttk.Label(algo_frame, textvariable=self.max_iter_var).grid(row=4, column=2, sticky=tk.W)
        
        # Description frame
        desc_frame = ttk.LabelFrame(self.advanced_tab, text="Parameter Descriptions", padding=10)
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Description text
        desc_text = tk.Text(desc_frame, wrap=tk.WORD, height=12)
        desc_text.pack(fill=tk.BOTH, expand=True)
        
        # Add description content
        description = """
Harmony Memory Size (HMS): Number of solution vectors in the harmony memory. 
Higher values explore more possibilities but slow down the algorithm.

Harmony Memory Considering Rate (HMCR): Probability of selecting a component from harmony memory. 
Higher values favor exploitation of existing harmonies.

Pitch Adjusting Rate (PAR): Probability of adjusting pitch after selecting from harmony memory.
Higher values increase local improvements but may cause premature convergence.

Bandwidth (BW): Controls the amount of adjustment when PAR is applied.
Higher values make larger adjustments, increasing exploration.

Maximum Iterations: Number of improvisation steps before termination.
Higher values produce better results but take longer to complete.
"""
        desc_text.insert(tk.END, description)
        desc_text.config(state=tk.DISABLED)  # Make read-only
        
        # Add scrollbar
        desc_scrollbar = ttk.Scrollbar(desc_text, command=desc_text.yview)
        desc_text.configure(yscrollcommand=desc_scrollbar.set)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def setup_multi_instrument_tab(self):
        # Style selection frame
        style_frame = ttk.LabelFrame(self.multi_tab, text="Style Selection", padding=10)
        style_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Style dropdown
        ttk.Label(style_frame, text="Music Style:").grid(row=0, column=0, sticky=tk.W, pady=5)
        styles = ["classical", "jazz", "rock", "pop"]
        style_dropdown = ttk.Combobox(style_frame, textvariable=self.style_var, values=styles, width=15)
        style_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Style description
        ttk.Label(style_frame, text="Instruments:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.instruments_label = ttk.Label(style_frame, text="violin, piano, cello")
        self.instruments_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Update instruments when style changes
        style_dropdown.bind("<<ComboboxSelected>>", self.update_instruments_label)
        
        # Multi-instrument generation frame
        multi_gen_frame = ttk.LabelFrame(self.multi_tab, text="Multi-Instrument Generation", padding=10)
        multi_gen_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Output directory
        ttk.Label(multi_gen_frame, text="Output directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(multi_gen_frame, textvariable=self.output_dir_var, width=40).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Button(multi_gen_frame, text="Browse...", command=self.browse_output_dir).grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        
        # Generate button
        multi_generate_btn = ttk.Button(multi_gen_frame, text="Generate Multi-Instrument Arrangement", 
                                      command=self.generate_multi_instrument)
        multi_generate_btn.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Style description frame
        style_desc_frame = ttk.LabelFrame(self.multi_tab, text="Style Descriptions", padding=10)
        style_desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Style descriptions text
        style_desc_text = tk.Text(style_desc_frame, wrap=tk.WORD, height=12)
        style_desc_text.pack(fill=tk.BOTH, expand=True)
        
        # Add style description content
        style_description = """
Classical: A traditional orchestral arrangement featuring violin for melody, piano for harmony, and cello for bass. Emphasizes proper voice leading and common practice period harmonic progressions.

Jazz: A jazz combo arrangement with saxophone playing the melody, piano providing chord voicings, and acoustic bass handling the walking bass line. Features extended harmonies and swing rhythm.

Rock: A rock band arrangement with electric guitar for lead melody, rhythm guitar for chords, and electric bass providing the foundation. Features power chords and rhythmic patterns typical of rock music.

Pop: A contemporary pop arrangement with piano carrying the melody, acoustic guitar providing rhythmic strumming patterns, and electric bass with a simple but solid bass line.
"""
        style_desc_text.insert(tk.END, style_description)
        style_desc_text.config(state=tk.DISABLED)  # Make read-only
        
        # Add scrollbar
        style_desc_scrollbar = ttk.Scrollbar(style_desc_text, command=style_desc_text.yview)
        style_desc_text.configure(yscrollcommand=style_desc_scrollbar.set)
        style_desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def update_instruments_label(self, event=None):
        """Update the instruments label based on selected style"""
        style = self.style_var.get()
        if style == "classical":
            self.instruments_label.config(text="violin, piano, cello")
        elif style == "jazz":
            self.instruments_label.config(text="saxophone, piano, acoustic bass")
        elif style == "rock":
            self.instruments_label.config(text="electric guitar, electric guitar, electric bass")
        elif style == "pop":
            self.instruments_label.config(text="piano, acoustic guitar, electric bass")
    
    def browse_output_dir(self):
        """Open file dialog to select output directory"""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:  # If a directory was selected
            self.output_dir_var.set(directory)
    
    def generate_music(self):
        """Generate basic music based on current settings"""
        # Disable all tabs during generation
        for tab_id in range(self.tab_control.index("end")):
            self.tab_control.tab(tab_id, state="disabled")
            
        self.status_var.set("Initializing music generation...")
        self.progress_var.set(0)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Starting music generation...\n")
        
        # Start generation in a separate thread to keep UI responsive
        threading.Thread(target=self._generate_music_thread, daemon=True).start()
    
    def _generate_music_thread(self):
        """Thread function for music generation to avoid freezing UI"""
        try:
            # Get all parameters from UI
            key = self.key_var.get()
            mode = self.mode_var.get()
            measures = self.measures_var.get()
            beats_per_measure = self.beats_per_measure_var.get()
            tempo = self.tempo_var.get()
            
            hms = self.hms_var.get()
            hmcr = self.hmcr_var.get()
            par = self.par_var.get()
            bw = self.bw_var.get()
            max_iter = self.max_iter_var.get()
            
            output_format = self.output_format_var.get()
            output_dir = self.output_dir_var.get()
            
            # Update status
            self._update_status("Creating Harmony Search instance...")
            
            # Create harmony search instance with custom progress callback
            self.hs_instance = HarmonySearchMusic(
                key=key,
                mode=mode,
                measures=measures,
                beats_per_measure=beats_per_measure,
                tempo=tempo,
                hms=hms,
                hmcr=hmcr,
                par=par,
                bw=bw,
                max_iter=max_iter
            )
            
            # Update status and progress
            self._update_status("Initializing harmony memory...")
            self._update_progress(10)
            
            # Run optimization with progress tracking
            self._update_status("Running optimization...")
            
            # We need to patch the optimize method to report progress
            original_optimize = self.hs_instance.optimize
            
            def optimize_with_progress():
                # Initialize harmony memory
                self.hs_instance.initialize_harmony_memory()
                self._update_progress(20)
                
                # Prepare for iterations
                progress_step = 60 / self.hs_instance.max_iter  # 60% of progress bar for iterations
                
                # Run iterations
                self.hs_instance.best_harmony = None
                self.hs_instance.best_fitness = -float('inf')
                
                for iteration in range(self.hs_instance.max_iter):
                    # Check if the thread should stop
                    if not getattr(threading.current_thread(), "do_run", True):
                        break
                        
                    # Improvise and update harmony memory
                    new_harmony = self.hs_instance.improvise_new_harmony()
                    updated = self.hs_instance.update_harmony_memory(new_harmony)
                    
                    # Update best harmony if needed
                    if new_harmony['fitness'] > self.hs_instance.best_fitness:
                        self.hs_instance.best_harmony = new_harmony.copy()
                        self.hs_instance.best_fitness = new_harmony['fitness']
                        
                        # Report significant improvements
                        if iteration % 100 == 0 or (updated and iteration % 10 == 0):
                            self._append_to_results(f"Iteration {iteration}, Fitness: {self.hs_instance.best_fitness:.2f}")
                    
                    # Update progress every few iterations
                    if iteration % 10 == 0:
                        current_progress = 20 + (iteration * progress_step)
                        self._update_progress(min(80, current_progress))
                        self._update_status(f"Optimizing: iteration {iteration}/{self.hs_instance.max_iter}")
                
                self._update_progress(80)
                return self.hs_instance.best_harmony
            
            # Replace optimize method temporarily
            self.hs_instance.optimize = optimize_with_progress
            
            # Run optimization
            self.current_harmony = self.hs_instance.optimize()
            
            # Restore original method
            self.hs_instance.optimize = original_optimize
            
            # Generate output file
            self._update_status("Generating MIDI file...")
            self._update_progress(90)
            
            # Prepare output filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"harmony_search_{key}_{mode}_{timestamp}.{output_format}"
            output_path = os.path.join(output_dir, filename)
            
            # Generate music file
            output_file = self.hs_instance.generate_music(output_format=output_format, filename=output_path)
            
            # Complete
            self._update_status("Music generation complete!")
            self._update_progress(100)
            
            # Display results
            self._append_to_results(f"\nMusic generation successful!")
            self._append_to_results(f"Fitness score: {self.hs_instance.best_fitness:.2f}")
            self._append_to_results(f"Output file: {output_file}")
            
            # Ask if user wants to open the directory
            if messagebox.askyesno("Generation Complete", 
                                  f"Music file saved as:\n{output_file}\n\nOpen containing folder?"):
                self._open_folder(os.path.dirname(output_file))
            
        except Exception as e:
            self._update_status(f"Error: {str(e)}")
            self._append_to_results(f"\nError during generation: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during music generation:\n{str(e)}")
        finally:
            # Re-enable tabs
            for tab_id in range(self.tab_control.index("end")):
                self.tab_control.tab(tab_id, state="normal")
    
    def generate_multi_instrument(self):
        """Generate multi-instrument arrangement based on current settings"""
        # Disable all tabs during generation
        for tab_id in range(self.tab_control.index("end")):
            self.tab_control.tab(tab_id, state="disabled")
            
        self.status_var.set("Initializing multi-instrument arrangement...")
        self.progress_var.set(0)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Starting multi-instrument arrangement...\n")
        
        # Start generation in a separate thread
        threading.Thread(target=self._generate_multi_instrument_thread, daemon=True).start()
    
    def _generate_multi_instrument_thread(self):
        """Thread function for multi-instrument arrangement generation"""
        try:
            # Check if we need to generate a new harmony first
            if self.hs_instance is None or self.current_harmony is None:
                self._append_to_results("No existing harmony found. Generating a new one first...")
                self._update_status("Generating base harmony...")
                self._update_progress(5)
                
                # Create a new harmony search instance
                self.hs_instance = HarmonySearchMusic(
                    key=self.key_var.get(),
                    mode=self.mode_var.get(),
                    measures=self.measures_var.get(),
                    beats_per_measure=self.beats_per_measure_var.get(),
                    tempo=self.tempo_var.get(),
                    hms=self.hms_var.get(),
                    hmcr=self.hmcr_var.get(),
                    par=self.par_var.get(),
                    bw=self.bw_var.get(),
                    max_iter=self.max_iter_var.get()
                )
                
                # Run optimization (simplified progress reporting)
                self._update_status("Running optimization for base harmony...")
                self._update_progress(10)
                self.current_harmony = self.hs_instance.optimize(verbose=False)
                self._update_progress(40)
                self._append_to_results(f"Base harmony generated with fitness: {self.hs_instance.best_fitness:.2f}")
            
            # Now create the multi-instrument arrangement
            self._update_status("Creating multi-instrument arrangement...")
            self._update_progress(50)
            
            # Get style and output directory
            style = self.style_var.get()
            output_dir = self.output_dir_var.get()
            
            # Prepare filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            key = self.hs_instance.key
            mode = self.hs_instance.mode
            filename = f"{style}_arrangement_{key}_{mode}_{timestamp}.mid"
            output_path = os.path.join(output_dir, filename)
            
            # Create multi-instrument generator
            self._update_status(f"Generating {style} arrangement...")
            multi_gen = MultiInstrumentGenerator(self.hs_instance)
            
            # Generate the arrangement
            self._update_progress(70)
            output_file = multi_gen.generate_full_arrangement(
                harmony=self.current_harmony,
                style=style,
                filename=output_path
            )
            
            # Complete
            self._update_status("Arrangement generation complete!")
            self._update_progress(100)
            
            # Display results
            self._append_to_results(f"\nMulti-instrument arrangement successful!")
            self._append_to_results(f"Style: {style}")
            self._append_to_results(f"Output file: {output_file}")
            
            # Ask if user wants to open the directory
            if messagebox.askyesno("Arrangement Complete", 
                                  f"Arrangement saved as:\n{output_file}\n\nOpen containing folder?"):
                self._open_folder(os.path.dirname(output_file))
            
        except Exception as e:
            self._update_status(f"Error: {str(e)}")
            self._append_to_results(f"\nError during arrangement: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during arrangement generation:\n{str(e)}")
        finally:
            # Re-enable tabs
            for tab_id in range(self.tab_control.index("end")):
                self.tab_control.tab(tab_id, state="normal")
    
    def _update_status(self, message):
        """Update status bar message"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def _update_progress(self, value):
        """Update progress bar value"""
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def _append_to_results(self, text):
        """Append text to results with auto-scroll"""
        self.results_text.insert(tk.END, f"{text}\n")
        self.results_text.see(tk.END)  # Scroll to the end
        self.root.update_idletasks()
    
    def _open_folder(self, path):
        """Open folder in file explorer"""
        if os.path.exists(path):
            import platform
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                import subprocess
                subprocess.Popen(["open", path])
            else:  # Linux
                import subprocess
                subprocess.Popen(["xdg-open", path])


if __name__ == "__main__":
    root = tk.Tk()
    app = HarmonySearchGUI(root)
    root.mainloop()