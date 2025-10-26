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
            # waveform static file information (#0)
            self.byte_order                    = st.unpack('H', f.read(2))[0]
            self.version                       = st.unpack('8s', f.read(8))[0].decode('utf-8')
            self.num_digits_in_byte_count      = st.unpack('1s', f.read(1))[0].decode('utf-8')
            self.num_bytes_to_eof              = st.unpack('l', f.read(4))[0]
            self.num_bytes_per_point           = st.unpack('b', f.read(1))[0]
            self.byte_offset_to_curve_buffer   = st.unpack('l', f.read(4))[0]
            self.hor_zoom_scale                = st.unpack('l', f.read(4))[0]
            self.hor_zoom_pos                  = st.unpack('f', f.read(4))[0]
            self.ver_zoom_scale                = st.unpack('d', f.read(8))[0]
            self.ver_zoom_pos                  = st.unpack('f', f.read(4))[0]
            self.waveform_label                = st.unpack('32s', f.read(32))[0].decode('utf-8')
            self.n                             = st.unpack('L', f.read(4))[0]
            self.header_size                   = st.unpack('H', f.read(2))[0]

            # waveform header (#78)
            self.set_type                      = st.unpack('i', f.read(4))[0]
            self.wfm_cnt                       = st.unpack('L', f.read(4))[0]
            _ = f.read(36)  # skip these bytes
            self.data_type                     = st.unpack('i', f.read(4))[0]  # (#122)
            _ = f.read(16)  # skip these bytes
            self.curve_ref_count               = st.unpack('L', f.read(4))[0]  # (#142)
            self.num_req_fastframe             = st.unpack('L', f.read(4))[0]
            self.num_acq_fastframe             = st.unpack('L', f.read(4))[0]
            _ = f.read(14)  # skip these bytes

            # explicit dimension 1 (voltage axis) (#168)
            #  in the manual, theres no spacing between Ext dim X and the number
            self.exp_dim1_scale                = st.unpack('d', f.read(8))[0]
            self.exp_dim1_offset               = st.unpack('d', f.read(8))[0]
            self.exp_dim1_size                 = st.unpack('L', f.read(4))[0]
            self.exp_dim1_units                = st.unpack('20s', f.read(20))[0].decode('utf-8')
            f.read(16)  # Skip these bytes
            self.exp_dim1_resolution           = st.unpack('d', f.read(8))[0]
            self.exp_dim1_ref_point            = st.unpack('d', f.read(8))[0]
            self.exp_dim1_format               = st.unpack('i', f.read(4))[0]
            self.exp_dim1_storage_type         = st.unpack('i', f.read(4))[0]
            f.read(20)  # Skip these bytes
            self.exp_dim1_user_scale           = st.unpack('d', f.read(8))[0]
            self.exp_dim1_user_units           = st.unpack('20s', f.read(20))[0].decode('utf-8')
            self.exp_dim1_user_offset          = st.unpack('d', f.read(8))[0]
            if self.version == ':WFM#003':
                self.exp_dim1_point_density    = st.unpack('d', f.read(8))[0]
            else:
                self.exp_dim1_point_density    = st.unpack('L', f.read(4))[0]
            self.exp_dim1_href                 = st.unpack('d', f.read(8))[0]
            self.exp_dim1_trig_delay           = st.unpack('d', f.read(8))[0]

            # explicit dimension 2 (voltage axis) (#328)
            self.exp_dim2_scale                = st.unpack('d', f.read(8))[0]
            self.exp_dim2_offset               = st.unpack('d', f.read(8))[0]
            self.exp_dim2_size                 = st.unpack('L', f.read(4))[0]
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
                self.exp_dim2_point_density    = st.unpack('L', f.read(4))[0]
            self.exp_dim2_href                 = st.unpack('d', f.read(8))[0]
            self.exp_dim2_trig_delay           = st.unpack('d', f.read(8))[0]

            # implicit dimension 1 (time axis) (#488)
            self.imp_dim1_scale                = st.unpack('d', f.read(8))[0]
            self.imp_dim1_offset               = st.unpack('d', f.read(8))[0]
            self.imp_dim1_size                 = st.unpack('L', f.read(4))[0]
            self.imp_dim1_units                = st.unpack('20s', f.read(20))[0].decode('utf-8')
            f.read(36)  # Skip these bytes
            self.imp_dim1_user_scale           = st.unpack('d', f.read(8))[0]
            self.imp_dim1_user_units           = st.unpack('20s', f.read(20))[0].decode('utf-8')
            self.imp_dim1_user_offset          = st.unpack('d', f.read(8))[0]
            f.read(8)  # Skip these bytes
            self.imp_dim1_href                 = st.unpack('d', f.read(8))[0]
            self.imp_dim1_trig_delay           = st.unpack('d', f.read(8))[0]

            # implicit dimension 2 (time axis) (#624)
            self.imp_dim2_scale                = st.unpack('d', f.read(8))[0]
            self.imp_dim2_offset               = st.unpack('d', f.read(8))[0]
            self.imp_dim2_size                 = st.unpack('L', f.read(4))[0]
            self.imp_dim2_units                = st.unpack('20s', f.read(20))[0].decode('utf-8')
            f.read(36)  # Skip these bytes
            self.imp_dim2_user_scale           = st.unpack('d', f.read(8))[0]
            self.imp_dim2_user_units           = st.unpack('20s', f.read(20))[0].decode('utf-8')
            self.imp_dim2_user_offset          = st.unpack('d', f.read(8))[0]
            f.read(8)  # Skip these bytes
            self.imp_dim2_href                 = st.unpack('d', f.read(8))[0]
            self.imp_dim2_trig_delay           = st.unpack('d', f.read(8))[0]

            # time base 1 and 2 info (#760)
            self.time_base1_real_point_spacing = st.unpack('L', f.read(4))[0]
            self.time_base1_sweep              = st.unpack('i', f.read(4))[0]
            self.time_base1_type_of_base       = st.unpack('i', f.read(4))[0]

            self.time_base2_real_point_spacing = st.unpack('L', f.read(4))[0]
            self.time_base2_sweep              = st.unpack('i', f.read(4))[0]
            self.time_base2_type_of_base       = st.unpack('i', f.read(4))[0]

            # WFM update specification (#784)
            f.read(24)  # Skip these bytes

            # WFM curve information (#808)
            f.read(10)  # Skip these bytes
            self.precharge_start_offset        = st.unpack('L', f.read(4))[0]
            self.data_start_offset             = st.unpack('L', f.read(4))[0]
            self.postcharge_start_offset       = st.unpack('L', f.read(4))[0]
            self.postcharge_stop_offset        = st.unpack('L', f.read(4))[0]
            self.end_of_curve_buffer_offset    = st.unpack('L', f.read(4))[0]

            # FastFrame Frames
            # skip

            # Curve Buffer
            self.curve_size_in_bytes = self.postcharge_start_offset - self.data_start_offset
            self.curve_size = int(self.curve_size_in_bytes / self.num_bytes_per_point)
            f.read(self.data_start_offset)  # Skip these bytes

            if self.num_bytes_per_point == 1:
                self.curve_data = np.fromstring(f.read(self.curve_size_in_bytes), dtype='b')
            elif self.num_bytes_per_point > 1:
                self.curve_data = np.fromstring(f.read(self.curve_size_in_bytes), dtype='h')

            self.curve_data = np.array(self.curve_data, dtype=np.float64)  # convert to double

            # Outputs
            self.data = np.array(self.curve_data * self.exp_dim1_scale + self.exp_dim1_offset)
            self.time = np.arange(0, self.curve_size) * self.imp_dim1_scale + self.imp_dim1_offset

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


def main(fname):
    wfm = wfmread(fname)
    wfm.write_to_npz()

if __name__ == '__main__':
    main(sys.argv[1])
