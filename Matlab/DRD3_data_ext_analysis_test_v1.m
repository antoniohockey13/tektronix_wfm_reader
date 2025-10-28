% Joaquim Pinol - 17/7/2025

% To perform timing analysis of SPS data with MSO64B,

clc
clear
%figure


% TODO: check how many cycles available

%[waveform, time, info, ~, ~] = wfm2readframe('C:\Users\propietari\Desktop\PhD\DRD3_cactusv2\cycle_0\cycle_00000_ch1.wfm', 1);
[waveform, time, info, ~, ~] = wfm2readframe('C:\Users\prop\Desktop\PhD\MCv2\DRD3_TB\run_13027\cycle_00000_ch1.wfm', 1);

% Extract event num TODO: 2 events more, consistent?
Events_Found = info.N;

%add triggernum on T
%Event_Rows = table(height(T), 5);
%varTypes = ["uint32","double","double","double","double"];
%varNames = ["Event_Line","C_DN","C_A","C_DP","MCP"];
%Tsize = [Events_Found length(varNames)];
%Osci_Data = table('Size',Tsize,'VariableTypes',varTypes,'VariableNames',varNames);

Osci_Data.C_A = zeros(Events_Found, length(waveform));
Osci_Data.C_DP = zeros(Events_Found, length(waveform));
Osci_Data.C_DN = zeros(Events_Found, length(waveform));
Osci_Data.MCP = zeros(Events_Found, length(waveform));

% Iterate through events and keep waveforms
for WaveForm_Index = 1 : Events_Found

    %CSA1 runs are inverted polarity on Digital
    [current_waveform, ~, ~, ~, ~] = wfm2readframe('C:\Users\prop\Desktop\PhD\MCv2\DRD3_TB\run_13027\cycle_00000_ch1.wfm', WaveForm_Index);
    Osci_Data.C_DN(WaveForm_Index, :) = current_waveform;

    [current_waveform, ~, ~, ~, ~] = wfm2readframe('C:\Users\prop\Desktop\PhD\MCv2\DRD3_TB\run_13027\cycle_00000_ch2.wfm', WaveForm_Index);
    Osci_Data.C_A(WaveForm_Index, :) = current_waveform;

    [current_waveform, ~, ~, ~, ~] = wfm2readframe('C:\Users\prop\Desktop\PhD\MCv2\DRD3_TB\run_13027\cycle_00000_ch3.wfm', WaveForm_Index);
    Osci_Data.C_DP(WaveForm_Index, :) = current_waveform;

    %Osci_Data.C_DN(WaveForm_Index, :) = Osci_Data.C_DP(WaveForm_Index, :) * -1.0;

    [current_waveform, ~, ~, ~, ~] = wfm2readframe('C:\Users\prop\Desktop\PhD\MCv2\DRD3_TB\run_13027\cycle_00000_ch4.wfm', WaveForm_Index);
    Osci_Data.MCP(WaveForm_Index, :) = current_waveform;

end

Events_Found
Events_to_Cut = zeros(height(Events_Found), 1);

Extracted_Data.CH1 = zeros(height(Event_Rows), 1024-10);
Extracted_Data.CH5 = zeros(height(Event_Rows), 1024-14);
Extracted_Data.CH14 = zeros(height(Event_Rows), 1024-14);
Extracted_Data.CH15 = zeros(height(Event_Rows), 1024-14);

for EventsFound_Index = 1 : Events_Found

    Extracted_Data.CH1(EventsFound_Index, :) = table2array(T(Event_Rows.CH1(EventsFound_Index),11:1024));
    Extracted_Data.CH5(EventsFound_Index, :) = table2array(T(Event_Rows.CH5(EventsFound_Index),15:1024));
    Extracted_Data.CH14(EventsFound_Index, :) = table2array(T(Event_Rows.CH14(EventsFound_Index),15:1024));
    Extracted_Data.CH15(EventsFound_Index, :) = table2array(T(Event_Rows.CH15(EventsFound_Index),15:1024));

end

%{
rf = rowfilter(T);
PoI_Data = T(rf.Var1 == 0 & rf.Var2 == pixel_Col & rf.Var3 == pixel_Row & rf.Var5 ~= 127 & rf.Var5 ~= 0,:);

nexttile
histogram(PoI_Data.Var5,127)
ylim([0 150]) %150 needs to be obtained from data, limits the Y-axis size
ylabel('Counts', 'FontSize', 14);
xlabel('ToA [DAC]', 'FontSize', 14);
title('ToA distribution')

nexttile
histogram(PoI_Data.Var4,256)
ylabel('Counts', 'FontSize', 14);
xlabel('ToT [DAC]', 'FontSize', 14);
title('ToT distribution')
%}
%{
% Find available Osci data files
FileList = dir(fullfile("Osci_Data/r67/", '*.mat'));
%FileList_Table = struct2table(FileList);
path_to_Osci_files = "Osci_Data/r67";
%}
miniCactustime_Analog_time = zeros (Events_Found, 1);
miniCactustime_Analog_Amplitude = zeros (Events_Found, 1);
miniCactustime_Digital_time = zeros (Events_Found, 1);
MCP1_time = zeros (Events_Found, 1);
MCP1_Amplitude = zeros (Events_Found, 1);
MCP2_time = zeros (Events_Found, 1);
MCP2_Amplitude = zeros (Events_Found, 1);

varTypes = ["uint32","double","double","double","double","double","double","double","double"];
varNames = ["Event_Num","mCv2_A_time","mCv2_A_ampl","mCv2_D_time","mCv2_D_ampl","PMT1_time","PMT1_ampl","PMT2_time","PMT2_ampl",];
Tsize = [Events_Found length(varNames)];
Event_Data = table('Size',Tsize,'VariableTypes',varTypes,'VariableNames',varNames);

Fit_Pol_Order = 1;
   Fit_points_0_5 = 5;

%Event_Data.Event_Num = zeros(height(Event_Rows), 1);

for Extracted_Data_Index = 1 : Events_Found

    %FileName = path_to_Osci_files + '/' + FileList(File_Index).name;
    %fileID = open(FileName);
    Event_Data.Event_Num(Extracted_Data_Index) = Extracted_Data_Index;

    % Find Threshold
    miniCactustime_Analog_max = max(Extracted_Data.CH1(Extracted_Data_Index,:));
    miniCactustime_Analog_min = min(Extracted_Data.CH1(Extracted_Data_Index,:));
    miniCactustime_Analog_thr = (miniCactustime_Analog_max - miniCactustime_Analog_min) / 2 + miniCactustime_Analog_min;
    miniCactustime_Analog_Amplitude(Extracted_Data_Index) = 0.001;
    miniCactustime_Analog_Amplitude(Extracted_Data_Index) = miniCactustime_Analog_max - miniCactustime_Analog_min;
    Event_Data.mCv2_A_ampl(Extracted_Data_Index) = miniCactustime_Analog_max - miniCactustime_Analog_min;
    
    if miniCactustime_Analog_Amplitude(Extracted_Data_Index) < 0.1
        Events_to_Cut(Extracted_Data_Index) = 1;
    end

    if miniCactustime_Analog_Amplitude(Extracted_Data_Index) > 1
        Events_to_Cut(Extracted_Data_Index) = 1;
    end

    prev_Value = miniCactustime_Analog_min;
    for index = 2 : 1000
        value = Extracted_Data.CH1(Extracted_Data_Index, index);
        if (value > miniCactustime_Analog_thr)
            miniCactustime_Analog_time(Extracted_Data_Index) = double(index) * 312.5;% / 1024.0; %to convert to ps
            Event_Data.mCv2_A_time(Extracted_Data_Index) = double(index) * 312.5;% / 1024.0; %to convert to ps
            break
        end
        prev_Value = value;
    end


    % Find Threshold
    miniCactustime_Digital_max = max(Extracted_Data.CH5(Extracted_Data_Index,:));
    miniCactustime_Digital_min = min(Extracted_Data.CH5(Extracted_Data_Index,:));
    miniCactustime_Digital_thr = (miniCactustime_Digital_max - miniCactustime_Digital_min) / 2 + miniCactustime_Digital_min;
    miniCactustime_Digital_Amplitude(Extracted_Data_Index) = 0.001;
    miniCactustime_Digital_Amplitude(Extracted_Data_Index) = miniCactustime_Digital_max - miniCactustime_Digital_min;
    Event_Data.mCv2_D_ampl(Extracted_Data_Index) = miniCactustime_Digital_max - miniCactustime_Digital_min;
    
    if miniCactustime_Analog_Amplitude(Extracted_Data_Index) < 0.1
        Events_to_Cut(Extracted_Data_Index) = 1;
    end

    if miniCactustime_Analog_Amplitude(Extracted_Data_Index) > 10
        Events_to_Cut(Extracted_Data_Index) = 1;
    end

    prev_Value = miniCactustime_Digital_min;
    for index = 2 : 1000
        value = Extracted_Data.CH5(Extracted_Data_Index, index);
        if (value > miniCactustime_Digital_thr)
            miniCactustime_Digital_time(Extracted_Data_Index) = double(index) * 312.5;% / 1024.0; %to convert to ps
            Event_Data.mCv2_D_time(Extracted_Data_Index) = double(index) * 312.5;% / 1024.0; %to convert to ps
            break
        end
        prev_Value = value;
    end
    
    % Find Threshold
    MCP1_max = max(Extracted_Data.CH14(Extracted_Data_Index,:));
    MCP1_min = min(Extracted_Data.CH14(Extracted_Data_Index,:));
    MCP1_thr = (MCP1_max - MCP1_min) / 2 + MCP1_min;
    MCP1_Amplitude(Extracted_Data_Index) = 0.001;
    MCP1_Amplitude(Extracted_Data_Index) = MCP1_max - MCP1_min;
    Event_Data.PMT1_ampl(Extracted_Data_Index) = MCP1_max - MCP1_min;

    if MCP1_Amplitude(Extracted_Data_Index) < 0.6
        Events_to_Cut(Extracted_Data_Index) = 1;
    end
    
    prev_Value = MCP1_min;
    for index = 2 : 1000
        value = Extracted_Data.CH14(Extracted_Data_Index, index);
        if (value < MCP1_thr)
            MCP1_time(Extracted_Data_Index) = double(index)* 312.5;% * 1e-12;% / 1024.0; %to convert to ps
            Event_Data.PMT1_time(Extracted_Data_Index) = double(index) * 312.5;% / 1024.0; %to convert to ps
            break
        end
        prev_Value = value;
    end

    % Find Threshold
    MCP2_max = max(Extracted_Data.CH15(Extracted_Data_Index,:));
    MCP2_min = min(Extracted_Data.CH15(Extracted_Data_Index,:));
    MCP2_thr = (MCP2_max - MCP2_min) / 2 + MCP2_min;
    MCP2_Amplitude(Extracted_Data_Index) = 0.001;
    MCP2_Amplitude(Extracted_Data_Index) = MCP2_max - MCP2_min;
    Event_Data.PMT2_ampl(Extracted_Data_Index) = MCP2_max - MCP2_min;
    
    if MCP2_Amplitude(Extracted_Data_Index) < 0.4
        Events_to_Cut(Extracted_Data_Index) = 1;
    end

    prev_Value = MCP2_min;
    for index = 2 : 1000
        value = Extracted_Data.CH15(Extracted_Data_Index, index);
        if (value < MCP2_thr)
            MCP2_time(Extracted_Data_Index) = double(index) * 312.5;% * 1e-12;% / 1024.0; %to convert to ps
            Event_Data.PMT2_time(Extracted_Data_Index) = double(index) * 312.5;% / 1024.0; %to convert to ps
            break
            break
        end
        prev_Value = value;
    end



    

end

nexttile
histogram(miniCactustime_Analog_Amplitude,256)
ylabel('Counts', 'FontSize', 14);
xlabel('Amplitude [mV]', 'FontSize', 14);
title('mCv2 Amp distribution')

nexttile
histogram(miniCactustime_Digital_Amplitude,256)
ylabel('Counts', 'FontSize', 14);
xlabel('Amplitude [mV]', 'FontSize', 14);
title('mCv2 Digital Amp distribution')

nexttile
histogram(MCP1_Amplitude,256)
ylabel('Counts', 'FontSize', 14);
xlabel('Amplitude [mV]', 'FontSize', 14);
title('MCP1 Amp distribution')

nexttile
histogram(MCP2_Amplitude,256)
ylabel('Counts', 'FontSize', 14);
xlabel('Amplitude [mV]', 'FontSize', 14);
title('MCP2 Amp distribution')

%for File_Index = 1 : MaxEvents_to_Analyze
%    if CLKtime(File_Index) > 10 & LGADtime(File_Index) > 10
%       T.Validtime = 1
%    end
%end

Delta_mCv2_MCP1 = miniCactustime_Analog_time - MCP1_time;
Delta_MCP1_MCP2 = MCP1_time - MCP2_time;


nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(Delta_mCv2_MCP1,250);
ylabel('Counts', 'FontSize', 14);
xlabel('mCv2 - MCP1 [ps]', 'FontSize', 14);
%h.BinLimits=[8e4 12e4];
%h.BinLimits=[80 120];
title('Delta mCv2 MCP1');

nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(Delta_MCP1_MCP2,250);
ylabel('Counts', 'FontSize', 14);
xlabel('MCP1 - MCP2 [ps]', 'FontSize', 14);
%h.BinLimits=[-1e-12 1e-12];
%h.BinLimits=[80 120];
title('Delta MCP1 MCP2');

nexttile
%histfit(Delta_mCv2_MCP1, 256);
%pd = fitdist (Delta_mCv2_MCP1, 'Normal')

% Define the bin edges you want
EDGES = -2e4:100:-1.5e4;
%EDGES = 80:2:120;

% Bin the data according to the predefined edges:
Y = histcounts(Delta_mCv2_MCP1, EDGES);

% Fit a normal distribution using the curve fitting tool:
binCenters = conv(EDGES, [0.5, 0.5], 'valid'); % moving average
[xData, yData] = prepareCurveData( binCenters, Y );

ft = fittype( 'gauss1' );
fitresult = fit( xData, yData, ft );
%disp(fitresult); % optional

% Plot fit with data (optional)
%figure(); 
histogram(Delta_mCv2_MCP1, EDGES); hold on; grid on;
plot(fitresult);
title('Delta mCv2 MCP1 - fit');

mu_mCv2_MCP1 = fitresult.b1;
sigma_mCv2_MCP1 = fitresult.c1/sqrt(2)


nexttile
%histfit(Delta_mCv2_MCP1, 256);
%pd = fitdist (Delta_mCv2_MCP1, 'Normal')

% Define the bin edges you want
EDGES = -3e3:100:3e3;
%EDGES = 80:2:120;

% Bin the data according to the predefined edges:
Y = histcounts(Delta_MCP1_MCP2, EDGES);

% Fit a normal distribution using the curve fitting tool:
binCenters = conv(EDGES, [0.5, 0.5], 'valid'); % moving average
[xData, yData] = prepareCurveData( binCenters, Y );

ft = fittype( 'gauss1' );
fitresult = fit( xData, yData, ft );
%disp(fitresult); % optional

% Plot fit with data (optional)
%figure(); 
histogram(Delta_MCP1_MCP2, EDGES); hold on; grid on;
plot(fitresult);
title('Delta MCP1 MCP2 - fit');

mu_MCP1_MCP2 = fitresult.b1;
sigma_MCP1_MCP2 = fitresult.c1/sqrt(2)

rf = rowfilter(Event_Data);
Filtered_Events = Event_Data(rf.mCv2_A_ampl > 0.1 & rf.PMT1_ampl > 0.6 & rf.PMT2_ampl > 0.4,:);


Filtered_Delta_mCv2_MCP1 = Filtered_Events.mCv2_A_time - Filtered_Events.PMT1_time;
Filtered_Delta_MCP1_MCP2 = Filtered_Events.PMT1_time - Filtered_Events.PMT2_time;


nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(Filtered_Delta_mCv2_MCP1,250);
ylabel('Counts', 'FontSize', 14);
xlabel('mCv2 - MCP1 [ps]', 'FontSize', 14);
%h.BinLimits=[8e4 12e4];
%h.BinLimits=[80 120];
title('Delta mCv2 MCP1');

nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(Filtered_Delta_MCP1_MCP2,250);
ylabel('Counts', 'FontSize', 14);
xlabel('MCP1 - MCP2 [ps]', 'FontSize', 14);
%h.BinLimits=[-1e-12 1e-12];
%h.BinLimits=[80 120];
title('Delta MCP1 MCP2');

nexttile
%histfit(Delta_mCv2_MCP1, 256);
%pd = fitdist (Delta_mCv2_MCP1, 'Normal')

% Define the bin edges you want
EDGES = -2e4:100:-1.5e4;
%EDGES = 80:2:120;

% Bin the data according to the predefined edges:
Y = histcounts(Filtered_Delta_mCv2_MCP1, EDGES);

% Fit a normal distribution using the curve fitting tool:
binCenters = conv(EDGES, [0.5, 0.5], 'valid'); % moving average
[xData, yData] = prepareCurveData( binCenters, Y );

ft = fittype( 'gauss1' );
fitresult = fit( xData, yData, ft );
%disp(fitresult); % optional

% Plot fit with data (optional)
%figure(); 
histogram(Filtered_Delta_mCv2_MCP1, EDGES); hold on; grid on;
plot(fitresult);
title('Delta mCv2 MCP1 Filtered - fit');

mu_mCv2_MCP1_Filtered = fitresult.b1;
sigma_mCv2_MCP1_Filtered = fitresult.c1/sqrt(2)


nexttile
%histfit(Delta_mCv2_MCP1, 256);
%pd = fitdist (Delta_mCv2_MCP1, 'Normal')

% Define the bin edges you want
EDGES = -400:1:-200;
%EDGES = 80:2:120;

% Bin the data according to the predefined edges:
Y = histcounts(Filtered_Delta_MCP1_MCP2, EDGES);

% Fit a normal distribution using the curve fitting tool:
binCenters = conv(EDGES, [0.5, 0.5], 'valid'); % moving average
[xData, yData] = prepareCurveData( binCenters, Y );

ft = fittype( 'gauss1' );
fitresult = fit( xData, yData, ft );
%disp(fitresult); % optional

% Plot fit with data (optional)
%figure(); 
histogram(Filtered_Delta_MCP1_MCP2, EDGES); hold on; grid on;
plot(fitresult);
title('Delta MCP1 MCP2 Filtered - fit');

mu_MCP1_MCP2_Filtered = fitresult.b1;
sigma_MCP1_MCP2_Filtered = fitresult.c1/sqrt(2)
%rf = rowfilter(Event_Data);
%Filtered_Events = T(rf.mCv2_A_ampl  0 & rf.Var2 == pixel_Col & rf.Var3 == pixel_Row & rf.Var5 ~= 127 & rf.Var5 ~= 0,:);


%figure
%nexttile
%Delta_87LGAD = zeros (MaxEvents_to_Analyze, 1);
%Delta_CLKtime_LGADtime = zeros (MaxEvents_to_Analyze, 1);
%ToA_t_LSB = zeros (MaxEvents_to_Analyze, 1);
%{
PoI_Data.TriggerCol = PoI_Data.TriggerCol + 1;

Hit_in_PoI_Index = 1

for Event_Index = 1 : height(LGADtime)

    if PoI_Data.TriggerCol(Hit_in_PoI_Index) == Event_Index
        
        %PoI_Data.TriggerCol(Event_Index)
        %Event_Index
        %Hit_in_PoI_Index = Hit_in_PoI_Index + 1;
        %PoI_Data.TriggerCol(Hit_in_PoI_Index+1);

        % Stop after amount of triggers reaches max specified
        if PoI_Data.TriggerCol(Hit_in_PoI_Index) >= MaxEvents_to_Analyze
            break
        end

        %if CLKtime(PoI_Data.TriggerCol(Hit_in_PoI_Index)) > 10
            Delta_87LGAD(Hit_in_PoI_Index) = (PoI_Data.Var5(Hit_in_PoI_Index) * 15.8) - CLKtime(PoI_Data.TriggerCol(Hit_in_PoI_Index)) + LGADtime(PoI_Data.TriggerCol(Hit_in_PoI_Index));
            ToA_relocated(Hit_in_PoI_Index) = PoI_Data.Var5(Hit_in_PoI_Index);
            Delta_CLKtime_LGADtime(Hit_in_PoI_Index) = -CLKtime(PoI_Data.TriggerCol(Hit_in_PoI_Index)) + LGADtime(PoI_Data.TriggerCol(Hit_in_PoI_Index));
        %end

        %disp ('Matched')
        %Event_Index
        %disp ('to')
        %Hit_in_PoI_Index
        Hit_in_PoI_Index = Hit_in_PoI_Index + 1;
    else
        %disp ('Skipped')
        %Event_Index
    end

    

end

nexttile
k = histogram(Delta_87LGAD,250);
k.BinLimits=[1000 3500];
title('DeltaT p8-7 to LGAD');


nexttile
%histfit(Delta_PaLGAD, 256);
%pd = fitdist (Delta_PaLGAD, 'Normal')


% Define the bin edges you want
EDGES = 1000:50:3500;

% Bin the data according to the predefined edges:
Y = histcounts(Delta_87LGAD, EDGES);

% Fit a normal distribution using the curve fitting tool:
binCenters = conv(EDGES, [0.5, 0.5], 'valid'); % moving average
[xData, yData] = prepareCurveData( binCenters, Y );

ft = fittype( 'gauss1' );
fitresult = fit( xData, yData, ft );
%disp(fitresult); % optional

% Plot fit with data (optional)
%figure(); 
histogram(Delta_87LGAD, EDGES); hold on; grid on;
plot(fitresult);
title('DeltaT p8-7 to LGAD - fit');

mu_87 = fitresult.b1
sigma_87 = fitresult.c1/sqrt(2)


%figure
%nexttile
%j = histogram(Delta_CLKtime_LGADtime, 250);
%title('DeltaT CLKtime to LGAD');

%figure
nexttile
j = histogram(CLKtime, 250);
title('CLKtime');

%figure
nexttile
j = histogram(LGADtime, 250);
title('LGADtime');

nexttile
%figure
l = histogram2(ToA_relocated, Delta_CLKtime_LGADtime,'DisplayStyle','tile','ShowEmptyBins','on','NumBins',200);
%l.BinLimits=[1000 3500];
title('Toa vs LGAD-CLK');
%}