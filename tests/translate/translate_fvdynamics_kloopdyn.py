import copy

import fv3core.stencils.fv_dynamics as fv_dynamics

from .parallel_translate import ParallelTranslate2PyState
from .translate_dyncore import TranslateDynCore
from .translate_tracer2d1l import TranslateTracer2D1L


class TranslateFVDynamics_KLoopDyn(ParallelTranslate2PyState):
    inputs = {**TranslateDynCore.inputs, **TranslateTracer2D1L.inputs}

    def __init__(self, grids):
        super().__init__(grids)
        self._base.compute_func = fv_dynamics.do_dyn
        grid = grids[0]
        self._base.in_vars["data_vars"] = {
            "u": grid.y3d_domain_dict(),
            "v": grid.x3d_domain_dict(),
            "w": {},
            "delz": {},
            "qvapor": {},
            "qliquid": {},
            "qice": {},
            "qrain": {},
            "qsnow": {},
            "qgraupel": {},
            "qcld": {},
            "pe": {
                "istart": grid.is_ - 1,
                "iend": grid.ie + 1,
                "jstart": grid.js - 1,
                "jend": grid.je + 1,
                "kend": grid.npz + 1,
                "kaxis": 1,
            },
            "pk": grid.compute_buffer_k_dict(),
            "peln": {
                "istart": grid.is_,
                "iend": grid.ie,
                "jstart": grid.js,
                "jend": grid.je,
                "kend": grid.npz,
                "kaxis": 1,
            },
            "pkz": grid.compute_dict(),
            "phis": {},
            "q_con": {},
            "delp": {},
            "pt": {},
            "omga": {},
            "ua": {},
            "va": {},
            "uc": grid.x3d_domain_dict(),
            "vc": grid.y3d_domain_dict(),
            "ak": {},
            "bk": {},
            "dp1": {},
            "mfxd": grid.x3d_compute_dict(),
            "mfyd": grid.y3d_compute_dict(),
            "cxd": grid.x3d_compute_domain_y_dict(),
            "cyd": grid.y3d_compute_domain_x_dict(),
            "diss_estd": {},
            "cappa": {},
            "wsd": grid.compute_dict(),
        }
        self._base.in_vars["parameters"] = [
            "n_map",
            "mdt",
            "nq",
            "n_split",
            "akap",
            "zvir",
            "ptop",
            "ks",
        ]
        self._base.out_vars = copy.copy(self._base.in_vars["data_vars"])
        self.max_error = 1e-7
        for var in ["ak", "bk"]:
            del self._base.out_vars[var]
        self._base.out_vars["phis"] = {"kstart": 0, "kend": 0}
        self._base.in_vars["data_vars"]["wsd"]["kstart"] = grid.npz
        self._base.in_vars["data_vars"]["wsd"]["kend"] = None
