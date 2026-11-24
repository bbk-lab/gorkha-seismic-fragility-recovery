function [Ag, dt, src] = load_records(rec_dir)
%LOAD_RECORDS  Shared stochastic set (made by scripts/make_synthetic_records.py) + optional real records.
%   Put two-column text files (time[s]  acceleration[g]) in records/real/ to ADD real records
%   (e.g. the 2015 Gorkha KATNP record) - each is resampled and normalised to PGA = 1 g.
Ag = dlmread(fullfile(rec_dir,'synthetic_gm_set.csv'), ',');
dt = str2double(fileread(fullfile(rec_dir,'synthetic_gm_dt.txt'))); src = 'synthetic';
rd = fullfile(rec_dir,'real'); nt = size(Ag,1);
if exist(rd,'dir')
  f = dir(fullfile(rd,'*.txt'));
  for i = 1:numel(f)
    D = dlmread(fullfile(rd,f(i).name)); tt = D(:,1); aa = D(:,2);
    ti = (0:dt:tt(end))'; ai = interp1(tt, aa, ti, 'linear', 0); ai = ai/max(abs(ai));
    col = zeros(nt,1); nn = min(nt, numel(ai)); col(1:nn) = ai(1:nn); Ag(:,end+1) = col; src = 'synthetic+real';
  end
end
end
