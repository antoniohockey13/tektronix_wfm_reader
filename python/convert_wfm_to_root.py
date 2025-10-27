import glob
import re
import ROOT
import wfmread 
from collections import defaultdict
import click

@click.command()
@click.option('-i', '--input-dir', help='Input directory containing .wfm files', type=click.Path(exists=True))
@click.option('-o', '--output-file', help='Output ROOT file name', default='waveforms.root')
def main(input_dir, output_file):
    # --- 1. Group .wfm files by cycle ---
    pattern = re.compile(r"cycle_(\d+)_ch(\d)\.wfm")
    groups = defaultdict(dict)
    for fname in sorted(glob.glob(f"{input_dir}/cycle_*_ch*.wfm")):
        match = pattern.search(fname)
        if not match:
            continue
        cycle = int(match.group(1))
        ch = int(match.group(2))
        groups[cycle][ch] = fname

    print(f"Found {len(groups)} cycles.")

    # --- 2. Prepare ROOT output ---
    fout = ROOT.TFile(f"{input_dir}/{output_file}", "RECREATE")
    t = ROOT.TTree("waveforms", "Tektronix FastFrame waveform data")

    # Create ROOT branches
    time_vec = [ROOT.std.vector('double')() for _ in range(4)]
    volt_vec = [ROOT.std.vector('double')() for _ in range(4)]
    event_number = ROOT.std.vector('int')()

    for i in range(4):
        t.Branch(f"time_ch{i+1}", time_vec[i])
        t.Branch(f"voltage_ch{i+1}", volt_vec[i])
    t.Branch("event_number", event_number)

    # --- 3. Global event counter ---
    global_event = 0

    # --- 4. Loop over all cycles ---
    for cycle, files in sorted(groups.items()):
        print(f"Processing cycle {cycle}...")

        # Load waveforms for each channel
        wfms = {}
        nframes = None
        for ch in range(1, 5):
            if ch not in files:
                continue
            print(f"  Loading channel {ch} from {files[ch]}")
            data = tekwfm.tekwfm.read_wfm(files[ch])
            wfms[ch] = data["wfms"]
            
            if nframes is None:
                nframes = wfms[ch].count  # number of fast frames
            else:
                nframes = min(nframes, wfms[ch].count)

        if not wfms:
            continue

        # --- Loop over FastFrames ---
        for frame in range(nframes):
            event_number.clear()
            event_number.push_back(global_event)
            global_event += 1

            for i in range(4):
                time_vec[i].clear()
                volt_vec[i].clear()

            for ch, wfm in wfms.items():
                # Extract the frame
                segment = wfm.frame(frame)
                time_data = segment.time
                voltage_data = segment.y

                time_vec[ch - 1].extend(time_data)
                volt_vec[ch - 1].extend(voltage_data)

            t.Fill()

    print(f"Total events written: {global_event}")

    # --- 5. Write ROOT file ---
    t.Write()
    fout.Close()

    print("✅ Conversion finished. Output saved as waveforms.root")

if __name__ == "__main__":
    main()