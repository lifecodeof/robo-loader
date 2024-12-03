import sounddevice as sd
import numpy as np

def get_sound_level(duration=0.5, sample_rate=44100, reference_rms=1.0):
    """
    Measure sound level in dB.
    :param duration: Duration of the audio recording in seconds
    :param sample_rate: Sampling rate for audio
    :param reference_rms: Reference RMS level for 0 dB
    :return: Sound level in decibels
    """
    # Record audio for the specified duration
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float64')
    sd.wait()  # Wait until the recording is complete
    
    # Compute RMS of the recording
    rms = np.sqrt(np.mean(recording**2))
    
    # Avoid division by zero or log of zero
    if rms == 0:
        rms = 1e-9  # Small value to avoid math errors
    
    # Convert RMS to dB level using the reference RMS
    db_level = 20 * np.log10(rms / reference_rms)
    
    return abs(db_level * 20)

if __name__ == "__main__":    
    # Example usage with a reference RMS
    reference_rms = 0.1  # Set this based on your microphone calibration
    sound_level = get_sound_level(reference_rms=reference_rms)
    print(f"Sound level: {sound_level:.2f} dB")
