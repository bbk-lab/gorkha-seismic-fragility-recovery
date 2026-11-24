function sec = section_mphi(S)
%SECTION_MPHI  Fibre moment-curvature analysis of a rectangular RC section (Mander confinement).
%   S fields (units: mm, N, MPa; N compression positive):
%     b h cover  fc fy fyh fsu_ratio  dbl dbh s nlegs   layers [y_from_top(mm)  As(mm2)]   N (kN)
%   Returns curvature [1/m], moment [kN m] and idealised properties used by the frame model.
P.Es = 200000; P.epsu_s = 0.08; nf = 60;
b = S.b; h = S.h; c = S.cover; fco = S.fc; fy = S.fy; fyh = S.fyh;
P.Ec = 5000*sqrt(fco); P.fy = fy; P.fco = fco;
% ---- confinement (Mander et al. 1988) ------------------------------------
bc = b - 2*c; dc = h - 2*c; sp = S.s - S.dbh;
Ab = pi*S.dbh^2/4; rho_s = S.conf_eff*2*S.nlegs*Ab/(S.s*max(bc,dc));   % conf_eff<1: poor hooks / detailing
ke = 0.75*(1 - sp/(2*bc))*(1 - sp/(2*dc));
fl = 0.5*ke*rho_s*fyh;
P.fcc = fco*(-1.254 + 2.254*sqrt(1 + 7.94*fl/fco) - 2*fl/fco);
P.ecc = 0.002*(1 + 5*(P.fcc/fco - 1));
P.ecu = min(0.004 + 1.4*rho_s*fyh*P.epsu_s/P.fcc, 0.025);
% ---- fibres --------------------------------------------------------------
dy = h/nf; P.y = ((1:nf)' - 0.5)*dy; P.h = h;
incore = (P.y >= c) & (P.y <= h - c);
P.Acore = bc*dy*double(incore); P.Aunc = b*dy*ones(nf,1) - P.Acore; P.icore = find(incore,1,'first');
P.ysb = S.layers(:,1); P.Asb = S.layers(:,2);
P.epsy = fy/P.Es; P.Esh = (S.fsu_ratio*fy - fy)/(P.epsu_s - P.epsy);
N0 = S.N*1e3; nph = 300; phimax = 0.06/h;
phi = linspace(0, phimax, nph+1)'; M = zeros(nph+1,1); ect = zeros(nph+1,1); est = zeros(nph+1,1);
for i = 2:nph+1
    lo = -0.03; hi = 0.06;
    for it = 1:45
        mid = 0.5*(lo+hi); Nm = resp(P, mid, phi(i));
        if Nm < N0, lo = mid; else hi = mid; end %#ok<SEPEX>
    end
    et = 0.5*(lo+hi); [~, Mi, ec_core, es_b] = resp(P, et, phi(i));
    M(i) = Mi; ect(i) = ec_core; est(i) = min(es_b);
end
fail = find(ect >= P.ecu | -est >= 0.06, 1, 'first'); if isempty(fail), fail = nph+1; end
iu = max(fail - 1, 3);
phi = phi(1:iu); M = M(1:iu); ect = ect(1:iu); est = est(1:iu);
iy = find(-est >= P.epsy, 1, 'first'); if isempty(iy), iy = min(5, iu); end
My1 = M(iy); phiy1 = phi(iy);
in = find(ect >= 0.004 | -est >= 0.015, 1, 'first'); if isempty(in), in = iu; end
Mn = M(in); Mmax = max(M);
sec.phi = phi*1e3; sec.M = M*1e-6;
sec.My1 = My1*1e-6; sec.phiy1 = phiy1*1e3;
sec.Mn = Mn*1e-6; sec.Mmax = Mmax*1e-6;
sec.phiy_eff = phiy1*Mn/My1*1e3;
sec.phiu = phi(iu)*1e3;
sec.EIeff = sec.Mn/sec.phiy_eff;
sec.fcc = P.fcc; sec.ecu = P.ecu; sec.rho_s = rho_s; sec.EIg = P.Ec*b*h^3/12*1e-9;
sec.mu_phi = sec.phiu/sec.phiy_eff;
end

function [Nint, M, eps_core, es] = resp(P, et, phi)
ec = et - phi*P.y; es = et - phi*P.ysb;
sc_core = mander(ec, P.fcc, P.ecc, P.ecu, P.Ec);
sc_unc  = mander(ec, P.fco, 0.002, 0.005, P.Ec);
fcf = sc_core.*P.Acore + sc_unc.*P.Aunc;
fs  = steel(es, P).*P.Asb;
Nint = sum(fcf) + sum(fs);
M = sum(fcf.*(P.h/2 - P.y)) + sum(fs.*(P.h/2 - P.ysb));
eps_core = ec(P.icore);
end

function s = mander(e, f0, e0, eu, E0)
Esec = f0/e0; r = E0/(E0 - Esec); x = max(e,0)/e0;
s = f0*x*r./(r - 1 + x.^r);
s(e <= 0) = 0; s(e > eu) = 0;
end

function s = steel(e, P)
a = abs(e); s = P.Es*a; m = a > P.epsy;
s(m) = P.fy + P.Esh*(a(m) - P.epsy); s(a > P.epsu_s) = 0; s = sign(e).*s;
end
