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
def main(input_folder, output_folder, channel):
    """
    Stream WFM frames from files and write them as entries in a ROOT TTree.
    Each TTree entry contains:
        - event_number: int
        - time: std::vector<double>
        - voltage: std::vector<double>
    """
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"Processing channel: {channel}")
    input_folder = os.fspath(input_folder)
    output_folder = os.fspath(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    out_path = os.path.join(output_folder, f"improved_waveforms_ch{channel}.root")
    root_file = ROOT.TFile(out_path, "RECREATE")
    tree = ROOT.TTree("waveforms", "Waveform Data")

    # C-compatible 32-bit int for scalar branch
    event_number = array('i', [0])
    time_vec = ROOT.std.vector('double')()
    voltage_vec = ROOT.std.vector('double')()
    min_voltage = array('f', [0.0])
    min_time = array('f', [0.0])


    tree.Branch("event_number", event_number, "event_number/I")
    tree.Branch("time", time_vec)
    tree.Branch("voltage", voltage_vec)
    tree.Branch("min_voltage", min_voltage, "min_voltage/F")
    tree.Branch("min_time", min_time, "min_time/F")

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
            time_vec.clear()
            voltage_vec.clear()

            n = len(time_axis)
            # try to reserve capacity (not all PyROOT builds expose reserve; guard with try/except)
            try:
                time_vec.reserve(n)
                voltage_vec.reserve(n)
            except Exception:
                pass

            # push data into vectors
            # using local variables for speed
            tv = time_vec
            vv = voltage_vec
            for t, v in zip(time_axis, waveform):
                tv.push_back(float(t))
                vv.push_back(float(v))

            event_number[0] = int(global_event_counter)
            min_voltage[0] = float(np.min(waveform))
            min_time[0] = float(time_axis[np.argmin(waveform)])
            tree.Fill()
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