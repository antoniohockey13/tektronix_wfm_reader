from signals.PeakSignal import PeakSignal, draw_in_plotly
import click
import ROOT
import numpy as np
from array import array
import os

# Use M. Senger signal library to extract needed information to implement them into corryvreckan

def is_hit(SNR, StartTime, RiseTime):
    """
    Simple hit finding logic based on SNR, StartTime, and RiseTime thresholds.
    Adjust the thresholds as needed for your specific application.
    
    Args:
        SNR (float): Signal-to-noise ratio of the pulse.
        StartTime (float): Start time of the pulse.
        RiseTime (float): Rise time of the pulse.
    """
    # if any variable is None or NaN, return False
    if SNR is None or StartTime is None or RiseTime is None:
        return False
    if isinstance(SNR, float) and (SNR != SNR):
        return False
    if isinstance(StartTime, float) and (StartTime != StartTime):
        return False
    if isinstance(RiseTime, float) and (RiseTime != RiseTime):
        return False
    
    SNR_threshold = 0.0      # Example threshold for SNR
    StartTime_lowerthreshold = 0.0 # Example threshold for StartTime
    StartTime_upperthreshold = np.inf # Example threshold for StartTime
    RiseTime_lowerthreshold = 0.0 # Example threshold for RiseTime
    RiseTime_upperthreshold = np.inf # Example threshold for RiseTime

    if abs(SNR) > SNR_threshold and \
        StartTime > StartTime_lowerthreshold and StartTime < StartTime_upperthreshold and \
        RiseTime > RiseTime_lowerthreshold and RiseTime < RiseTime_upperthreshold:
        return True
    return False

@click.command()
@click.option('-i', '--input_file', type=click.Path(), help="Input file path without channel and extension")
@click.option('-o', '--output_file', default="output.root", type=click.Path(), help="Output file to store the variables in ROOT format")
def main(input_file, output_file):
    # Open the input file
    df = ROOT.RDataFrame("waveforms", input_file)
    if not df:
        print(f"Error: Could not open file {input_file}")
        return
    if not output_file.endswith(".root"):
        output_file += ".root"
    output_path = os.path.dirname(output_file)
    # # Read first entry
    # df1 = df.Range(1)

    # # Extract columns as NumPy arrays
    # data = df1.AsNumpy(["event_number", "time", "voltage"])

    # # Access values
    # event_number = data["event_number"][0]
    # time_vec = np.array(data["time"][0])
    # voltage_vec = np.array(data["voltage"][0])
    # pulse = PeakSignal(time = time_vec, samples = voltage_vec, peak_polarity="negative")
    # fig = draw_in_plotly(pulse)
    # fig.update_layout(
    #     title = "My signal",
    #     xaxis_title = "Time (s)",
    #     yaxis_title = "Amplitude (V)",
    # )
    # fig.show()

    # input("Press Enter to continue...")
    # Store interesting histograms in a root file
    root_file = ROOT.TFile(output_file, "RECREATE")
    tree = ROOT.TTree("tree", "tree")
    # Variables to store in the tree
    snr = array('f', [0])
    amplitude = array('f', [0])
    toa = array('f', [0])
    integral = array('f', [0])
    rise_time = array('f', [0])

    tree.Branch("snr", snr, "snr/F")
    tree.Branch("amplitude", amplitude, "amplitude/F")
    tree.Branch("toa", toa, "toa/F")
    tree.Branch("integral", integral, "integral/F")
    tree.Branch("rise_time", rise_time, "rise_time/F")

    # Write interesting variables into a .txt file for corryvreckan
    with open(f"{output_path}/signal_data.txt", "w") as f:
        f.write("Event_Number, Detector, Charge, ToA\n")
        for _ in range(df.Count().GetValue()):
            data = df.Range(_, _+1).AsNumpy(["event_number", "time", "voltage"])
            event_number = data["event_number"][0]
            time_vec = np.array(data["time"][0])
            voltage_vec = np.array(data["voltage"][0])

            pulse = PeakSignal(time = time_vec, samples = voltage_vec, peak_polarity="negative")

            if is_hit(pulse.SNR, pulse.peak_start_time, pulse.rise_time):
                # TODO, Define with an if hardcoded for each run
                detector_name = ""  
                
                charge = pulse.peak_integral
                time_of_arrival = pulse.peak_start_time
                f.write(f"{event_number}, {detector_name}, {charge}, {time_of_arrival}\n")

                snr[0] = pulse.SNR
                amplitude[0] = pulse.amplitude
                toa[0] = time_of_arrival
                integral[0] = charge
                rise_time[0] = pulse.rise_time

            tree.Fill()
    root_file.Write()
    root_file.Close()
                

if __name__ == "__main__":
    main()
                