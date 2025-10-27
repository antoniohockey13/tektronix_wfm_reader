import click
import re
import glob
import ROOT
import wfmread
import TektronixWfmV1
from collections import defaultdict
import numpy as np
from array import array

@click.command()
@click.option('-i', '--input_dir', type=click.Path(exists=True))
@click.option('-o', '--output_file', type=click.Path(), default="waveforms.root")
def main(input_dir, output_file):
    """
    Read folder with waveform files obtained from a Tektronix scope in fast frame mode. 
    Files have a name such as: cycle_X_chY.wfm, where X and Y are integer numbers
    """

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
    # time_vec = [ROOT.std.vector('double')() for _ in range(4)]
    # volt_vec = [ROOT.std.vector('double')() for _ in range(4)]
    # event_number = ROOT.std.vector('int')(1)
    time_arr = array('f', 25000*[0])
    volt_arr_ch1 = array('f', 25000*[0])
    volt_arr_ch2 = array('f', 25000*[0])
    volt_arr_ch3 = array('f', 25000*[0])
    volt_arr_ch4 = array('f', 25000*[0])
    event_number = array('i', 1*[0])
    v1_min = array('f', 1*[0])
    v2_min = array('f', 1*[0])
    v3_min = array('f', 1*[0])
    v4_min = array('f', 1*[0])
    # for i in range(4):
    #     t.Branch(f"time_ch{i+1}", time_vec[i])
    #     t.Branch(f"voltage_ch{i+1}", volt_vec[i])
    # t.Branch("event_number", event_number)
    t.Branch("time", time_arr, "time[25000]/F")
    t.Branch("v1", volt_arr_ch1, "voltage_ch1[25000]/F")
    t.Branch("v2", volt_arr_ch2, "voltage_ch2[25000]/F")
    t.Branch("v3", volt_arr_ch3, "voltage_ch3[25000]/F")
    t.Branch("v4", volt_arr_ch4, "voltage_ch4[25000]/F")
    t.Branch("event", event_number, "event_number[1]/I")
    t.Branch("v1_min", v1_min, "v1_min[1]/F")
    t.Branch("v2_min", v2_min, "v2_min[1]/F")
    t.Branch("v3_min", v3_min, "v3_min[1]/F")
    t.Branch("v4_min", v4_min, "v4_min[1]/F")
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
            data = wfmread.wfmread(files[ch])
            wfms[ch] = data
            
            if nframes is None:
                nframes = len(wfms[ch].frames)  # number of fast frames
            else:
                nframes = min(nframes, len(wfms[ch].frames))
            print(f"    Number of frames: {nframes}")
        if not wfms:
            continue

        # --- Loop over FastFrames ---
        for frame in range(nframes):
            # print(global_event, event_number)
            event_number[0] = global_event

            # for i in range(4):
            #     time_vec[i].clear()
            #     volt_vec[i].clear()

            for ch, wfm in wfms.items():
                if type(wfm.frames[frame]) == type(None)    :
                    continue    
                # print(f"  Processing channel {ch}, frame {frame}...")
                # print(wfm.frames)
                # print(f"Waveform time points: {len(wfm.time)}, voltage points: {len(wfm.frames[frame])}")
                time_data = wfm.time
                # print(f"Time data: {time_data}")    
                voltage_data = wfm.frames[frame]
                # print(f"Voltage data mean: {np.mean(np.array(voltage_data))}")
                # for tval in time_data:
                #     time_vec[ch - 1].push_back(tval)
                # for vval in voltage_data:
                #     volt_vec[ch - 1].push_back(vval)
                #     event_number[0] = global_event
                #   print(len(time_data), len(voltage_data))
                for i in range(len(time_data)):
                    time_arr[i] = time_data[i]
                    if ch == 1:
                        volt_arr_ch1[i] = voltage_data[i]
                    elif ch == 2:
                        volt_arr_ch2[i] = voltage_data[i]
                    elif ch == 3:
                        volt_arr_ch3[i] = voltage_data[i]
                    elif ch == 4:
                        volt_arr_ch4[i] = voltage_data[i]
            if ch == 1:
                v1_min[0] = (min(voltage_data))
            if ch == 2:
                v2_min[0] = (min(voltage_data))
            if ch == 3:
                v3_min[0] = (min(voltage_data))
            if ch == 4:
                v4_min[0] = (min(voltage_data))
            t.Fill()
            global_event += 1


    print(f"Total events written: {global_event}")

    # --- 5. Write ROOT file ---
    t.Write()
    fout.Close()

    print("✅ Conversion finished. Output saved as waveforms.root")

if __name__ == "__main__":
    main()