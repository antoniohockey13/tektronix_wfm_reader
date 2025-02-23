# Software for Tektronix Oscilloscope (Updated Feb 2025)

**Feb 2025:** Updated to read `.wfm` files from the **5 Series B MSO Mixed Signal Oscilloscope**.

## Files
### `wfmread.py`: Read binary `wfm003` files for data analysis
- has the option to write to an `.npz` file

#### To write to an `.npz` file:

$ python wfmread.py file.wfm  
This will output a new file called `file.npz`  
This file can be read in through python and plotted with matplotlib as so:  

$ python  
```python
>>> import numpy as np
>>> import matplotlib.pyplot as plt
>>> data = np.load('file.npz')
>>> data.files
  ['voltage', 'timescale']
>>> waveforms = data['voltage']
>>> time = data['timescale']
## data['voltage'] is a list of all waveforms, you can read a single waveform
## by calling its element data['voltage'][0] (first waveform)
>>> plt.plot(time, waveforms[0])
>>> plt.show()
```

### `time_resolution.ipynb`: Example analysis code using `wfmread.py`

## Credits
- Partially based on MATLAB code [`wfm_ascii_dpo.m`](https://www.mathworks.com/matlabcentral/fileexchange/14918-tektronix-wfm-file-reader) by Randy White (2007).
- [Tektronix Waveform File Format Manual 077-0220-11](https://download.tek.com/manual/Waveform-File-Format-Manual-077022011.pdf)
