#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import struct as st
import numpy as np
import os 
import ROOT


class wfmread:
    '''
    Reads the .wfm binary structure for analysis without saving to large files
    '''
    def __init__(self, name):
        self.name = name
        self.__read_wfm(name)

    def __read_wfm(self, name):
        with open(name, 'rb') as f:
            # Struct format reference:
            # H = unsigned short (2 bytes)
            # Ns = char[N] (N bytes): N int
            # l = long (4 bytes)
            # b = signed char (1 byte)
            # f = float (4 bytes)
            # d = double (8 bytes)
            # L = unsigned long (4 bytes)
            # i = int (4 bytes)
            # --- waveform static file information (#0) --- 78bytes
            self.byte_order                    = st.unpack('H', f.read(2))[0]
            self.version                       = st.unpack('8s', f.read(8))[0].decode('utf-8')
            self.num_digits_in_byte_count      = st.unpack('1s', f.read(1))[0].decode('utf-8')
            self.num_bytes_to_eof              = st.unpack('i', f.read(4))[0]
            self.num_bytes_per_point           = st.unpack('b', f.read(1))[0]
            self.byte_offset_to_curve_buffer   = st.unpack('i', f.read(4))[0]
            self.hor_zoom_scale                = st.unpack('i', f.read(4))[0]
            self.hor_zoom_pos                  = st.unpack('f', f.read(4))[0]
            self.ver_zoom_scale                = st.unpack('d', f.read(8))[0]
            self.ver_zoom_pos                  = st.unpack('f', f.read(4))[0]
            self.waveform_label                = st.unpack('32s', f.read(32))[0].decode('utf-8')
            self.n                             = st.unpack('I', f.read(4))[0]
            self.header_size                   = st.unpack('H', f.read(2))[0]

            # --- waveform header ---
            self.set_type                      = st.unpack('i', f.read(4))[0] # 0 single waveform, 1 fast frame
            if self.set_type == 0:
                self.isfast_frame             = False
            elif self.set_type == 1:
                self.isfast_frame             = True
            else:
                raise ValueError("Unknown set type: {}".format(self.set_type))
            self.wfm_cnt                       = st.unpack('I', f.read(4))[0]
            _ = f.read(36)  # skip these bytes
            # Acquisition counter 8b, transaction counter 8b, slot ID 4b, Is static flag 4b
            # wfm update specification count 4b, imp dim ref count 4b, exp dim ref count 4b
            self.data_type                     = st.unpack('i', f.read(4))[0]  # (#122)
            _ = f.read(16)  # skip these bytes
            # gen purpose counter 8b, accumulated waveform count 4b, target target accumulation count 4b
            self.curve_ref_count               = st.unpack('I', f.read(4))[0]  # (#142)
            self.num_req_fastframe             = st.unpack('I', f.read(4))[0]
            self.num_acq_fastframe             = st.unpack('I', f.read(4))[0]
            _ = f.read(14)  # skip these bytes
            # summary frame 2b, pix map display format 4b, pix map max value 8b
            # --- explicit dimension 1 (voltage axis) ---
            #  in the manual, theres no spacing between Ext dim X and the number
            # V = wfmCurveData*Scale + Offset
            self.exp_dim1_scale                = st.unpack('d', f.read(8))[0]
            self.exp_dim1_offset               = st.unpack('d', f.read(8))[0]
            self.exp_dim1_size                 = st.unpack('I', f.read(4))[0]
            self.exp_dim1_units                = st.unpack('20s', f.read(20))[0].decode('utf-8')
            f.read(16)  # Skip these bytes
            # dim extent min 8b, dim extent max 8b,
            self.exp_dim1_resolution           = st.unpack('d', f.read(8))[0]
            self.exp_dim1_ref_point            = st.unpack('d', f.read(8))[0]
            self.exp_dim1_format               = st.unpack('i', f.read(4))[0]
            self.exp_dim1_storage_type         = st.unpack('i', f.read(4))[0]
            f.read(20)  # Skip these bytes
            # N value 4b, over range 4b, under range 4b, high range 4b, low range 4b
            self.exp_dim1_user_scale           = st.unpack('d', f.read(8))[0]
            self.exp_dim1_user_units           = st.unpack('20s', f.read(20))[0].decode('utf-8')
            self.exp_dim1_user_offset          = st.unpack('d', f.read(8))[0]
            if self.version == ':WFM#003':
                self.exp_dim1_point_density    = st.unpack('d', f.read(8))[0]
            else:
                self.exp_dim1_point_density    = st.unpack('I', f.read(4))[0]
            self.exp_dim1_href                 = st.unpack('d', f.read(8))[0]
            self.exp_dim1_trig_delay           = st.unpack('d', f.read(8))[0]

            # --- explicit dimension 2 (voltage axis) ---
            self.exp_dim2_scale                = st.unpack('d', f.read(8))[0]
            self.exp_dim2_offset               = st.unpack('d', f.read(8))[0]
            self.exp_dim2_size                 = st.unpack('I', f.read(4))[0]
            self.exp_dim2_units                = st.unpack('20s', f.read(20))[0].decode('utf-8')
            f.read(16)  # Skip these bytes
            self.exp_dim2_resolution           = st.unpack('d', f.read(8))[0]
            self.exp_dim2_ref_point            = st.unpack('d', f.read(8))[0]
            self.exp_dim2_format               = st.unpack('i', f.read(4))[0]
            self.exp_dim2_storage_type         = st.unpack('i', f.read(4))[0]
            f.read(20)  # Skip these bytes
            self.exp_dim2_user_scale           = st.unpack('d', f.read(8))[0]
            self.exp_dim2_user_units           = st.unpack('20s', f.read(20))[0].decode('utf-8')
            self.exp_dim2_user_offset          = st.unpack('d', f.read(8))[0]
            if self.version == ':WFM#003':
                self.exp_dim2_point_density    = st.unpack('d', f.read(8))[0]
            else:
                self.exp_dim2_point_density    = st.unpack('I', f.read(4))[0]
            self.exp_dim2_href                 = st.unpack('d', f.read(8))[0]
            self.exp_dim2_trig_delay           = st.unpack('d', f.read(8))[0]

            # --- implicit dimension 1 (time axis) ---
            self.imp_dim1_scale                = st.unpack('d', f.read(8))[0]
            self.imp_dim1_offset               = st.unpack('d', f.read(8))[0]
            self.imp_dim1_size                 = st.unpack('I', f.read(4))[0]
            self.imp_dim1_units                = st.unpack('20s', f.read(20))[0].decode('utf-8')
            f.read(36)  # Skip these bytes
            self.imp_dim1_user_scale           = st.unpack('d', f.read(8))[0]
            self.imp_dim1_user_units           = st.unpack('20s', f.read(20))[0].decode('utf-8')
            self.imp_dim1_user_offset          = st.unpack('d', f.read(8))[0]
            f.read(8)  # Skip these bytes
            self.imp_dim1_href                 = st.unpack('d', f.read(8))[0]
            self.imp_dim1_trig_delay           = st.unpack('d', f.read(8))[0]

            # --- implicit dimension 2 (time axis) ---
            self.imp_dim2_scale                = st.unpack('d', f.read(8))[0]
            self.imp_dim2_offset               = st.unpack('d', f.read(8))[0]
            self.imp_dim2_size                 = st.unpack('I', f.read(4))[0]
            self.imp_dim2_units                = st.unpack('20s', f.read(20))[0].decode('utf-8')
            f.read(36)  # Skip these bytes
            self.imp_dim2_user_scale           = st.unpack('d', f.read(8))[0]
            self.imp_dim2_user_units           = st.unpack('20s', f.read(20))[0].decode('utf-8')
            self.imp_dim2_user_offset          = st.unpack('d', f.read(8))[0]
            f.read(8)  # Skip these bytes
            self.imp_dim2_href                 = st.unpack('d', f.read(8))[0]
            self.imp_dim2_trig_delay           = st.unpack('d', f.read(8))[0]

            # --- time base 1 and 2 info ---
            self.time_base1_real_point_spacing = st.unpack('I', f.read(4))[0]
            self.time_base1_sweep              = st.unpack('i', f.read(4))[0]
            self.time_base1_type_of_base       = st.unpack('i', f.read(4))[0]

            self.time_base2_real_point_spacing = st.unpack('I', f.read(4))[0]
            self.time_base2_sweep              = st.unpack('i', f.read(4))[0]
            self.time_base2_type_of_base       = st.unpack('i', f.read(4))[0]

            # --- WFM update specification ---
            # read but we keep values for possible first-frame timestamp
            real_point_offset_first            = st.unpack('I', f.read(4))[0]
            tt_offset_first                    = st.unpack('d', f.read(8))[0]
            frac_sec_first                     = st.unpack('d', f.read(8))[0]
            gmt_sec_first                      = st.unpack('i', f.read(4))[0]
            # store first frame timestamp
            try:
                self.frame_timestamps.append(float(gmt_sec_first) + float(frac_sec_first))
            except Exception:
                pass
            # --- WFM curve information --
            f.read(10)  # Skip these bytes
            self.precharge_start_offset        = st.unpack('I', f.read(4))[0]
            self.data_start_offset             = st.unpack('I', f.read(4))[0]
            self.postcharge_start_offset       = st.unpack('I', f.read(4))[0]
            self.postcharge_stop_offset        = st.unpack('I', f.read(4))[0]
            self.end_of_curve_buffer_offset    = st.unpack('I', f.read(4))[0]

            # FastFrame Frames
            if self.set_type == 1 and getattr(self, 'num_acq_fastframe', 0) > 1:
                n_extra_frames = int(self.num_acq_fastframe) - 1

                # Read N-1 WfmCurveSpec
                self._fast_curves = []
                for i in range(n_extra_frames):
                    state_flags = st.unpack('I', f.read(4))[0]
                    checksum_type = st.unpack('i', f.read(4))[0]
                    checksum = st.unpack('H', f.read(2))[0]
                    precharge_start = st.unpack('I', f.read(4))[0]
                    data_start = st.unpack('I', f.read(4))[0]
                    postcharge_start = st.unpack('I', f.read(4))[0]
                    postcharge_stop = st.unpack('I', f.read(4))[0]
                    end_of_curve = st.unpack('I', f.read(4))[0]


                    self._fast_curves.append({
                    'state_flags': state_flags,
                    'checksum_type': checksum_type,
                    'checksum': checksum,
                    'precharge_start': precharge_start,
                    'data_start': data_start,
                    'postcharge_start': postcharge_start,
                    'postcharge_stop': postcharge_stop,
                    'end_of_curve': end_of_curve
                    })

                # --- Curve Buffer ---
                # compute expected curve size for the main (first) curve
                # note: data_start_offset and postcharge_stop_offset are offsets relative to the curve buffer
                try:
                    self.curve_size_in_bytes = int(self.postcharge_start_offset) - int(self.data_start_offset)
                except Exception:
                    self.curve_size_in_bytes = None
                
                # Move to curve buffer start
                if getattr(self, 'byte_offset_to_curve_buffer', None) is None:
                    # fallback: try to compute from current file position
                    curve_buf_start = f.tell()
                else:
                    curve_buf_start = int(self.byte_offset_to_curve_buffer)
                
                # Read full curve buffer once to allow slicing for each frame
                f.seek(curve_buf_start)
                # If end_of_curve_buffer_offset is available, use it to determine buffer length
                buffer_len = None
                if getattr(self, 'end_of_curve_buffer_offset', None) is not None:
                    try:
                        buffer_len = int(self.end_of_curve_buffer_offset)
                    except Exception:
                        buffer_len = None


                # If we have N frames layout, we can't always rely on single curve_size_in_bytes for all
                # Instead read until the next header/EOF (use num_bytes_to_eof to be safe)
                try:
                    # num_bytes_to_eof is bytes from early header to EOF
                    # compute how many bytes remain from curve_buf_start to EOF
                    f.seek(0, os.SEEK_END)
                    file_size = f.tell()
                    # bytes from curve buffer start to EOF
                    remaining = file_size - curve_buf_start
                    f.seek(curve_buf_start)
                    full_curve_buf = f.read(remaining if buffer_len is None else min(remaining, buffer_len))
                except Exception:
                    full_curve_buf = b''

                # Determine numpy dtype from exp_dim1_format
                fmt = getattr(self, 'exp_dim1_format', 0)
                dtype_map = {
                    0: np.int16,
                    1: np.int32,
                    2: np.uint32,
                    3: np.uint64,
                    4: np.float32,
                    5: np.float64,
                    6: np.uint8,
                    7: np.int8
                }
                if fmt not in dtype_map:
                    # fallback to int16
                    dtype = np.int16
                else:
                    dtype = dtype_map[fmt]


                bpp = int(np.dtype(dtype).itemsize)
                if self.num_bytes_per_point and abs(int(self.num_bytes_per_point)) != bpp:
                    # if header num_bytes_per_point disagrees, prefer header but make sure slicing counts match
                    bpp = abs(int(self.num_bytes_per_point))

                # Helper to convert raw bytes slice -> numpy array in engineering units
                def slice_to_array(raw_bytes):
                    # ensure length multiple of bpp
                    n_samples = len(raw_bytes) // bpp
                    if n_samples <= 0:
                        return np.array([])
                    
                    arr = np.frombuffer(raw_bytes[:n_samples * bpp], dtype=dtype, count=n_samples)
                    # convert to float64 and apply exp_dim1 scale/offset
                    scale = float(getattr(self, 'exp_dim1_scale', 1.0))
                    offset = float(getattr(self, 'exp_dim1_offset', 0.0))
                    return arr.astype(np.float64) * scale + offset
                
                # Build list of curve specs including first frame then extras
                all_curve_specs = []
                # first
                all_curve_specs.append({
                    'data_start': int(self.data_start_offset) if getattr(self, 'data_start_offset', None) is not None else None,
                    'postcharge_stop': int(self.postcharge_stop_offset) if getattr(self, 'postcharge_stop_offset', None) is not None else None
                })
                # extras
                if getattr(self, '_fast_curves', None):
                    for cs in self._fast_curves:
                        all_curve_specs.append({
                            'data_start': cs.get('data_start'),
                            'postcharge_stop': cs.get('postcharge_stop')
                        })

                # Extract frames from full_curve_buf using offsets relative to curve buffer start
                self.frames = []
                for cs in all_curve_specs:
                    if cs['data_start'] is None or cs['postcharge_stop'] is None:
                        self.frames.append(None)
                        continue
                    s = int(cs['data_start'])
                    e = int(cs['postcharge_stop'])
                    # bounds-check
                    if s < 0 or e <= s or e > len(full_curve_buf):
                    # try clamping to available buffer
                        s = max(0, s)
                        e = min(len(full_curve_buf), e)
                    if e <= s:
                        self.frames.append(None)
                        continue
                    raw = full_curve_buf[s:e]
                    arr = slice_to_array(raw)
                    self.frames.append(arr)
                # Backwards-compatible single-frame outputs: fill self.data and self.time
                if len(self.frames) >= 1 and self.frames[0] is not None and self.frames[0].size > 0:
                    self.curve_data = np.array(self.frames[0], dtype=np.float64)
                    self.data = np.array(self.curve_data)
                    # time: implicit dimension 1
                    try:
                        pts = int(getattr(self, 'imp_dim1_size', self.curve_data.size))
                        self.time = np.arange(0, pts) * float(getattr(self, 'imp_dim1_scale', 1.0)) + float(getattr(self, 'imp_dim1_offset', 0.0))
                    except Exception:
                        self.time = np.arange(0, self.curve_data.size)
                else:
                    self.curve_data = np.array([])
                    self.data = np.array([])
                    self.time = np.array([])
######################################################################  
    def write_to_npz(self):
        out_name = self.name.rstrip('.wfm')
        np.savez(out_name, voltage=self.data, timescale=self.time)

    def write_to_root(self):
        """
        Write waveform data to a ROOT file.
        The output ROOT file will have the same name as the input .wfm file but with a .root extension.
        """
        out_name = self.name.rstrip('.wfm') + '.root'
        f = ROOT.TFile(out_name, "RECREATE")
        t = ROOT.TTree("waveform", "Tektronix waveform data")

        voltage = ROOT.std.vector('double')()
        time = ROOT.std.vector('double')()

        t.Branch("voltage", voltage)
        t.Branch("time", time)

        voltage.clear()
        time.clear()
        for v in self.data:
            voltage.push_back(v)
        for tval in self.time:
            time.push_back(tval)

        t.Fill()
        f.Write()
        f.Close()