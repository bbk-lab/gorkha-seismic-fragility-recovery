function R = pushover_frame(M, drift_target, nsteps)
%PUSHOVER_FRAME  Displacement-controlled nonlinear static analysis (first-mode load pattern).
if nargin < 2, drift_target = 0.04; end
if nargin < 3, nsteps = 400; end
nd = M.ndof; ns = M.nspr; nst = M.nst; uxf = M.uxf; mass = M.mass;
% ---- elastic modal properties --------------------------------------------
[Ks, ~] = spring_assemble(M, zeros(nd,1), zeros(ns,1), zeros(ns,1));
K0 = M.Kel + Ks;
E = zeros(nd, nst); for f = 1:nst, E(uxf(f), f) = 1; end
Fl = (K0\E); Fl = Fl(uxf,:); Klat = inv(Fl); Klat = 0.5*(Klat+Klat');
Mm = diag(mass); [V, D] = eig(Klat, Mm); [w2, ix] = sort(real(diag(D))); phi = real(V(:,ix(1)));
phi = phi/phi(end); T1 = 2*pi/sqrt(w2(1));
Pref = zeros(nd,1); Pref(uxf) = mass.*phi;
c = uxf(nst); up = zeros(ns,1); qb = zeros(ns,1); U = zeros(nd,1); lam = 0;
dtarget = drift_target*M.H; dc = dtarget/nsteps;
hist = zeros(nsteps+1, 3+nst); ratio_hist = zeros(nsteps+1, 2); nyield = zeros(nsteps+1,1);
iu = 0; iy1 = 0; colmask = (M.type == 1);
for stp = 1:nsteps
  [Ks, Fs, ~, ~, ~] = spring_assemble(M, U, up, qb);
  K = M.Kel + Ks; dUp = K\Pref; dl = dc/dUp(c); Ut = U + dl*dUp; lt = lam + dl;
  for it = 1:40
    [Ks, Fs, upt, qbt, ~] = spring_assemble(M, Ut, up, qb);
    Fint = M.Kel*Ut + Fs; Rr = lt*Pref - Fint; K = M.Kel + Ks;
    if norm(Rr) < 1e-7*max(1, norm(lt*Pref)), break; end
    dUr = K\Rr; dUp = K\Pref; dl = -dUr(c)/dUp(c);
    Ut = Ut + dUr + dl*dUp; lt = lt + dl;
  end
  U = Ut; lam = lt; up = upt; qb = qbt;
  ux = [0; U(uxf)]; drifts = diff(ux)/M.hst;
  hist(stp+1,:) = [U(c), lam*sum(Pref), max(abs(drifts)), drifts'];
  rr = abs(up)./M.thpu; ratio_hist(stp+1,:) = [max(rr(colmask)), max(rr)];
  nyield(stp+1) = sum(abs(up) > 0);
  if iy1 == 0 && nyield(stp+1) > 0, iy1 = stp+1; end
  if iu == 0 && (ratio_hist(stp+1,1) >= 1 || hist(stp+1,3) >= 0.04), iu = stp+1; end
  if iu > 0 && stp+1 >= iu + 5, break; end
end
last = find(hist(:,1) > 0, 1, 'last'); if isempty(iu) || iu == 0, iu = last; end
R.D = hist(1:iu,1); R.V = hist(1:iu,2); R.midr = hist(1:iu,3); R.drifts = hist(1:iu,4:end);
R.col_ratio = ratio_hist(1:iu,1); R.nyield = nyield(1:iu);
R.phi = phi; R.T1 = T1; R.mass = mass; R.iy1 = iy1; R.Vmax = max(R.V); R.W = M.W;
R.Vy_over_W = R.Vmax/M.W;
end

function [Ks, Fs, up, qb, kt] = spring_assemble(M, U, up0, qb0)
nd = M.ndof; ns = M.nspr; Ks = zeros(nd); Fs = zeros(nd,1);
h = M.spr_h; n = M.spr_n;
uh = U(h); un = zeros(ns,1); m = n > 0; un(m) = U(n(m));
th = uh - un;
[F, up, qb, kt] = bilin(th, up0, qb0, M.k0, M.Fy, M.kp);
for s = 1:ns
  Fs(h(s)) = Fs(h(s)) + F(s); Ks(h(s),h(s)) = Ks(h(s),h(s)) + kt(s);
  if n(s) > 0
    Fs(n(s)) = Fs(n(s)) - F(s); Ks(n(s),n(s)) = Ks(n(s),n(s)) + kt(s);
    Ks(h(s),n(s)) = Ks(h(s),n(s)) - kt(s); Ks(n(s),h(s)) = Ks(n(s),h(s)) - kt(s);
  end
end
end
