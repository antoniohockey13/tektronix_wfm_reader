// wfmread.cpp
#include "wfmread.h"
#include <fstream>
#include <iostream>
#include <cstring>
#include <algorithm>
#include <cmath>
#include <stdexcept>

template<typename T>
T WfmRead::read_scalar(std::ifstream& f) {
    T v;
    f.read(reinterpret_cast<char*>(&v), sizeof(T));
    if (!f) throw std::runtime_error("Failed to read scalar from file");
    return v;
}

std::string WfmRead::read_str(std::ifstream& f, std::size_t n) {
    std::string s;
    s.resize(n);
    f.read(&s[0], n);
    if (!f) throw std::runtime_error("Failed to read string");
    // trim nulls and trailing spaces
    auto pos = s.find('\0');
    if (pos != std::string::npos) s.resize(pos);
    // trim trailing spaces
    while (!s.empty() && (s.back() == ' ' || s.back() == '\n' || s.back() == '\r' || s.back() == '\t')) s.pop_back();
    return s;
}

WfmRead::WfmRead(const std::string& filename) : name(filename) {
    read_wfm(filename);
}

WfmRead::~WfmRead() { }

std::vector<double> WfmRead::raw_slice_to_array(const std::vector<char>& raw, size_t start, size_t end) {
    if (end <= start || start >= raw.size()) return {};
    size_t len = end - start;
    // Determine dtype from exp_dim1_format (mapping as in python)
    // 0: int16, 1:int32, 2:uint32, 3:uint64, 4:float32, 5:float64, 6:uint8, 7:int8
    std::vector<double> out;
    int fmt = exp_dim1_format;
    size_t bpp = 2;
    if (fmt == 0) bpp = sizeof(int16_t);
    else if (fmt == 1) bpp = sizeof(int32_t);
    else if (fmt == 2) bpp = sizeof(uint32_t);
    else if (fmt == 3) bpp = sizeof(uint64_t);
    else if (fmt == 4) bpp = sizeof(float);
    else if (fmt == 5) bpp = sizeof(double);
    else if (fmt == 6) bpp = sizeof(uint8_t);
    else if (fmt == 7) bpp = sizeof(int8_t);
    else bpp = sizeof(int16_t); // fallback

    if (num_bytes_per_point != 0 && std::abs(num_bytes_per_point) != (int)bpp) {
        bpp = static_cast<size_t>(std::abs(num_bytes_per_point));
    }

    size_t n_samples = len / bpp;
    out.reserve(n_samples);
    const char* base = raw.data() + start;
    for (size_t i = 0; i < n_samples; ++i) {
        const char* p = base + i * bpp;
        double val = 0.0;
        switch (fmt) {
            case 0: { int16_t v; std::memcpy(&v, p, sizeof(v)); val = static_cast<double>(v); break; }
            case 1: { int32_t v; std::memcpy(&v, p, sizeof(v)); val = static_cast<double>(v); break; }
            case 2: { uint32_t v; std::memcpy(&v, p, sizeof(v)); val = static_cast<double>(v); break; }
            case 3: { uint64_t v; std::memcpy(&v, p, sizeof(v)); val = static_cast<double>(v); break; }
            case 4: { float v; std::memcpy(&v, p, sizeof(v)); val = static_cast<double>(v); break; }
            case 5: { double v; std::memcpy(&v, p, sizeof(v)); val = v; break; }
            case 6: { uint8_t v; std::memcpy(&v, p, sizeof(v)); val = static_cast<double>(v); break; }
            case 7: { int8_t v; std::memcpy(&v, p, sizeof(v)); val = static_cast<double>(v); break; }
            default: { int16_t v; std::memcpy(&v, p, sizeof(v)); val = static_cast<double>(v); break; }
        }
        // apply scale + offset
        val = val * exp_dim1_scale + exp_dim1_offset;
        out.push_back(val);
    }
    return out;
}

void WfmRead::read_wfm(const std::string& filename) {
    using std::uint32_t;
    using std::int32_t;
    using std::uint16_t;
    using std::int8_t;

    std::ifstream f(filename, std::ios::binary);
    if (!f.is_open()) throw std::runtime_error("Cannot open file: " + filename);

    // reading sequence inspired by python file. Some fields may be unused here.
    try {
        // byte_order (unsigned short)
        uint16_t byte_order = read_scalar<uint16_t>(f);

        // version (8s)
        std::string version = read_str(f, 8);

        // num_digits_in_byte_count (1s)
        std::string num_digits_in_byte_count = read_str(f, 1);

        // num_bytes_to_eof (int)
        int32_t num_bytes_to_eof = read_scalar<int32_t>(f);

        // num_bytes_per_point (signed char)
        int8_t nbpp = read_scalar<int8_t>(f);
        num_bytes_per_point = static_cast<int>(nbpp);

        // byte_offset_to_curve_buffer (i)
        int32_t byte_offset_to_curve_buffer_i = read_scalar<int32_t>(f);
        byte_offset_to_curve_buffer = static_cast<uint32_t>(byte_offset_to_curve_buffer_i);

        // hor_zoom_scale (i)
        int32_t hor_zoom_scale = read_scalar<int32_t>(f);

        // hor_zoom_pos (f)
        float hor_zoom_pos = read_scalar<float>(f);

        // ver_zoom_scale (d)
        double ver_zoom_scale = read_scalar<double>(f);

        // ver_zoom_pos (f)
        float ver_zoom_pos = read_scalar<float>(f);

        // waveform_label (32s)
        std::string waveform_label = read_str(f, 32);

        // n (I)
        uint32_t n = read_scalar<uint32_t>(f);

        // header_size (H)
        uint16_t hs = read_scalar<uint16_t>(f);
        header_size = static_cast<int>(hs);

        // --- waveform header ---
        set_type = read_scalar<int32_t>(f); // 0 single waveform, 1 fast frame
        uint32_t wfm_cnt = read_scalar<uint32_t>(f);

        // skip 36 bytes
        f.seekg(36, std::ios::cur);

        exp_dim1_format = read_scalar<int32_t>(f); // data_type in python (#122)
        // skip 16 bytes
        f.seekg(16, std::ios::cur);

        // curve_ref_count etc.
        uint32_t curve_ref_count = read_scalar<uint32_t>(f);
        uint32_t num_req_fastframe = read_scalar<uint32_t>(f);
        uint32_t num_acq_fastframe = read_scalar<uint32_t>(f);

        // skip 14 bytes
        f.seekg(14, std::ios::cur);

        // --- explicit dim1 (voltage axis) ---
        exp_dim1_scale = read_scalar<double>(f);
        exp_dim1_offset = read_scalar<double>(f);
        exp_dim1_size = read_scalar<uint32_t>(f);
        std::string exp_dim1_units = read_str(f, 20);
        f.seekg(16, std::ios::cur);
        double exp_dim1_resolution = read_scalar<double>(f);
        double exp_dim1_ref_point = read_scalar<double>(f);
        exp_dim1_format = read_scalar<int32_t>(f);
        int exp_dim1_storage_type = read_scalar<int32_t>(f);
        f.seekg(20, std::ios::cur);
        double exp_dim1_user_scale = read_scalar<double>(f);
        std::string exp_dim1_user_units = read_str(f, 20);
        double exp_dim1_user_offset = read_scalar<double>(f);

        // version specific point_density: attempt safe read
        // We'll try reading 8 bytes first; if it fails, read 4 instead via restore
        try {
            // peek 8 bytes for point density
            double maybe_pd = read_scalar<double>(f);
            (void)maybe_pd;
            // then read href/trig_delay
            exp_dim1_href = read_scalar<double>(f);
            exp_dim1_trig_delay = read_scalar<double>(f);
        } catch (...) {
            // fallback: try reading 4-byte int for point_density
            f.clear();
            // reposition: after exp_dim1_user_offset we are just past it; but above failed only if double not present.
            // For safety, continue; some files may already be positioned correctly.
        }

        // --- explicit dim2 (voltage axis) ---
        // We'll read but not heavily use these fields.
        double exp_dim2_scale = read_scalar<double>(f);
        double exp_dim2_offset = read_scalar<double>(f);
        uint32_t exp_dim2_size = read_scalar<uint32_t>(f);
        std::string exp_dim2_units = read_str(f, 20);
        f.seekg(16, std::ios::cur);
        double exp_dim2_resolution = read_scalar<double>(f);
        double exp_dim2_ref_point = read_scalar<double>(f);
        int exp_dim2_format = read_scalar<int32_t>(f);
        int exp_dim2_storage_type = read_scalar<int32_t>(f);
        f.seekg(20, std::ios::cur);
        double exp_dim2_user_scale = read_scalar<double>(f);
        std::string exp_dim2_user_units = read_str(f, 20);
        double exp_dim2_user_offset = read_scalar<double>(f);
        // skip some reads for point density etc:
        f.seekg(8 + 8 + 4 + 8 + 8, std::ios::cur); // best-effort skip

        // --- implicit dimension 1 (time axis) ---
        imp_dim1_scale = read_scalar<double>(f);
        imp_dim1_offset = read_scalar<double>(f);
        imp_dim1_size = read_scalar<uint32_t>(f);
        std::string imp_dim1_units = read_str(f, 20);
        f.seekg(36, std::ios::cur);
        double imp_dim1_user_scale = read_scalar<double>(f);
        std::string imp_dim1_user_units = read_str(f, 20);
        double imp_dim1_user_offset = read_scalar<double>(f);
        f.seekg(8, std::ios::cur);
        double imp_dim1_href_local = read_scalar<double>(f);
        double imp_dim1_trig_delay_local = read_scalar<double>(f);

        // --- implicit dimension 2 (time axis) ---
        double imp_dim2_scale = read_scalar<double>(f);
        double imp_dim2_offset = read_scalar<double>(f);
        uint32_t imp_dim2_size = read_scalar<uint32_t>(f);
        std::string imp_dim2_units = read_str(f, 20);
        f.seekg(36, std::ios::cur);
        double imp_dim2_user_scale = read_scalar<double>(f);
        std::string imp_dim2_user_units = read_str(f, 20);
        double imp_dim2_user_offset = read_scalar<double>(f);
        f.seekg(8, std::ios::cur);
        double imp_dim2_href_local2 = read_scalar<double>(f);
        double imp_dim2_trig_delay_local2 = read_scalar<double>(f);

        // time base
        uint32_t time_base1_real_point_spacing = read_scalar<uint32_t>(f);
        int32_t time_base1_sweep = read_scalar<int32_t>(f);
        int32_t time_base1_type_of_base = read_scalar<int32_t>(f);

        uint32_t time_base2_real_point_spacing = read_scalar<uint32_t>(f);
        int32_t time_base2_sweep = read_scalar<int32_t>(f);
        int32_t time_base2_type_of_base = read_scalar<int32_t>(f);

        // WFM update specification (we read a few values but not storing timestamp list)
        uint32_t real_point_offset_first = read_scalar<uint32_t>(f);
        double tt_offset_first = read_scalar<double>(f);
        double frac_sec_first = read_scalar<double>(f);
        int32_t gmt_sec_first = read_scalar<int32_t>(f);
        // optional: store timestamp somewhere

        // WFM curve information
        f.seekg(10, std::ios::cur);
        uint32_t precharge_start_offset = read_scalar<uint32_t>(f);
        data_start_offset = read_scalar<uint32_t>(f);
        postcharge_start_offset = read_scalar<uint32_t>(f);
        postcharge_stop_offset = read_scalar<uint32_t>(f);
        end_of_curve_buffer_offset = read_scalar<uint32_t>(f);

        // FastFrame frames
        if (set_type == 1 && num_acq_fastframe > 1) {
            int n_extra_frames = static_cast<int>(num_acq_fastframe) - 1;
            _fast_curves.clear();
            for (int i = 0; i < n_extra_frames; ++i) {
                uint32_t state_flags = read_scalar<uint32_t>(f);
                int32_t checksum_type = read_scalar<int32_t>(f);
                uint16_t checksum = read_scalar<uint16_t>(f);
                uint32_t precharge_start = read_scalar<uint32_t>(f);
                uint32_t data_start = read_scalar<uint32_t>(f);
                uint32_t postcharge_start = read_scalar<uint32_t>(f);
                uint32_t postcharge_stop = read_scalar<uint32_t>(f);
                uint32_t end_of_curve = read_scalar<uint32_t>(f);
                _fast_curves.emplace_back(state_flags, checksum_type, checksum, precharge_start, data_start, postcharge_start, postcharge_stop, end_of_curve);
            }
        }

        // compute curve size for main (first) curve
        uint32_t curve_size_in_bytes = 0;
        try {
            curve_size_in_bytes = (postcharge_start_offset > data_start_offset) ? (postcharge_start_offset - data_start_offset) : 0;
        } catch (...) { curve_size_in_bytes = 0; }

        // compute curve buffer start
        std::streampos curve_buf_start_pos;
        if (byte_offset_to_curve_buffer != 0) {
            curve_buf_start_pos = static_cast<std::streampos>(byte_offset_to_curve_buffer);
        } else {
            curve_buf_start_pos = f.tellg();
        }

        // Read full curve buffer to memory
        f.seekg(0, std::ios::end);
        std::streampos file_size = f.tellg();
        std::streamoff remaining = file_size - curve_buf_start_pos;
        f.seekg(curve_buf_start_pos, std::ios::beg);

        size_t to_read = static_cast<size_t>(remaining);
        if (end_of_curve_buffer_offset != 0 && end_of_curve_buffer_offset < to_read) {
            to_read = end_of_curve_buffer_offset;
        }
        std::vector<char> full_curve_buf;
        full_curve_buf.resize(to_read);
        if (to_read > 0) {
            f.read(full_curve_buf.data(), to_read);
        }

        // Build list of curve specs (first + extras)
        struct CS { uint32_t data_start; uint32_t postcharge_stop; };
        std::vector<CS> all_curve_specs;
        all_curve_specs.push_back({ data_start_offset, postcharge_stop_offset });
        for (auto &tpl : _fast_curves) {
            uint32_t data_start = std::get<4>(tpl);
            uint32_t postcharge_stop = std::get<6>(tpl);
            all_curve_specs.push_back({ data_start, postcharge_stop });
        }

        // Extract frames
        frames.clear();
        for (auto &cs : all_curve_specs) {
            if (cs.data_start == 0 && cs.postcharge_stop == 0) {
                frames.emplace_back(); // empty
                continue;
            }
            uint32_t s = cs.data_start;
            uint32_t e = cs.postcharge_stop;
            // bounds-check relative to buffer
            if (s >= full_curve_buf.size() || e <= s) {
                // clamp
                s = std::min<uint32_t>(s, full_curve_buf.size());
                e = std::min<uint32_t>(e, full_curve_buf.size());
            }
            if (e <= s) {
                frames.emplace_back();
                continue;
            }
            // convert slice
            auto arr = raw_slice_to_array(full_curve_buf, s, e);
            frames.push_back(std::move(arr));
        }

        // Fill data and time using first frame
        if (!frames.empty() && !frames[0].empty()) {
            data = frames[0];
            // try to set time vector using imp_dim1_size and scale/offset
            size_t pts = data.size();
            if (imp_dim1_size != 0) pts = static_cast<size_t>(imp_dim1_size);
            time.resize(pts);
            for (size_t i = 0; i < pts; ++i) {
                time[i] = static_cast<double>(i) * imp_dim1_scale + imp_dim1_offset;
            }
        } else {
            data.clear();
            time.clear();
        }

    } catch (const std::exception& ex) {
        std::cerr << "Error parsing WFM file '" << filename << "': " << ex.what() << std::endl;
        // leave data/time empty
        data.clear();
        time.clear();
        frames.clear();
    }
}

