from harmony_search_music_generator import HarmonySearchMusic
from multi_instrument_extension import MultiInstrumentGenerator

def generate_basic_piece():
    """Generate a basic piece with default settings"""
    print("Generating music with default settings...")
    try:
        hs = HarmonySearchMusic(
            key='C',
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
        
        midi_file = hs.generate_music()
        print(f"Basic piece generated: {midi_file}")
        print(f"Fitness score: {hs.best_fitness:.2f}")
        
        return hs
    except Exception as e:
        print(f"Error generating basic piece: {e}")
        return None

def generate_customized_piece():
    """Generate a piece with custom settings"""
    print("\nGenerating customized music...")
    try:
        hs = HarmonySearchMusic(
            key='A',
            mode='minor',
            measures=12,
            beats_per_measure=3,  # 3/4 time signature
            tempo=90,
            hms=40,
            hmcr=0.85,
            par=0.35,
            bw=0.15,
            max_iter=800
        )
        
        midi_file = hs.generate_music()
        print(f"Custom piece generated: {midi_file}")
        print(f"Fitness score: {hs.best_fitness:.2f}")
        
        return hs
    except Exception as e:
        print(f"Error generating customized piece: {e}")
        return None

def generate_multi_instrument_pieces():
    """Generate pieces with multiple instruments"""
    try:
        # First create a basic harmony
        hs = HarmonySearchMusic(
            key='D',
            mode='major',
            measures=16,
            beats_per_measure=4,
            tempo=110,
            max_iter=500  # Reduced iterations for testing
        )
        
        # Generate the harmony
        harmony = hs.optimize()
        
        # Create arrangements with different instrument combinations
        multi_gen = MultiInstrumentGenerator(hs)
        
        try:
            print("\nGenerating classical arrangement...")
            classical_file = multi_gen.generate_full_arrangement(harmony, style='classical')
            print(f"Classical arrangement: {classical_file}")
        except Exception as e:
            print(f"Error generating classical arrangement: {e}")
        
        try:
            print("\nGenerating jazz arrangement...")
            jazz_file = multi_gen.generate_full_arrangement(harmony, style='jazz')
            print(f"Jazz arrangement: {jazz_file}")
        except Exception as e:
            print(f"Error generating jazz arrangement: {e}")
        
        try:
            print("\nGenerating rock arrangement...")
            rock_file = multi_gen.generate_full_arrangement(harmony, style='rock')
            print(f"Rock arrangement: {rock_file}")
        except Exception as e:
            print(f"Error generating rock arrangement: {e}")
        
        print("\nGeneration complete!")
        
    except Exception as e:
        print(f"Error in multi-instrument generation: {e}")

if __name__ == "__main__":
    # Generate a basic piece
    hs_basic = generate_basic_piece()
    
    # Generate a customized piece
    hs_custom = generate_customized_piece()
    
    # Generate multi-instrument arrangements
    generate_multi_instrument_pieces()