// convert_wfm_to_ROOT.cpp
#include "wfmread.h"
#include <ROOT/RDataFrame.hxx>
#include <TFile.h>
#include <TTree.h>
#include <TROOT.h>

#include <filesystem>
#include <regex>
#include <map>
#include <iostream>
#include <vector>
#include <algorithm>

namespace fs = std::filesystem;

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: convert_wfm_to_ROOT <input_dir> [output_file.root]\n";
        return 1;
    }
    std::string input_dir = argv[1];
    std::string output_file = (argc >= 3) ? argv[2] : "waveforms.root";

    // --- 1. Group files by cycle ---
    std::regex pattern(R"(cycle_(\d+)_ch(\d)\.wfm$)");
    std::map<int, std::map<int, std::string>> groups;

    for (auto &p : fs::directory_iterator(input_dir)) {
        if (!p.is_regular_file()) continue;
        std::string fname = p.path().filename().string();
        std::smatch m;
        if (std::regex_search(fname, m, pattern)) {
            int cycle = std::stoi(m[1].str());
            int ch = std::stoi(m[2].str());
            groups[cycle][ch] = p.path().string();
        }
    }

    std::cout << "Found " << groups.size() << " cycles.\n";

    // --- 2. Prepare ROOT output ---
    std::string outpath = fs::path(input_dir) / output_file;
    TFile fout(outpath.c_str(), "RECREATE");
    TTree t("waveforms", "Tektronix FastFrame waveform data");

    const int MAXPTS = 25000;
    float time_arr[MAXPTS];
    float volt_arr_ch1[MAXPTS];
    float volt_arr_ch2[MAXPTS];
    float volt_arr_ch3[MAXPTS];
    float volt_arr_ch4[MAXPTS];
    int event_number[1];
    float v1_min[1], v2_min[1], v3_min[1], v4_min[1];

    // initialize arrays
    for (int i=0;i<MAXPTS;++i) {
        time_arr[i] = 0.0f;
        volt_arr_ch1[i] = volt_arr_ch2[i] = volt_arr_ch3[i] = volt_arr_ch4[i] = 0.0f;
    }
    event_number[0] = 0;
    v1_min[0]=v2_min[0]=v3_min[0]=v4_min[0]=0.0f;

    t.Branch("time", time_arr, "time[25000]/F");
    t.Branch("v1", volt_arr_ch1, "v1[25000]/F");
    t.Branch("v2", volt_arr_ch2, "v2[25000]/F");
    t.Branch("v3", volt_arr_ch3, "v3[25000]/F");
    t.Branch("v4", volt_arr_ch4, "v4[25000]/F");
    t.Branch("event", event_number, "event[1]/I");
    t.Branch("v1_min", v1_min, "v1_min[1]/F");
    t.Branch("v2_min", v2_min, "v2_min[1]/F");
    t.Branch("v3_min", v3_min, "v3_min[1]/F");
    t.Branch("v4_min", v4_min, "v4_min[1]/F");

    // --- 3. Global event counter ---
    int global_event = 0;

    // --- 4. Loop cycles ---
    for (auto &cycle_pair : groups) {
        int cycle = cycle_pair.first;
        auto files = cycle_pair.second;
        std::cout << "Processing cycle " << cycle << "...\n";

        std::map<int, WfmRead*> wfms;
        int nframes = -1;
        for (int ch = 1; ch <= 4; ++ch) {
            auto it = files.find(ch);
            if (it == files.end()) continue;
            std::cout << "  Loading channel " << ch << " from " << it->second << "\n";
            try {
                WfmRead* w = new WfmRead(it->second);
                wfms[ch] = w;
                if (nframes == -1) nframes = static_cast<int>(w->frames.size());
                else nframes = std::min(nframes, static_cast<int>(w->frames.size()));
                std::cout << "    Number of frames: " << w->frames.size() << " (nframes min=" << nframes << ")\n";
            } catch (const std::exception& ex) {
                std::cerr << "Error loading file " << it->second << " : " << ex.what() << "\n";
            }
        }
        if (wfms.empty()) continue;

        // Loop over frames
        for (int frame = 0; frame < nframes; ++frame) {
            event_number[0] = global_event;
            // clear arrays (only up to size of available time)
            int fill_pts = 0;
            // find a time vector from any channel (prefer channel 1)
            std::vector<double> time_data;
            if (wfms.count(1) && !wfms[1]->time.empty()) time_data = wfms[1]->time;
            else {
                // search any wfms
                for (auto &p : wfms) {
                    if (!p.second->time.empty()) { time_data = p.second->time; break;}
                }
            }
            fill_pts = std::min<int>(MAXPTS, static_cast<int>(time_data.size()));

            for (int i=0;i<fill_pts;++i) time_arr[i] = static_cast<float>(time_data[i]);
            for (int i=fill_pts;i<MAXPTS;++i) time_arr[i] = 0.0f;

            // zero voltage arrays
            for (int i=0;i<MAXPTS;++i) {
                volt_arr_ch1[i]=volt_arr_ch2[i]=volt_arr_ch3[i]=volt_arr_ch4[i]=0.0f;
            }
            // Fill voltages per channel
            for (auto &p : wfms) {
                int ch = p.first;
                WfmRead* w = p.second;
                if (frame >= static_cast<int>(w->frames.size())) continue;
                auto &vdata = w->frames[frame];
                if (vdata.empty()) continue;
                int vpts = std::min<int>(MAXPTS, static_cast<int>(vdata.size()));
                for (int i=0;i<vpts;++i) {
                    float vv = static_cast<float>(vdata[i]);
                    if (ch == 1) volt_arr_ch1[i] = vv;
                    else if (ch == 2) volt_arr_ch2[i] = vv;
                    else if (ch == 3) volt_arr_ch3[i] = vv;
                    else if (ch == 4) volt_arr_ch4[i] = vv;
                }
                // compute minima for this channel for this frame
                float vmin = 0.0f;
                if (!vdata.empty()) {
                    vmin = static_cast<float>(*std::min_element(vdata.begin(), vdata.end()));
                }
                if (ch == 1) v1_min[0] = vmin;
                if (ch == 2) v2_min[0] = vmin;
                if (ch == 3) v3_min[0] = vmin;
                if (ch == 4) v4_min[0] = vmin;
            }

            t.Fill();
            global_event++;
        }

        // cleanup
        for (auto &p : wfms) {
            delete p.second;
        }
        wfms.clear();
    }

    std::cout << "Total events written: " << global_event << "\n";

    t.Write();
    fout.Close();

    std::cout << "✅ Conversion finished. Output saved as " << outpath << "\n";
    return 0;
}

