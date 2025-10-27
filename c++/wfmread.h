// wfmread.h
#pragma once
#include <string>
#include <vector>
#include <cstdint>

class WfmRead {
public:
    explicit WfmRead(const std::string& filename);
    ~WfmRead();

    // Raw outputs
    std::vector<double> data;                 // first frame converted to engineering units
    std::vector<double> time;                 // time vector (implicit dim1)
    std::vector<std::vector<double>> frames;  // every fast frame (may be empty vectors)
    std::string name;

    // Options / diagnostics (public for possible inspection)
    int header_size = 0;
    int set_type = 0;
    int exp_dim1_format = 0;
    int num_bytes_per_point = 0;

private:
    void read_wfm(const std::string& filename);

    // helpers
    template<typename T>
    static T read_scalar(std::ifstream& f);

    static std::string read_str(std::ifstream& f, std::size_t n);

    // convert raw bytes slice into vector<double> using current format/scale/offset
    std::vector<double> raw_slice_to_array(const std::vector<char>& raw, size_t start, size_t end);

    // stored header fields (only those used)
    double exp_dim1_scale = 1.0;
    double exp_dim1_offset = 0.0;
    uint32_t exp_dim1_size = 0;
    double imp_dim1_scale = 1.0;
    double imp_dim1_offset = 0.0;
    uint32_t imp_dim1_size = 0;
    uint32_t data_start_offset = 0;
    uint32_t postcharge_start_offset = 0;
    uint32_t postcharge_stop_offset = 0;
    uint32_t end_of_curve_buffer_offset = 0;
    uint32_t byte_offset_to_curve_buffer = 0;
    std::vector<std::tuple<uint32_t,int,int,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t>> _fast_curves;
};

