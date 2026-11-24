function [F, up, qb, kt] = bilin(u, up0, qb0, k, Fy, kp)
%BILIN  Vectorised 1-D elasto-plastic law with linear kinematic hardening (return mapping).
%   u: total deformation, up0/qb0: committed plastic deformation / back-stress,
%   k: initial stiffness, Fy: yield force, kp: post-yield stiffness.
H  = kp.*k./(k - kp);
xi = k.*(u - up0) - qb0;
f  = abs(xi) - Fy;
yl = f > 0;
dg = zeros(size(u));
dg(yl) = f(yl)./(k(yl) + H(yl));
sg = sign(xi);
up = up0 + dg.*sg;
qb = qb0 + H.*dg.*sg;
F  = k.*(u - up);
kt = k; kt(yl) = k(yl).*H(yl)./(k(yl) + H(yl));
end
