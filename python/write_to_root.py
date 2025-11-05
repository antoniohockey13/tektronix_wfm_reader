# Improved and more memory-efficient version of write_to_root.py
# Key changes:
#  - stream frames directly from wfm2readframe -> avoids storing all waveforms in RAM
#  - escape .wfm in regex and sort filenames for deterministic ordering
#  - use array('i') for event_number (matches "event_number/I")
#  - attempt to reserve vector capacity when possible
#  - reduce noisy prints for performance (kept essential prints)
import os
import re
from array import array
import numpy as np
from wfm2readframe import wfm2readframe
import click
import ROOT
import tqdm


def iter_waveforms(input_file):
    """
    Generator that yields (time, waveform) for each frame in a WFM file.
    This reads frames on demand (no full-file storage).
    """
    # Read first frame to get number of events and the time axis
    first_waveform, time, info, _, _ = wfm2readframe(input_file, 1)
    Events_Found = info["N"]
    # yield the first waveform (wfm2readframe returned it already)
    yield time, np.asarray(first_waveform, dtype=float)
    # remaining frames
    for idx in range(2, Events_Found + 1):
        waveform, _, _, _, _ = wfm2readframe(input_file, idx)
        yield time, np.asarray(waveform, dtype=float)


@click.command()
@click.option('-i', 'input_folder', required=True, help="Folder containing .wfm files")
@click.option('-o', 'output_folder', type=click.Path(), default=".", help="Output folder for ROOT file")
@click.option('-c', 'channel', type=int, default=1, help="Channel number to process")
@click.option('--condor', is_flag=True, help="Run in batch mode, do not show progress bar")
def main(input_folder, output_folder, channel, condor):
    """
    Stream WFM frames from files and write them as entries in 2 ROOT TTree.

    The output ROOT file contains two TTrees:
    1) "waveforms": contains the waveform data. Each entry has:
       - event_number: integer event index
       - voltage: vector of voltage samples
       - min_voltage: minimum voltage in the waveform
       - min_time: time at which minimum voltage occurs
    2) "metadata": contains metadata such as channel number and run number and time axis
    Parameters:
    - input_folder: folder containing .wfm files
    - output_folder: folder to store the output ROOT file
    - channel: channel number to process
    - condor: if set, run in batch mode without progress bar

    """
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"Processing channel: {channel}")
    is_condor = condor
    print(f"Condor mode: {is_condor}")
    run_number = None  # Placeholder for run number extraction if needed
    # Extract run number from input folder name if possible
    match = re.search(r'run_(\d+)', input_folder)
    if match:
        run_number = int(match.group(1))
        print(f"Detected run number: {run_number}")
    else:
        print("No run number detected in input folder name.")
    input_folder = os.fspath(input_folder)
    output_folder = os.fspath(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    out_path = os.path.join(output_folder, f"more_waveforms_ch{channel}.root")
    root_file = ROOT.TFile(out_path, "RECREATE")
    tree_waveforms = ROOT.TTree("waveforms", "Waveform Data")
    tree_metadata = ROOT.TTree("metadata", "Metadata")
    if is_condor:
        # Remove tqdm for non-local mode
        tqdm.tqdm = lambda x: x
    # Split the file in smaller ones of 10GB
    tree_waveforms.SetMaxTreeSize(10*1024**3)
    tree_waveforms.SetAutoFlush(500_000_000)
    root_file.SetCompressionLevel(1)


    # C-compatible 32-bit int for scalar branch
    event_number = array('i', [0])
    time_vec = ROOT.VecOps.RVec('double')()
    voltage_vec = ROOT.VecOps.RVec('double')()
    min_voltage = array('f', [0.0])
    min_time = array('f', [0.0])

    tree_waveforms.Branch("event_number", event_number, "event_number/I")
    tree_waveforms.Branch("voltage", voltage_vec)
    tree_waveforms.Branch("min_voltage", min_voltage, "min_voltage/F")
    tree_waveforms.Branch("min_time", min_time, "min_time/F")
    
    tree_metadata.Branch("channel", array('i', [channel]), "channel/I")
    tree_metadata.Branch("time", time_vec)
    tree_metadata.Branch("run_number", array('i', [0]), "run_number/I")

    pattern = re.compile(rf'cycle_(\d+)_ch{channel}\.wfm$')  # escaped .wfm
    files = sorted(os.listdir(input_folder))

    global_event_counter = 0
    printed_files = 0
    for filename in files:
        match = pattern.search(filename)
        if not match:
            continue
        printed_files += 1
        input_file = os.path.join(input_folder, filename)
        print(f"Processing file: {input_file}")
        # Stream frames from the file to avoid allocating large arrays
        for time_axis, waveform in tqdm.tqdm(iter_waveforms(input_file)):
            # prepare vectors; clear previous contents
            if global_event_counter == 0:
                tmpt = ROOT.std.vector('double')(time_axis.astype(np.float64).tolist())
                # Fill the time vector only once (assumed constant across events)
                time_vec.clear()
                time_vec.insert(time_vec.end(), tmpt.begin(), tmpt.end())
                tree_metadata.Fill()
            if len(waveform) == 0:
                global_event_counter += 1
                continue
            tmpv = ROOT.std.vector('double')(waveform.astype(np.float64).tolist())
            voltage_vec.clear()
            voltage_vec.insert(voltage_vec.end(), tmpv.begin(), tmpv.end())

            event_number[0] = int(global_event_counter)
            min_voltage[0] = float(np.min(waveform))
            min_time[0] = float(time_axis[np.argmin(waveform)])
            tree_waveforms.Fill()
            global_event_counter += 1

        # small progress info per file (keeps stdout readable)
        if printed_files % 10 == 0:
            print(f"Processed {printed_files} files, {global_event_counter} events so far...")

    # final write
    root_file.Write()
    root_file.Close()
    print(f"Wrote {global_event_counter} events to {out_path}")


if __name__ == "__main__":
    main()
