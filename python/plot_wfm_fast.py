# timing_analysis_sps.py
# Joaquim Pinol - 17/7/2025
# Timing analysis of SPS data acquired with Tektronix MSO64B

import numpy as np
from wfm2readframe import wfm2readframe
import matplotlib.pyplot as plt
import click


def extract_waveforms(input_file):

	ch1 = input_file + "_ch1.wfm"
	ch2 = input_file + "_ch2.wfm"
	ch3 = input_file + "_ch3.wfm"
	ch4 = input_file + "_ch4.wfm"

	# --- Read the first frame just to get waveform length and number of events ---
	waveform, time, info, _, _ = wfm2readframe(ch1, 1)
	
	Events_Found = info["N"]
	Nsamples = len(waveform)
	
	print(f"Found {Events_Found} events, each with {Nsamples} samples.")
	
	# --- Prepare data containers ---
	Osci_Data = {
		"ch1": np.zeros((Events_Found, Nsamples), dtype=float),
		"ch2": np.zeros((Events_Found, Nsamples), dtype=float),
		"ch3": np.zeros((Events_Found, Nsamples), dtype=float),
		"ch4": np.zeros((Events_Found, Nsamples), dtype=float),
	}
	# --- Iterate over all events (frames) ---
	for WaveForm_Index in range(1, Events_Found + 1):
		# ch1
		current_waveform, _, _, _, _ = wfm2readframe(ch1, WaveForm_Index)
		Osci_Data["ch1"][WaveForm_Index - 1, :] = current_waveform

		# ch2
		current_waveform, _, _, _, _ = wfm2readframe(ch2, WaveForm_Index)
		Osci_Data["ch2"][WaveForm_Index - 1, :] = current_waveform

		# ch3
		current_waveform, _, _, _, _ = wfm2readframe(ch3, WaveForm_Index)
		Osci_Data["ch3"][WaveForm_Index - 1, :] = current_waveform

		# ch4
		current_waveform, _, _, _, _ = wfm2readframe(ch4, WaveForm_Index)
		Osci_Data["ch4"][WaveForm_Index - 1, :] = current_waveform

		print(f"Frame {WaveForm_Index}/{Events_Found} read.")
	
	print("All waveforms loaded successfully.")
	return Osci_Data, time
@click.command()
@click.option('-i', 'input_file', type=click.Path(), help="Input file path without channel and extension")
def main(input_file):

	Osci_Data, time = extract_waveforms(input_file)

	for ch in range(1, 5):
		print(f"Channel {ch} data shape: {Osci_Data[f'ch{ch}'].shape}")
		# Draw waveform for one event as example
		event = 1
		plt.figure()
		plt.plot(time, Osci_Data[f'ch{ch}'][event, :])
		plt.title(f'Channel {ch} - Event {event}')
		plt.xlabel('Time (s)')
		plt.ylabel('Amplitude (V)')
		plt.grid()
		plt.show()

		# Draw the min (ch 1-3)/ max (ch 4) value of each waveform
		if ch == 4:
			max_values = Osci_Data[f'ch{ch}'].max(axis=1)
			plt.figure()
			plt.plot(max_values, 'o-')
			plt.title(f'Channel {ch} - Max Values per Event')
			plt.xlabel('Event Index')
			plt.ylabel('Max Amplitude (V)')
			plt.grid()
			plt.show()
		else:
			# Draw the min value of each waveform	
			min_values = Osci_Data[f'ch{ch}'].min(axis=1)
			plt.figure()
			plt.plot(min_values, 'o-')
			plt.title(f'Channel {ch} - Min Values per Event')
			plt.xlabel('Event Index')
			plt.ylabel('Min Amplitude (V)')
			plt.grid()
			plt.show()


if __name__ == "__main__":
	main()


