#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tektronix WFM Version 1 file decoder (supports FastFrame mode)
---------------------------------------------------------------
Pure Python + NumPy implementation. Decodes header, dimensions, and all frames.

Outputs:
  - reader.frames        : list of NumPy arrays, each containing one frame (in volts)
  - reader.time          : NumPy array with the common time axis (seconds)
  - reader.timestamps    : list of UTC timestamps (gmtSec + fracSec) per frame
  - reader.metadata      : dict with basic header information

Usage:
    python wfm_v1_reader.py yourfile.wfm
"""

import struct as st
import numpy as np
import os
import sys


class TektronixWfmV1:
    """Simple reader for Tektronix .wfm version 1 files (with FastFrame support)."""

    def __init__(self, filename: str):
        self.filename = filename
        self.frames = []
        self.timestamps = []
        self.time = None
        self.metadata = {}
        self._read()

    # -------------------------------------------------------------------------
    def _read(self):
        with open(self.filename, "rb") as f:
            # --- HEADER (Static file information) ---
            self.byte_order = st.unpack("H", f.read(2))[0]
            self.version = st.unpack("8s", f.read(8))[0].decode("ascii", errors="ignore").strip()
            self.num_digits_in_byte_count = st.unpack("1s", f.read(1))[0]
            # For version 1 → 8 bytes (int64)
            self.num_bytes_to_eof = st.unpack("q", f.read(8))[0]
            self.num_bytes_per_point = st.unpack("b", f.read(1))[0]
            self.byte_offset_to_curve_buffer = st.unpack("l", f.read(4))[0]
            self.hor_zoom_scale = st.unpack("l", f.read(4))[0]
            self.hor_zoom_pos = st.unpack("f", f.read(4))[0]
            self.ver_zoom_scale = st.unpack("d", f.read(8))[0]
            self.ver_zoom_pos = st.unpack("f", f.read(4))[0]
            self.waveform_label = st.unpack("32s", f.read(32))[0].decode("ascii", errors="ignore").strip("\x00")
            self.metadata["label"] = self.waveform_label

            # --- waveform header ---
            self.set_type = st.unpack("i", f.read(4))[0]  # 0 = single, 1 = fast frame
            self.is_fastframe = (self.set_type == 1)
            self.wfm_cnt = st.unpack("L", f.read(4))[0]
            f.read(36)  # skip some header bytes
            self.data_type = st.unpack("i", f.read(4))[0]
            f.read(16)
            self.curve_ref_count = st.unpack("L", f.read(4))[0]
            self.num_req_fastframe = st.unpack("L", f.read(4))[0]
            self.num_acq_fastframe = st.unpack("L", f.read(4))[0]
            f.read(14)

            # --- Explicit Dimension 1 (Voltage scaling) ---
            self.exp_dim1_scale = st.unpack("d", f.read(8))[0]
            self.exp_dim1_offset = st.unpack("d", f.read(8))[0]
            self.exp_dim1_size = st.unpack("L", f.read(4))[0]
            f.read(60)  # skip rest of explicit dimension 1 (not needed here)

            # --- Implicit Dimension 1 (Time base) ---
            f.seek(370)  # jump roughly to implicit dim 1 start (fixed offset in v1)
            self.imp_dim1_scale = st.unpack("d", f.read(8))[0]  # seconds per point
            self.imp_dim1_offset = st.unpack("d", f.read(8))[0]
            self.imp_dim1_size = st.unpack("L", f.read(4))[0]
            f.read(20)  # skip units and some extras
            self.metadata["dt"] = self.imp_dim1_scale
            self.metadata["n_points"] = self.imp_dim1_size

            # --- WfmUpdateSpec (first frame) ---
            real_point_offset = st.unpack("L", f.read(4))[0]
            tt_offset = st.unpack("d", f.read(8))[0]
            frac_sec = st.unpack("d", f.read(8))[0]
            gmt_sec = st.unpack("l", f.read(4))[0]
            self.timestamps.append(gmt_sec + frac_sec)

            # --- WfmCurveSpec (first frame) ---
            f.read(10)
            self.precharge_start_offset = st.unpack("L", f.read(4))[0]
            self.data_start_offset = st.unpack("L", f.read(4))[0]
            self.postcharge_start_offset = st.unpack("L", f.read(4))[0]
            self.postcharge_stop_offset = st.unpack("L", f.read(4))[0]
            self.end_of_curve_buffer_offset = st.unpack("L", f.read(4))[0]

            # --- FastFrame: additional update + curve specs ---
            self.curves = [{
                "data_start": self.data_start_offset,
                "postcharge_stop": self.postcharge_stop_offset,
            }]

            if self.is_fastframe and self.num_acq_fastframe > 1:
                n_extra = int(self.num_acq_fastframe) - 1

                # read extra WfmUpdateSpec blocks (timestamps)
                for _ in range(n_extra):
                    real_point_offset = st.unpack("L", f.read(4))[0]
                    tt_offset = st.unpack("d", f.read(8))[0]
                    frac_sec = st.unpack("d", f.read(8))[0]
                    gmt_sec = st.unpack("l", f.read(4))[0]
                    self.timestamps.append(gmt_sec + frac_sec)

                # read extra WfmCurveSpec blocks (frame offsets)
                for _ in range(n_extra):
                    state_flags = st.unpack("L", f.read(4))[0]
                    checksum_type = st.unpack("i", f.read(4))[0]
                    checksum = st.unpack("H", f.read(2))[0]
                    precharge_start = st.unpack("L", f.read(4))[0]
                    data_start = st.unpack("L", f.read(4))[0]
                    postcharge_start = st.unpack("L", f.read(4))[0]
                    postcharge_stop = st.unpack("L", f.read(4))[0]
                    end_of_curve = st.unpack("L", f.read(4))[0]
                    self.curves.append({
                        "data_start": data_start,
                        "postcharge_stop": postcharge_stop
                    })

            # --- Read waveform data ---
            # Seek to curve buffer start
            f.seek(self.byte_offset_to_curve_buffer)
            full_buf = f.read()

            # dtype per format (explicit dim1 format → assume int16 here)
            dtype = np.int16 if abs(self.num_bytes_per_point) == 2 else np.int8
            bytes_per_point = abs(self.num_bytes_per_point)

            # Helper to convert raw bytes → voltage array
            def to_array(b):
                n = len(b) // bytes_per_point
                arr = np.frombuffer(b[:n * bytes_per_point], dtype=dtype)
                return arr.astype(np.float64) * self.exp_dim1_scale + self.exp_dim1_offset

            # Extract each frame
            for c in self.curves:
                s = int(c["data_start"])
                e = int(c["postcharge_stop"])
                if e > s and e <= len(full_buf):
                    self.frames.append(to_array(full_buf[s:e]))
                else:
                    self.frames.append(np.array([]))

            # --- Generate common time axis ---
            npts = len(self.frames[0]) if self.frames and self.frames[0].size else self.imp_dim1_size
            self.time = np.arange(npts) * self.imp_dim1_scale + self.imp_dim1_offset

    # -------------------------------------------------------------------------
    def summary(self):
        print(f"File: {self.filename}")
        print(f"Version: {self.version}")
        print(f"FastFrame: {self.is_fastframe}  (frames = {len(self.frames)})")
        print(f"Samples per frame: {len(self.frames[0]) if self.frames else 'N/A'}")
        if self.timestamps:
            print(f"First timestamp (UTC seconds): {self.timestamps[0]:.6f}")
        print(f"Voltage scale: {self.exp_dim1_scale}, offset: {self.exp_dim1_offset}")
        print(f"Time step: {self.imp_dim1_scale} s")
        print()


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python wfm_v1_reader.py file.wfm")
        sys.exit(1)

    fname = sys.argv[1]
    reader = TektronixWfmV1(fname)
    reader.summary()

    print("Frames read:", len(reader.frames))
    if reader.frames:
        print("First 10 voltage samples (frame 0):")
        print(reader.frames[0][:10])
