"""Generate a reproducible set of stochastic ground motions (Clough-Penzien filtered white noise with
Jennings-type envelope), normalised to PGA = 1 g, shared by Python and MATLAB/Octave.

These are NOT recorded accelerograms. For real records (e.g. the 2015 KATNP/Kantipath record from
CESMD / PEER NGA) drop two-column text files (t[s]  a[g]) into matlab/records/real/ -
the MATLAB driver will use them automatically (see matlab/README_matlab.md)."""
import numpy as np, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
rng = np.random.default_rng(2015)
dt, T, nrec = 0.005, 30.0, 30
t = np.arange(0, T, dt); nt = len(t)
w = np.linspace(0.5, 2*np.pi*25, 500); dw = w[1]-w[0]
A = np.zeros((nt, nrec))
for i in range(nrec):
    wg = rng.uniform(10, 24); zg = rng.uniform(0.3, 0.8); wf = 2*np.pi*rng.uniform(0.25, 0.5); zf = 0.6
    r = w/wg; S = (1+4*zg**2*r**2)/((1-r**2)**2+4*zg**2*r**2)
    rf = w/wf; S *= rf**4/((1-rf**2)**2+4*zf**2*rf**2)
    ph = rng.uniform(0, 2*np.pi, len(w)); amp = np.sqrt(2*S*dw)
    a = np.zeros(nt)
    for k in range(0, len(w), 100):
        a += (amp[k:k+100, None]*np.cos(np.outer(w[k:k+100], t)+ph[k:k+100, None])).sum(axis=0)
    t1, t2, c = rng.uniform(1.5, 3.5), rng.uniform(10, 16), rng.uniform(0.1, 0.25)
    env = np.where(t < t1, (t/t1)**2, np.where(t < t2, 1.0, np.exp(-c*(t-t2))))
    a *= env; A[:, i] = a/np.abs(a).max()
np.savetxt(root/"matlab"/"records"/"synthetic_gm_set.csv", A, fmt="%.6f", delimiter=",")
(root/"matlab"/"records"/"synthetic_gm_dt.txt").write_text(f"{dt}\n")
print("records:", A.shape, "dt", dt)
