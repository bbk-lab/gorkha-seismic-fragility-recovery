function cfg = frame_config(design, nst)
%FRAME_CONFIG  Parameters of the generic Nepali RC moment frame (3 bays, nst storeys).
%   design = 'NE'  non-engineered: low-grade concrete, light 8 mm ties @150 mm (pre-code practice)
%   design = 'E'   engineered:     NBC 105:2020 / NBC 205 ductile-style detailing (ties 10 mm @100 mm)
%   EDIT the numbers below to match your own ETABS/design model.
cfg.design = design; cfg.nst = nst; cfg.nbay = 3; cfg.Lb = 4.0; cfg.hst = 3.0;
cfg.plan_width_frames = 4;           % identical frames in this direction (one frame modelled)
cfg.plan_area = (3*cfg.Lb)^2;        % 12 m x 12 m building
cfg.q_seis = 7.0;                    % kN/m2: DL (slab+finishes+infill mass) + 0.25 LL
cfg.n_hinge = 10;                    % Ibarra-Krawinkler factor for rotational springs
cfg.damping = 0.05;
cfg.beta_cap = 0.30;                 % capacity/modelling dispersion added to record-to-record dispersion
switch design
  case 'NE'
    colS = struct('b',350,'h',350,'cover',40,'fc',15,'fy',415,'fyh',415,'fsu_ratio',1.10,'dbl',16,'dbh',8,'s',150,'nlegs',2,'conf_eff',0.4);
    colS.layers = [];  colA = 1608; colS.nbars = 8;     % 8 x 16 mm
    beamS = struct('b',230,'h',400,'cover',30,'fc',15,'fy',415,'fyh',415,'fsu_ratio',1.10,'dbl',16,'dbh',8,'s',150,'nlegs',2,'conf_eff',0.4);
    beamS.As = 603;                                      % 3 x 16 mm top and bottom
  case 'E'
    colS = struct('b',400,'h',400,'cover',40,'fc',25,'fy',500,'fyh',500,'fsu_ratio',1.15,'dbl',16,'dbh',10,'s',100,'nlegs',3,'conf_eff',1.0);
    colS.layers = [];  colA = 1608; colS.nbars = 8;     % 8 x 16 mm
    beamS = struct('b',250,'h',400,'cover',30,'fc',25,'fy',500,'fyh',500,'fsu_ratio',1.15,'dbl',16,'dbh',10,'s',100,'nlegs',2,'conf_eff',1.0);
    beamS.As = 603;                                      % 3 x 16 mm top and bottom
  otherwise, error('design must be NE or E');
end
cfg.col = colS; cfg.col.Atot = colA; cfg.beam = beamS;
end
