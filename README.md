# Software for Tektronix Oscilloscope (Updated Oct 2025)

**Feb 2025:** Updated to read `.wfm` files from the **5 Series B MSO Mixed Signal Oscilloscope**.
**Oct 2025**: Implement Quim code in Matlab to python. Add functionality to write the file into ROOT 
## Files
### Matlab folder: Directly Quim code
### Python folder: Version of Quim's code with functionality to write the waveforms into ROOT (probably needs to be updated to a more efficient version)
- `wfm2readframe.py`: Base class that reads the wfm file
- `plot_wfm_fast.py`: Useful for a fast check, uses matplotlib to plot some data from the waveforms.
- `write_to_root.py`: Takes the `*.wfm` files and and convert the waveforms into a `.root` file

## Usage
### plot_wfm_fast.py

```
$ python3 /path/to/plot_wfm_fast.py -i /path/to/file/cycle_{cycle_number}
```
Notice that you do NOT need to pass the whole file name to the file just the `cycle_0000` part. Then, the code automatically add the channel and the extension. So, for `cycle_0000` the code will understand `cycle_0000_ch1.wfm`, `cycle_0000_ch2.wfm`, `cycle_0000_ch3.wfm` and `cycle_0000_ch4.wfm`


### write_to_root.py
```
$ python3 /path/to/write_to_root.py -i /path/to/run/folder -o /path/to/output/directory -c {channel_number}
```

The -i parameter request for the path to the folder where the `*.wfm` files are stored. The -o to where you want to store the output file, the default value is `.`. The -c parameter request the channel number you want to convert into a root file. The name of the final root file is `waveforms_ch{channel}.root` where channel is the -c parameter.


## Credits
- Partially based on MATLAB code [`wfm_ascii_dpo.m`](https://www.mathworks.com/matlabcentral/fileexchange/14918-tektronix-wfm-file-reader) by Randy White (2007).
- [Tektronix Waveform File Format Manual 077-0220-11](https://download.tek.com/manual/Waveform-File-Format-Manual-077022011.pdf)
- Original code from [Morgan Askins](https://github.com/MorganAskins/tektronix_wfmreader)
- Updated version from [AquaDragon](https://github.com/AquaDragon/tektronix_wfm_reader)
- Joaquim Piñol (Quim) Matlab code

