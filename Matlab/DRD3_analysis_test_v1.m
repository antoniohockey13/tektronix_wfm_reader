
%do tw plot!
% re-evaluate cuts
%more precise ToT meas

% Missing to do digital TWd averaging the two digitals

%Events_to_Cut = zeros(1, Events_Found);

% Delay samples for the CFD, dependant on the GS/s rate
CFD_Delay_Samples = 200;
CFD_Delay_Samples_MCP = 5;
CFD_Fraction = 0.4;
Sample_Period = 1.00 / 5e10;
Sample_Period_ps = Sample_Period * 1e12;
Min_Amplitude = 0.05; % Minimum amplitude to consider the data point

varTypes = ["uint32","double","double","double","double","double","double"];
varNames = ["Event_Num","C_A_time","C_DP_time","C_DN_time","MCP_time","C_A_ampl","C_D_ToT"];
Tsize = [Events_Found length(varNames)];
CFD_times = table('Size',Tsize,'VariableTypes',varTypes,'VariableNames',varNames);

for Event = 1 : Events_Found

    CFD_times.Event_Num(Event) = Event;

end

for Event = 1 : Events_Found
    
    Baseline_at_0 = Osci_Data.C_A(Event,:) - 0.665;
    
    Fraction = cat(2, Baseline_at_0 * CFD_Fraction, zeros(1, CFD_Delay_Samples));
    
    Delayed = cat(2, zeros(1, CFD_Delay_Samples), Baseline_at_0);

    %Subs_Frac_Del = Fraction - Delayed;        % Not used
    
    Subs_Del_Frac = Delayed - Fraction;

    % Find Threshold
    [Max_Value, Max_Index] = max(Subs_Del_Frac);
    [Min_Value, Min_Index] = min(Subs_Del_Frac);
    Analog_thr = 0.00; % (Max_Value - Min_Value) / 2; %0.00;
    
    if (Max_Value - Min_Value) > Min_Amplitude
        for index = Min_Index : Max_Index
            value = Subs_Del_Frac(index);
            if (value > Analog_thr)
                CFD_times.C_A_time(Event) = double(index) * Sample_Period_ps;   % Time expressed in ps (check sample rate is ok at start)
                Analog_index_thr = index;
                CFD_times.C_A_ampl(Event) = Max_Value - Min_Value;
                break
            end
        end
    end

    plot = 0;

    if plot

        figure
        plot(Osci_Data.C_A(Event,:))
        clear hold on
        plot(Baseline_at_0)
        hold on
        plot(Fraction)
        hold on
        plot(Delayed)
        hold on
        plot(Subs_Del_Frac)
        hold on

    end

end

for Event = 1 : Events_Found
    
    Baseline_at_0 = Osci_Data.C_DP(Event,:) - 0.0;
    
    Fraction = cat(2, Baseline_at_0 * CFD_Fraction, zeros(1, CFD_Delay_Samples));
    
    Delayed = cat(2, zeros(1, CFD_Delay_Samples), Baseline_at_0);

    %Subs_Frac_Del = Fraction - Delayed;        % Not used
    
    Subs_Del_Frac = Delayed - Fraction;

    % Find Threshold
    [Max_Value, Max_Index] = max(Subs_Del_Frac);
    [Min_Value, Min_Index] = min(Subs_Del_Frac);
    Analog_thr = 0.00; % (Max_Value - Min_Value) / 2; %0.00;

    Above_thr = zeros(1, length(Osci_Data.C_DP(Event,:)));
    Above_thr(Osci_Data.C_DP(Event, :) > 0.1) = 1;
    Above_thr(1) = 0;
    
    
    if (Max_Value - Min_Value) > Min_Amplitude

        [pks,locs,w,p] =findpeaks(Above_thr, 'MinPeakWidth', 1000);

        if ~isempty(w)
            CFD_times.C_D_ToT(Event) = w(1) * Sample_Period_ps;   % Time expressed in ps (check sample rate is ok at start)
        end

        for index = Min_Index : Max_Index
            value = Subs_Del_Frac(index);
            if (value > Analog_thr)
                CFD_times.C_DP_time(Event) = double(index) * Sample_Period_ps;   % Time expressed in ps (check sample rate is ok at start)
                Analog_index_thr = index;
                break
            end
        end
    end

    plot = 0;

    if plot

        figure
        plot(Osci_Data.C_DP(Event,:))
        clear hold on
        plot(Baseline_at_0)
        hold on
        plot(Fraction)
        hold on
        plot(Delayed)
        hold on
        plot(Subs_Del_Frac)
        hold on

    end

end

for Event = 1 : Events_Found
    
    Baseline_at_0 = Osci_Data.C_DN(Event,:) - 0.0;
    
    Fraction = cat(2, Baseline_at_0 * CFD_Fraction, zeros(1, CFD_Delay_Samples));
    
    Delayed = cat(2, zeros(1, CFD_Delay_Samples), Baseline_at_0);

    %Subs_Frac_Del = Fraction - Delayed;        % Not used
    
    Subs_Del_Frac = Delayed - Fraction;

    % Find Threshold
    [Max_Value, Max_Index] = max(Subs_Del_Frac);
    [Min_Value, Min_Index] = min(Subs_Del_Frac);
    Analog_thr = 0.00; % (Max_Value - Min_Value) / 2; %0.00;
    
    if (Max_Value - Min_Value) > Min_Amplitude
        for index = Max_Index : Min_Index
            value = Subs_Del_Frac(index);
            if (value < Analog_thr)
                CFD_times.C_DN_time(Event) = double(index) * Sample_Period_ps;   % Time expressed in ps (check sample rate is ok at start)
                Analog_index_thr = index;
                break
            end
        end
    end

    plot = 0;

    if plot

        figure
        plot(Osci_Data.C_DN(Event,:))
        clear hold on
        plot(Baseline_at_0)
        hold on
        plot(Fraction)
        hold on
        plot(Delayed)
        hold on
        plot(Subs_Del_Frac)
        hold on

    end

end

for Event = 1 : Events_Found
    
    Baseline_at_0 = Osci_Data.MCP(Event,:) - 0.0;
    
    Fraction = cat(2, Baseline_at_0 * CFD_Fraction, zeros(1, CFD_Delay_Samples_MCP));
    
    Delayed = cat(2, zeros(1, CFD_Delay_Samples_MCP), Baseline_at_0);

    %Subs_Frac_Del = Fraction - Delayed;        % Not used
    
    Subs_Del_Frac = Delayed - Fraction;

    % Find Threshold
    [Max_Value, Max_Index] = max(Subs_Del_Frac);
    [Min_Value, Min_Index] = min(Subs_Del_Frac);
    Analog_thr = 0.00; % (Max_Value - Min_Value) / 2; %0.00;
    
    if (Max_Value - Min_Value) > Min_Amplitude
        for index = Max_Index : Min_Index
            value = Subs_Del_Frac(index);
            if (value < Analog_thr)
                CFD_times.MCP_time(Event) = double(index) * Sample_Period_ps;   % Time expressed in ps (check sample rate is ok at start)
                Analog_index_thr = index;
                break
            end
        end
    end

    plot = 0;

    if plot

        figure
        plot(Osci_Data.MCP(Event,:))
        clear hold on
        plot(Baseline_at_0)
        hold on
        plot(Fraction)
        hold on
        plot(Delayed)
        hold on
        plot(Subs_Del_Frac)
        hold on

    end

end

NF_Delta_C_A_to_MCP = CFD_times.C_A_time - CFD_times.MCP_time;

NF_Delta_C_DP_to_MCP = CFD_times.C_DP_time - CFD_times.MCP_time;
NF_Delta_C_DN_to_MCP = CFD_times.C_DN_time - CFD_times.MCP_time;
NF_Delta_C_D_to_MCP = ((CFD_times.C_DP_time + CFD_times.C_DP_time) / 2) - CFD_times.MCP_time;

nexttile
h=histogram(CFD_times.C_A_time, 250);
title('mCv2 Analog time');
nexttile
h=histogram(CFD_times.C_DP_time, 250);
title('mCv2 DP time');
nexttile
h=histogram(CFD_times.C_DN_time, 250);
title('mCv2 DN time');
nexttile
h=histogram(CFD_times.MCP_time, 250);
title('mCv2 MCP time');

nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(NF_Delta_C_A_to_MCP,250);
ylabel('Counts', 'FontSize', 14);
xlabel('Cactus_Analog - MCP [ps]', 'FontSize', 14);
%h.BinLimits=[-1e-12 1e-12];
%h.BinLimits=[80 120];
title('No Filter - Delta mCv2_Analog MCP');

nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(NF_Delta_C_D_to_MCP,250);
ylabel('Counts', 'FontSize', 14);
xlabel('Cactus_Digital - MCP [ps]', 'FontSize', 14);
%h.BinLimits=[-1e-12 1e-12];
%h.BinLimits=[80 120];
title('No Filter - Delta mCv2_Digital MCP');

figure

rf = rowfilter(CFD_times);
Filtered_Events = CFD_times(rf.C_A_time ~= 0 & rf.C_DP_time ~= 0 & rf.C_DN_time ~= 0 & rf.MCP_time ~= 0,:);


Delta_C_A_to_MCP = Filtered_Events.C_A_time - Filtered_Events.MCP_time;

Delta_C_DP_to_MCP = Filtered_Events.C_DP_time - Filtered_Events.MCP_time;
Delta_C_DN_to_MCP = Filtered_Events.C_DN_time - Filtered_Events.MCP_time;
Delta_C_D_to_MCP = ((Filtered_Events.C_DP_time + Filtered_Events.C_DP_time) / 2) - Filtered_Events.MCP_time;

nexttile
h=histogram(Filtered_Events.C_A_time, 250);
title('mCv2 Analog time');
nexttile
h=histogram(Filtered_Events.C_DP_time, 250);
title('mCv2 DP time');
nexttile
h=histogram(Filtered_Events.C_DN_time, 250);
title('mCv2 DN time');
nexttile
h=histogram(Filtered_Events.MCP_time, 250);
title('mCv2 MCP time');

nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(Delta_C_A_to_MCP,250);
ylabel('Counts', 'FontSize', 14);
xlabel('Cactus_Analog - MCP [ps]', 'FontSize', 14);
%h.BinLimits=[-1e-12 1e-12];
%h.BinLimits=[80 120];
title('Delta mCv2_Analog MCP');

nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(Delta_C_D_to_MCP,250);
ylabel('Counts', 'FontSize', 14);
xlabel('Cactus_Digital - MCP [ps]', 'FontSize', 14);
%h.BinLimits=[-1e-12 1e-12];
%h.BinLimits=[80 120];
title('Delta mCv2_Digital MCP');

nexttile
% Define the bin edges you want
EDGES = 5000:50:15000;
%EDGES = -5e2:10:5e2;

% Bin the data according to the predefined edges:
Y = histcounts(Delta_C_A_to_MCP, EDGES);

% Fit a normal distribution using the curve fitting tool:
binCenters = conv(EDGES, [0.5, 0.5], 'valid'); % moving average
[xData, yData] = prepareCurveData( binCenters, Y );

ft = fittype( 'gauss1' );
fitresult = fit( xData, yData, ft );
%disp(fitresult); % optional

% Plot fit with data (optional)
%figure(); 
histogram(Delta_C_A_to_MCP, EDGES); hold on; grid on;
clear plot
plot(fitresult)
title('Delta mCv2 Ana to MCP - fit');

Delta_C_A_to_MCP_mu = fitresult.b1;
Delta_C_A_to_MCP_sigma = fitresult.c1/sqrt(2)


figure
%histfit(Delta_mCv2_MCP1, 256);
%pd = fitdist (Delta_mCv2_MCP1, 'Normal')

% Define the bin edges you want
EDGES = 5000:50:15000;
%EDGES = -5e2:10:5e2;

% Bin the data according to the predefined edges:
Y = histcounts(Delta_C_D_to_MCP, EDGES);

% Fit a normal distribution using the curve fitting tool:
binCenters = conv(EDGES, [0.5, 0.5], 'valid'); % moving average
[xData, yData] = prepareCurveData( binCenters, Y );

ft = fittype( 'gauss1' );
fitresult = fit( xData, yData, ft );
%disp(fitresult); % optional

% Plot fit with data (optional)
%figure(); 
histogram(Delta_C_D_to_MCP, EDGES); hold on; grid on;
plot(fitresult)
title('Delta mCv2 Dig to MCP - fit');

Delta_C_D_to_MCP_mu = fitresult.b1;
Delta_C_D_to_MCP_sigma = fitresult.c1/sqrt(2)

% TWa correction with Analog amplitude (only for digital)

TWa = table();
TWa.TOT = Filtered_Events.C_A_ampl;%CFD_times.mCv2_D_TOT;
TWa.TOA = Delta_C_D_to_MCP;

%rf = rowfilter(TW);
%TW_Filtered_Events = TW(rf.TOT > 0.03,:);%rf.TOT > 0.08 & rf.TOT < 25 & rf.TOA > -1.9e4 & rf.TOA < -1.6e4, :);

nexttile;
scatter(TWa.TOT, TWa.TOA);
title('Pre-TWa mCv2 Digital to MCP scatter');

x_min_Index = 0.04;
x_max_Index = 0.4;

hold on;
x = x_min_Index : 0.001 : x_max_Index;
%y = y_min_Index : y_max_Index;
% Fit line to data using polyfit
[c, S] = polyfit(TWa.TOT , TWa.TOA, 4);
% Display evaluated equation y = m*x + b
%disp(['Equation is y = ' num2str(c(1)) '*x + ' num2str(c(2))])
% Evaluate fit equation using polyval
[y_est, delta] = polyval(c, x, S);
% Add trend line to plot
%hold on
plot(x, y_est, 'r--', 'LineWidth', 2)
%hold on
%plot(x,y_est+2*delta,'m--',x,y_est-2*delta,'m--')
hold off

%x_sol = fzero(@(x) polyval(c, x)-0, rand());

%Analog_time_Rsq(Event) = S.rsquared;
%CFD_times.PMT1_R_2(Event) = S.rsquared;

for index = 1 : length(TWa.TOA)
    TWa_Delta_C_D_to_MCP = Delta_C_D_to_MCP - polyval(c, TWa.TOT);
end


TWa_ed = table();
TWa_ed.TOT = TWa.TOT;
TWa_ed.TOA = TWa_Delta_C_D_to_MCP;

%rf = rowfilter(TWa_ed);
%TWed_Filtered_Events = TWa_ed(rf.TOT > 0.03, :);

nexttile;
scatter(TWa_ed.TOT, TWa_ed.TOA);
title('Post-TWa mCv2 Digital to MCP scatter');

nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(TWa_Delta_C_D_to_MCP,250);
ylabel('Counts', 'FontSize', 14);
xlabel('Cactus Digital - MCP [ps]', 'FontSize', 14);
%h.BinLimits=[-1e-12 1e-12];
%h.BinLimits=[80 120];
title('Delta TWa mCv2 Digital to MCP');

nexttile
% Define the bin edges you want
EDGES = -1500:50:1500;
%EDGES = -5e2:10:5e2;

% Bin the data according to the predefined edges:
Y = histcounts(TWa_Delta_C_D_to_MCP, EDGES);

% Fit a normal distribution using the curve fitting tool:
binCenters = conv(EDGES, [0.5, 0.5], 'valid'); % moving average
[xData, yData] = prepareCurveData( binCenters, Y );

ft = fittype( 'gauss1' );
fitresult = fit( xData, yData, ft );
%disp(fitresult); % optional

% Plot fit with data (optional)
%figure(); 
histogram(TWa_Delta_C_D_to_MCP, EDGES); hold on; grid on;
clear plot
plot(fitresult)
title('Delta TWa mCv2 Digital to MCP');

TWa_Delta_C_D_to_MCP_mu = fitresult.b1;
TWa_Delta_C_D_to_MCP_sigma = fitresult.c1/sqrt(2)


% TWd correction with Analog amplitude (only for digital)

TWd = table();
TWd.TOT = Filtered_Events.C_D_ToT;%CFD_times.mCv2_D_TOT;
TWd.TOA = Delta_C_D_to_MCP;

%rf = rowfilter(TW);
%TW_Filtered_Events = TW(rf.TOT > 0.03,:);%rf.TOT > 0.08 & rf.TOT < 25 & rf.TOA > -1.9e4 & rf.TOA < -1.6e4, :);

figure;
scatter(TWd.TOT, TWd.TOA);
title('Pre-TWd mCv2 Digital to MCP scatter');

x_min_Index = 0.04;
x_max_Index = 0.4;

hold on;
x = x_min_Index : 0.001 : x_max_Index;
%y = y_min_Index : y_max_Index;
% Fit line to data using polyfit
[c, S] = polyfit(TWd.TOT , TWd.TOA, 4);
% Display evaluated equation y = m*x + b
%disp(['Equation is y = ' num2str(c(1)) '*x + ' num2str(c(2))])
% Evaluate fit equation using polyval
[y_est, delta] = polyval(c, x, S);
% Add trend line to plot
%hold on
plot(x, y_est, 'r--', 'LineWidth', 2)
%hold on
%plot(x,y_est+2*delta,'m--',x,y_est-2*delta,'m--')
hold off

%x_sol = fzero(@(x) polyval(c, x)-0, rand());

%Analog_time_Rsq(Event) = S.rsquared;
%CFD_times.PMT1_R_2(Event) = S.rsquared;

for index = 1 : length(TWd.TOA)
    TWd_Delta_C_D_to_MCP = Delta_C_D_to_MCP - polyval(c, TWd.TOT);
end


TWd_ed = table();
TWd_ed.TOT = TWd.TOT;
TWd_ed.TOA = TWd_Delta_C_D_to_MCP;

%rf = rowfilter(TWa_ed);
%TWed_Filtered_Events = TWa_ed(rf.TOT > 0.03, :);

nexttile;
scatter(TWd_ed.TOT, TWd_ed.TOA);
title('Post-TWd mCv2 Digital to MCP scatter');

nexttile
%xlim([-1.5e-8, 0]) %150 needs to be obtained from data, limits the Y-axis size
h=histogram(TWd_Delta_C_D_to_MCP,250);
ylabel('Counts', 'FontSize', 14);
xlabel('Cactus Digital - MCP [ps]', 'FontSize', 14);
%h.BinLimits=[-1e-12 1e-12];
%h.BinLimits=[80 120];
title('Delta TWd mCv2 Digital to MCP');

nexttile
% Define the bin edges you want
EDGES = -1500:50:1500;
%EDGES = -5e2:10:5e2;

% Bin the data according to the predefined edges:
Y = histcounts(TWd_Delta_C_D_to_MCP, EDGES);

% Fit a normal distribution using the curve fitting tool:
binCenters = conv(EDGES, [0.5, 0.5], 'valid'); % moving average
[xData, yData] = prepareCurveData( binCenters, Y );

ft = fittype( 'gauss1' );
fitresult = fit( xData, yData, ft );
%disp(fitresult); % optional

% Plot fit with data (optional)
%figure(); 
histogram(TWd_Delta_C_D_to_MCP, EDGES); hold on; grid on;
clear plot
plot(fitresult)
title('Delta TWd mCv2 Digital to MCP');

TWd_Delta_C_D_to_MCP_mu = fitresult.b1;
TWd_Delta_C_D_to_MCP_sigma = fitresult.c1/sqrt(2)