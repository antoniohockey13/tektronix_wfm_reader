
import os
# import time
import numpy as np
from wfm2readframe import wfm2readframe
import click
# import matplotlib.pyplot as plt
import re
# from collections import defaultdict 
import ROOT
from array import array


def extract_waveforms(input_file):
	"""
	Extract waveforms from a Tektronix WFM file. Using wfm2readframe to read frames.
	Args:
		input_file (str): Path to the WFM file.
	Returns:
		Osci_Data (np.ndarray): 2D array with shape (Events_Found, Nsamples) containing waveform data.
		time (np.ndarray): 1D array containing time values.
	"""
	
	# --- Read the first frame just to get waveform length and number of events ---
	waveform, time, info, _, _ = wfm2readframe(input_file, 1)
	
	Events_Found = info["N"]
	Nsamples = len(waveform)
	
	print(f"Found {Events_Found} events, each with {Nsamples} samples.")
	
	# --- Prepare data containers ---
	Osci_Data = np.zeros((Events_Found, Nsamples), dtype=float)	
	# --- Iterate over all events (frames) ---
	for WaveForm_Index in range(1, Events_Found + 1):
		current_waveform, _, _, _, _ = wfm2readframe(input_file, WaveForm_Index)
		Osci_Data[WaveForm_Index - 1, :] = current_waveform
		# print(f"Frame {WaveForm_Index}/{Events_Found} read.")
	
	print("All waveforms loaded successfully.")
	return Osci_Data, time

def get_size(input_folder):
	"""
	Get the number of samples in the waveform by reading the first file in the folder.
	Args:
		input_folder (str): Path to the folder containing WFM files.
	Returns:
		int: Number of samples in the waveform.
	"""
	# Extract first file to get waveform size
	for file in os.listdir(input_folder):
		pattern = re.compile(r'cycle_(\d+)_ch(\d+).wfm$')
		match = pattern.search(file)
		if match:
			input_file = os.path.join(input_folder, file)
			_, time, _, _, _ = wfm2readframe(input_file, 1)
			return len(time)

@click.command()
@click.option('-i', 'input_folder')
@click.option('-o', 'output_folder', type=click.Path(), default=".")
@click.option('-c', 'channel', type=int, default=1, help="Channel number to process")
def main(input_folder, output_folder, channel):
	"""
	Process WFM files in the input folder and save waveforms to a ROOT file.
	Args:
		input_folder (str): Path to the folder containing WFM files.
		output_folder (str): Path to save the output ROOT file.
		channel (int): Channel number to process.
	"""
	print(f"Input folder: {input_folder}")
	print(f"Output folder: {output_folder}")
	print(f"Processing channel: {channel}")
	# voltages_dict = defaultdict(dict)

	# Create ROOT branches
	root_file = ROOT.TFile(f"{output_folder}/waveforms_ch{channel}.root", "RECREATE")
	tree = ROOT.TTree("waveforms", "Waveform Data")
	
	# size = get_size(input_folder)
	time_vec = ROOT.std.vector('double')()
	voltage_vec = ROOT.std.vector('double')()
	event_number = array('i', [0])

	tree.Branch("event_number", event_number, "event_number/I")
	tree.Branch("time", time_vec)
	tree.Branch("voltage", voltage_vec)

	global_event_counter = 0
	pattern = re.compile(rf'cycle_(\d+)_ch{channel}.wfm$')
	print(f"Using pattern: {pattern.pattern}")
	# Sort files to ensure consistent order
	for file in sorted(os.listdir(input_folder)):
		print(f"Processing file: {file}")
		match = pattern.search(file)
		if not match:
			print(f"Input filename, {file}, does not match expected pattern 'cycle<NUM>_ch{channel}.wfm'")
			continue

		cycle_num = match.group(1)
		print(f"Extracted cycle number: {cycle_num}, channel: {channel}")
		input_file = os.path.join(input_folder, file)
		osci_data, time = extract_waveforms(input_file)
		
		# Iterar sobre todos los eventos (frames)
		for waveform in osci_data:
			time_vec.clear()
			voltage_vec.clear()
			
			for t, v in zip(time, waveform):
				time_vec.push_back(float(t))
				voltage_vec.push_back(float(v))

			event_number[0] = int(global_event_counter)
			tree.Fill()
			print(f"Event number = {global_event_counter}")
			global_event_counter += 1

	root_file.Write()
	root_file.Close()
	print(f"Data saved to {output_folder}/waveforms_ch{channel}.root")


if __name__ == "__main__":
	main()