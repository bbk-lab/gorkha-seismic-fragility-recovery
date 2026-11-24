%% PLOT_ANALYTICAL_RESULTS  Make the MATLAB figures from the CSV files written by run_analytical_fragility.m
%  Run run_analytical_fragility.m first. Figures are saved as PNG in results/matlab/figures/.
%  Tip (VS Code / MATLAB): each "%%" line starts a section - run one section at a time with Ctrl+Enter
%  to see how every figure is built.
clear; clc; close all;
here   = fileparts(mfilename('fullpath'));
resdir = fullfile(here,'..','results','matlab');
figdir = fullfile(resdir,'figures'); if ~exist(figdir,'dir'), mkdir(figdir); end
cases  = {'RC_NE_3st','RC_NE_4st','RC_E_3st','RC_E_4st'};
col    = [0.84 0.19 0.15; 0.99 0.55 0.24; 0.13 0.44 0.71; 0.03 0.19 0.42];
Phi    = @(z) 0.5*erfc(-z/sqrt(2));          % standard normal CDF without any toolbox
dsKey  = {'DS2','DS3'};                       % first three letters of the damage-state column
dsName = {'DS2 (moderate / yield)','DS3 (near-collapse)'};

%% 1) Pushover capacity curves (base shear / seismic weight vs roof drift)
H = 3.0*[3 4 3 4];                           % building heights [m] for the four cases
f1 = figure('Visible','off','Position',[100 100 760 480]); hold on; grid on;
for i = 1:numel(cases)
    T = readmatrix(fullfile(resdir,['capacity_' cases{i} '.csv']), 'NumHeaderLines', 1);
    W = 336*(3 + (mod(i,2)==0));                                              % seismic weight of the frame [kN]
    plot(100*T(:,1)/H(i), T(:,2)/W, 'LineWidth', 2, 'Color', col(i,:));
end
xlabel('Roof drift ratio [%]'); ylabel('Base shear / seismic weight [-]');
title('Pushover capacity curves of the RC frames'); legend(strrep(cases,'_','-'),'Location','southeast');
print(f1, fullfile(figdir,'M1_pushover_capacity.png'), '-dpng', '-r150');

%% 2) Incremental dynamic analysis curves for RC_NE_4st (grey = individual records)
D = readmatrix(fullfile(resdir,'ida_RC_NE_4st.csv'), 'NumHeaderLines', 1);
C = readmatrix(fullfile(resdir,'capacity_RC_NE_4st.csv'), 'NumHeaderLines', 1);
Sd = C(:,4); Fs = C(:,5); Fy = max(Fs); Du = Sd(end); Dy = 2*(Du - trapz(Sd,Fs)/Fy);   % same EPP rule as idealize_sdof.m
f2 = figure('Visible','off','Position',[100 100 760 480]); hold on; grid on;
nrec = max(D(:,1));
for r = 1:nrec
    m = D(:,1) == r; plot(D(m,3), D(m,2), '-', 'Color', [0.75 0.75 0.75]);
end
lv = unique(D(:,2)); med = zeros(size(lv));
for k = 1:numel(lv), med(k) = exp(mean(log(max(D(D(:,2)==lv(k),3),1e-6)))); end
plot(med, lv, 'k-', 'LineWidth', 2.2);
plot([Dy Dy], [0.05 6], '--', 'Color', col(2,:), 'LineWidth', 1.6);
plot([Du Du], [0.05 6], '--', 'Color', col(1,:), 'LineWidth', 1.6);
set(gca,'YScale','log'); xlim([0 1.3*Du]); ylim([0.05 6]);
xlabel('Max SDOF displacement S_d [m]'); ylabel('PGA [g]');
title('IDA curves, RC-NE-4st (dashed: DS2 and DS3 thresholds)');
print(f2, fullfile(figdir,'M2_IDA_RC_NE_4st.png'), '-dpng', '-r150');

%% 3) Analytical fragility curves (lognormal fit to the IDA results)
fid = fopen(fullfile(resdir,'analytical_fragility.csv')); hdr = fgetl(fid); L = {};
while true, s = fgetl(fid); if ~ischar(s), break; end, L{end+1} = strsplit(s, ','); end; fclose(fid); %#ok<SAGROW>
a = linspace(0.01, 1.2, 300);
f3 = figure('Visible','off','Position',[100 100 900 440]);
for j = 1:2                                    % 1 = DS2 (DG>=2), 2 = DS3 (DG3)
    subplot(1,2,j); hold on; grid on;
    for i = 1:numel(cases)
        for k = 1:numel(L)
            if strcmp(L{k}{1}, cases{i}) && strcmp(L{k}{12}(1:3), dsKey{j})
                med = str2double(L{k}{13}); bt = str2double(L{k}{15});
                plot(a, Phi(log(a/med)/bt), 'LineWidth', 2, 'Color', col(i,:));
            end
        end
    end
    xlabel('PGA [g]'); ylabel('P(damage state \geq DS | PGA)');
    title(dsName{j});
    if j == 1, legend(strrep(cases,'_','-'),'Location','southeast'); end
end
print(f3, fullfile(figdir,'M3_analytical_fragility.png'), '-dpng', '-r150');

%% 4) Optional: overlay with the empirical curves produced by the Python step
ep = fullfile(here,'..','results','tables','empirical_fragility_params.csv');
if exist(ep,'file')
    fid = fopen(ep); h = strsplit(fgetl(fid), ','); E = {};
    while true, s = fgetl(fid); if ~ischar(s), break; end, E{end+1} = strsplit(s, ','); end; fclose(fid); %#ok<SAGROW>
    iS = find(strcmp(h,'stratum')); i2 = find(strcmp(h,'median_DG2plus_g')); i3 = find(strcmp(h,'median_DG3_g')); ib = find(strcmp(h,'beta'));
    f4 = figure('Visible','off','Position',[100 100 900 440]);
    pairs = {'RC_NE|3+fl', {'RC_NE_3st','RC_NE_4st'}, 'RC non-engineered, 3+ floors'; ...
             'RC_E|3+fl',  {'RC_E_3st','RC_E_4st'},   'RC engineered, 3+ floors'};
    for p = 1:2
        subplot(1,2,p); hold on; grid on;
        for k = 1:numel(E)
            if strcmp(E{k}{iS}, pairs{p,1})
                m2 = str2double(E{k}{i2}); m3 = str2double(E{k}{i3}); b = str2double(E{k}{ib});
                h1 = plot(a, Phi(log(a/m2)/b), 'r-',  'LineWidth', 2);
                h2 = plot(a, Phi(log(a/m3)/b), 'r:',  'LineWidth', 2);
            end
        end
        for c = 1:2
            for k = 1:numel(L)
                if strcmp(L{k}{1}, pairs{p,2}{c})
                    med = str2double(L{k}{13}); bt = str2double(L{k}{15});
                    if strcmp(L{k}{12}(1:3),'DS2'), ls = '-'; else, ls = ':'; end
                    plot(a, Phi(log(a/med)/bt), ls, 'Color', col((p-1)*2 + c,:), 'LineWidth', 1.5);
                end
            end
        end
        xlabel('PGA [g]'); ylabel('P(damage \geq state)'); title(pairs{p,3}, 'FontSize', 10);
        legend([h1 h2], {'empirical DG\geq2','empirical DG3'}, 'Location','southeast');
    end
    print(f4, fullfile(figdir,'M4_analytical_vs_empirical.png'), '-dpng', '-r150');
end
fprintf('Figures written to %s\n', figdir);
