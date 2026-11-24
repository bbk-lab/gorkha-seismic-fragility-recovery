function M = build_frame(cfg)
%BUILD_FRAME  2-D RC frame with lumped plastic hinges (rotational springs), rigid floor diaphragms.
%   Hinge law: bilinear (nominal moment Mn -> Mmax at plastic-rotation capacity), strengths and
%   stiffness from fibre moment-curvature analysis of every member section (section_mphi.m).
nst = cfg.nst; nb = cfg.nbay; nc = nb + 1; L = cfg.Lb; h = cfg.hst; nh = cfg.n_hinge;
nn = (nst+1)*nc;
ux = zeros(nn,1); uy = zeros(nn,1); rz = zeros(nn,1); d = 0; uxf = zeros(nst,1);
for lev = 1:nst, d = d + 1; uxf(lev) = d; end                      % one lateral DOF per floor
for lev = 1:nst
  for ln = 1:nc
    n = lev*nc + ln; ux(n) = uxf(lev); d = d + 1; uy(n) = d; d = d + 1; rz(n) = d;
  end
end
% ---- member sections ------------------------------------------------------
q = cfg.q_seis; wtrib = L;                      % interior frame: tributary width = frame spacing = Lb
colSec = cell(nst,2);                           % {storey, 1=exterior 2=interior}
for lev = 1:nst
  for t = 1:2
    trib = 0.5*L*wtrib*(t==1) + L*wtrib*(t==2);
    S = cfg.col; S.N = q*trib*(nst - lev + 1); S.layers = col_layers(S);
    colSec{lev,t} = section_mphi(S);
  end
end
SB = cfg.beam; SB.N = 0; SB.layers = beam_layers(SB); beamSec = section_mphi(SB);
% ---- elements ------------------------------------------------------------
el = []; sp = [];                                % element rows / spring rows
Ec_c = 5000*sqrt(cfg.col.fc)*1e3; Ec_b = 5000*sqrt(cfg.beam.fc)*1e3;   % kPa
ne = 0; nsp = 0; hd = d;                          % hinge DOFs follow
E = {};                                           % element struct array
for lev = 1:nst
  for ln = 1:nc                                   % column
    ni = (lev-1)*nc + ln; nj = lev*nc + ln; t = 1 + (ln > 1 && ln < nc);
    E{end+1} = make_el(ni, nj, 0, 1, h, colSec{lev,t}, Ec_c, cfg.col.b*cfg.col.h*1e-6, nh, 1, lev, cfg.col);
  end
  for ln = 1:nb                                   % beam
    ni = lev*nc + ln; nj = lev*nc + ln + 1;
    E{end+1} = make_el(ni, nj, 1, 0, L, beamSec, Ec_b, cfg.beam.b*cfg.beam.h*1e-6, nh, 2, lev, cfg.beam);
  end
end
ne = numel(E); ndof = hd + 2*ne;
Kel = zeros(ndof); spr_h = zeros(2*ne,1); spr_n = zeros(2*ne,1);
k0 = zeros(2*ne,1); Fy = k0; kp = k0; thpu = k0; typ = k0; story = k0; Mmax = k0;
for e = 1:ne
  Ee = E{e}; hi = hd + 2*e - 1; hj = hd + 2*e;
  dofs = [ux(Ee.ni) uy(Ee.ni) hi ux(Ee.nj) uy(Ee.nj) hj];
  T = [Ee.c Ee.s 0; -Ee.s Ee.c 0; 0 0 1]; T6 = blkdiag(T,T);
  A = Ee.A; EI = Ee.EIel; Lm = Ee.L; Ec = Ee.Ec;
  kl = [ Ec*A/Lm 0 0 -Ec*A/Lm 0 0;
         0 12*EI/Lm^3 6*EI/Lm^2 0 -12*EI/Lm^3 6*EI/Lm^2;
         0 6*EI/Lm^2 4*EI/Lm 0 -6*EI/Lm^2 2*EI/Lm;
         -Ec*A/Lm 0 0 Ec*A/Lm 0 0;
         0 -12*EI/Lm^3 -6*EI/Lm^2 0 12*EI/Lm^3 -6*EI/Lm^2;
         0 6*EI/Lm^2 2*EI/Lm 0 -6*EI/Lm^2 4*EI/Lm ];
  kg = T6'*kl*T6;
  for a = 1:6, for b = 1:6
    if dofs(a) > 0 && dofs(b) > 0, Kel(dofs(a),dofs(b)) = Kel(dofs(a),dofs(b)) + kg(a,b); end
  end, end
  for end_ = 1:2
    s = 2*e - 2 + end_; spr_h(s) = hd + s; nd = [Ee.ni Ee.nj]; spr_n(s) = rz(nd(end_));
    k0(s) = Ee.k0; Fy(s) = Ee.Mn; Mmax(s) = Ee.Mmax; kp(s) = Ee.kp; thpu(s) = Ee.thpu; typ(s) = Ee.type; story(s) = Ee.story;
  end
end
M.cfg = cfg; M.ndof = ndof; M.Kel = Kel; M.nspr = 2*ne; M.spr_h = spr_h; M.spr_n = spr_n;
M.k0 = k0; M.Fy = Fy; M.kp = kp; M.thpu = thpu; M.type = typ; M.story = story; M.Mmax = Mmax;
M.uxf = uxf; M.nst = nst; M.hst = h; M.H = nst*h;
M.mass = q*(nb*L)*wtrib/9.81*ones(nst,1);         % t (kN s2/m) per floor
M.W = sum(M.mass)*9.81;                           % seismic weight of the modelled frame [kN]
M.sections.col = colSec; M.sections.beam = beamSec;
end

function e = make_el(ni, nj, c, s, Lm, sec, Ec, Ag, nh, type, story, S)
e.ni = ni; e.nj = nj; e.c = c; e.s = s; e.L = Lm; e.A = Ag; e.Ec = Ec;
e.EIel = sec.EIeff*(nh+1)/nh;                     % Ibarra-Krawinkler: elastic part amplified ...
e.k0 = nh*6*sec.EIeff/Lm;                         % ... hinge springs stiff so overall EI = EIeff
e.Mn = sec.Mn; e.Mmax = sec.Mmax;
Lp = 0.08*(Lm/2) + 0.022*S.fy*S.dbl/1000;         % Paulay-Priestley plastic hinge length [m]
e.thpu = max((sec.phiu - sec.phiy_eff)*Lp, 1e-4); % plastic rotation capacity [rad]
e.kp = max((sec.Mmax - sec.Mn)/e.thpu, 0.005*e.k0);
e.type = type; e.story = story;
end

function L = col_layers(S)
y1 = S.cover + S.dbh + S.dbl/2; A = S.Atot;
if S.nbars == 6, L = [y1 A/3; S.h/2 A/3; S.h-y1 A/3];
else, L = [y1 A*3/8; S.h/2 A*2/8; S.h-y1 A*3/8]; end
end

function L = beam_layers(S)
y1 = S.cover + S.dbh + S.dbl/2; L = [y1 S.As; S.h - y1 S.As];
end
