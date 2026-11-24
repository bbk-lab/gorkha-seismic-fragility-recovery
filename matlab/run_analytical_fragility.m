% RUN_ANALYTICAL_FRAGILITY  Analytical PGA-based fragility of 3- and 4-storey RC frames (NE / E designs).
%   Pipeline: section M-phi -> 2D hinge-model pushover -> equivalent SDOF -> IDA -> lognormal fit.
%   Outputs (results/matlab/): analytical_fragility.csv, capacity_<case>.csv, ida_<case>.csv, figures.
clear; clc;
here = fileparts(mfilename('fullpath')); addpath(here);
outdir = fullfile(here,'..','results','matlab'); if ~exist(outdir,'dir'), mkdir(outdir); end
[Ag, dt, src] = load_records(fullfile(here,'records')); nrec = size(Ag,2);
scales = logspace(log10(0.05), log10(6), 26);          % PGA levels [g]
designs = {'NE','E'}; storeys = [3 4];
fid = fopen(fullfile(outdir,'analytical_fragility.csv'),'w');
fprintf(fid,'case,design,storeys,T1_frame_s,T_sdof_s,Vmax_over_W,Dy_m,Du_m,mu_cap,midr_DS2,midr_DS3,ds,median_pga_g,beta_rtr,beta_total,n_records,records\n');
for d = 1:numel(designs)
  for ns = storeys
    name = sprintf('RC_%s_%dst', designs{d}, ns); fprintf('--- %s ---\n', name);
    cfg = frame_config(designs{d}, ns); M = build_frame(cfg);
    R = pushover_frame(M, 0.04, 400); S = idealize_sdof(R);
    fprintf('T1=%.2fs  Vmax/W=%.3f  Dy=%.3f m  Du=%.3f m  mu=%.1f\n', R.T1, R.Vy_over_W, S.Dy, S.Du, S.mu_cap);
    I = ida_sdof(Ag, dt, S, cfg.damping, scales);
    thr = [S.Dy, S.Du]; dsn = {'DS2_DG2plus','DS3_DG3'};
    for j = 1:2
      imds = nan(nrec,1);
      for r = 1:nrec
        sd = I.Sdmax(r,:); i1 = find(sd >= thr(j), 1, 'first');
        if ~isempty(i1)
          if i1 == 1, imds(r) = scales(1);
          else, f = (thr(j)-sd(i1-1))/(sd(i1)-sd(i1-1)); imds(r) = exp(log(scales(i1-1)) + f*(log(scales(i1))-log(scales(i1-1)))); end
        end
      end
      ok = ~isnan(imds); med = exp(mean(log(imds(ok)))); brtr = std(log(imds(ok)));
      btot = sqrt(brtr^2 + cfg.beta_cap^2);
      fprintf('  %s: median PGA = %.3f g, beta_rtr = %.2f, beta_tot = %.2f (n=%d)\n', dsn{j}, med, brtr, btot, sum(ok));
      fprintf(fid,'%s,%s,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.3f,%.5f,%.5f,%s,%.4f,%.4f,%.4f,%d,%s\n', name, designs{d}, ns, R.T1, S.T, R.Vy_over_W, S.Dy, S.Du, S.mu_cap, S.midr_y, S.midr_u, dsn{j}, med, brtr, btot, sum(ok), src);
    end
    % ---- export curves --------------------------------------------------
    fc = fopen(fullfile(outdir,['capacity_' name '.csv']),'w'); fprintf(fc,'roof_disp_m,base_shear_kN,midr,Sd_m,Fstar_kN\n');
    for i = 1:numel(R.D), fprintf(fc,'%.6f,%.4f,%.6f,%.6f,%.4f\n', R.D(i), R.V(i), R.midr(i), S.Sd(i), S.Fs(i)); end; fclose(fc);
    fi = fopen(fullfile(outdir,['ida_' name '.csv']),'w'); fprintf(fi,'record,pga_g,Sdmax_m\n');
    for r = 1:nrec, for l = 1:numel(scales), fprintf(fi,'%d,%.5f,%.6f\n', r, scales(l), I.Sdmax(r,l)); end, end; fclose(fi);
  end
end
fclose(fid);
fprintf('Done. Results in %s\n', outdir);
