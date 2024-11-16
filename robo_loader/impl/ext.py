import sounddevice as sd
import numpy as np

def get_sound_level(duration=0.5, sample_rate=44100):
    # Record audio for the specified duration
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()  # Wait until the recording is complete
    
    # Compute RMS of the recording
    rms = np.sqrt(np.mean(recording**2))
    
    # Convert RMS to dB level
    db_level = 20 * np.log10(rms + 1e-9)  # Adding a small value to avoid log(0)
    
    return db_level

if __name__ == "__main__":    
    # Example usage
    sound_level = get_sound_level()
    print(f"Sound level: {sound_level:.2f} dB")
