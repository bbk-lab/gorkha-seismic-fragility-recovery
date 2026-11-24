function out = ida_sdof(Ag, dt, S, zeta, scales)
%IDA_SDOF  Incremental dynamic analysis of the equivalent SDOF (EPP backbone, bilinear kinematic hysteresis).
%   Ag [nt x nrec] ground accelerations in g (PGA=1) ; scales = PGA levels in g.  Vectorised over record x level.
[nt, nrec] = size(Ag); nl = numel(scales); n = nrec*nl;
ri = repmat((1:nrec)', nl, 1); sc = reshape(repmat(scales(:)', nrec, 1), [], 1);
k = S.k*ones(n,1); Fy = S.Fy*ones(n,1); kp = 0.01*k; m = S.mstar; w = sqrt(S.k/m); c = zeta*w*dt;
u = zeros(n,1); um = zeros(n,1); up = zeros(n,1); qb = zeros(n,1); umax = zeros(n,1);
for t = 1:nt
  a = Ag(t, ri)'.*sc*9.81;
  [F, up, qb, ~] = bilin(u, up, qb, k, Fy, kp);
  un = (2*u - um*(1 - c) - dt^2*(F/m + a))/(1 + c);
  um = u; u = un; umax = max(umax, abs(u));
  umax(umax > 20) = 20; u(abs(u) > 20) = 20;
end
out.Sdmax = reshape(umax, nrec, nl); out.scales = scales(:)';
end
