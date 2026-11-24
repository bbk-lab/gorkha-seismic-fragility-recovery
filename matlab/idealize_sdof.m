function S = idealize_sdof(R)
%IDEALIZE_SDOF  Equivalent SDOF (first mode) + equal-energy elastic-perfectly-plastic idealisation (EC8 Annex B / N2).
phi = R.phi; m = R.mass;
Gam = sum(m.*phi)/sum(m.*phi.^2); mstar = sum(m.*phi);
Sd = R.D/Gam; Fs = R.V/Gam;                       % kN, m
Fy = max(Fs); Du = Sd(end); Em = trapz(Sd, Fs);
Dy = 2*(Du - Em/Fy); Dy = min(max(Dy, 1e-4), 0.95*Du);
S.Gamma = Gam; S.mstar = mstar; S.Fy = Fy; S.Dy = Dy; S.Du = Du;
S.k = Fy/Dy; S.T = 2*pi*sqrt(mstar/S.k); S.mu_cap = Du/Dy;
S.Sd = Sd; S.Fs = Fs;
% map SDOF displacement -> max inter-storey drift (from the pushover) for reporting
[Su, iu] = unique(Sd); S.midr_of_sd = @(x) interp1(Su, R.midr(iu), x, 'linear', 'extrap');
S.midr_y = S.midr_of_sd(Dy); S.midr_u = S.midr_of_sd(Du);
end
