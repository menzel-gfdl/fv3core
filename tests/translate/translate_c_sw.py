import fv3core.stencils.c_sw as c_sw
import fv3core.utils.gt4py_utils as utils

from .translate import TranslateFortranData2Py


class TranslateC_SW(TranslateFortranData2Py):
    def __init__(self, grid):
        super().__init__(grid)
        self.compute_func = c_sw.compute
        self.in_vars["data_vars"] = {
            "delp": {},
            "pt": {},
            "u": {"jend": grid.jed + 1},
            "v": {"iend": grid.ied + 1},
            "w": {},
            "uc": {"iend": grid.ied + 1},
            "vc": {"jend": grid.jed + 1},
            "ua": {},
            "va": {},
            "ut": {},
            "vt": {},
            "omga": {"serialname": "omgad"},
            "divgd": {"iend": grid.ied + 1, "jend": grid.jed + 1},
        }
        self.in_vars["parameters"] = ["dt2"]
        for name, info in self.in_vars["data_vars"].items():
            info["serialname"] = name + "d"
        self.out_vars = {}
        for v, d in self.in_vars["data_vars"].items():
            self.out_vars[v] = d
        for servar in ["delpcd", "ptcd"]:
            self.out_vars[servar] = {}
        # TODO: Fix edge_interpolate4 in d2a2c_vect to match closer and the
        # variables here should as well.
        self.max_error = 2e-10

    def compute(self, inputs):
        self.make_storage_data_input_vars(inputs)
        delpc, ptc = self.compute_func(**inputs)
        return self.slice_output(inputs, {"delpcd": delpc, "ptcd": ptc})


class TranslateTransportDelp(TranslateFortranData2Py):
    def __init__(self, grid):
        super().__init__(grid)
        self.in_vars["data_vars"] = {
            "delp": {},
            "pt": {},
            "utc": {},
            "vtc": {},
            "w": {},
            "wc": {},
        }
        self.out_vars = {"delpc": {}, "ptc": {}, "wc": {}}

    def compute(self, inputs):
        self.make_storage_data_input_vars(inputs)
        orig = (self.grid.is_ - 1, self.grid.js - 1, 0)
        inputs["delpc"] = utils.make_storage_from_shape(
            inputs["delp"].shape, origin=orig
        )
        inputs["ptc"] = utils.make_storage_from_shape(inputs["pt"].shape, origin=orig)
        c_sw.transportdelp(
            **inputs,
            rarea=self.grid.rarea,
            origin=orig,
            domain=self.grid.domain_shape_compute_buffer_2d(add=(2, 2, 0)),
        )
        return self.slice_output(
            inputs,
        )


class TranslateDivergenceCorner(TranslateFortranData2Py):
    def __init__(self, grid):
        super().__init__(grid)
        self.in_vars["data_vars"] = {
            "u": {
                "istart": grid.isd,
                "iend": grid.ied,
                "jstart": grid.jsd,
                "jend": grid.jed + 1,
            },
            "v": {
                "istart": grid.isd,
                "iend": grid.ied + 1,
                "jstart": grid.jsd,
                "jend": grid.jed,
            },
            "ua": {},
            "va": {},
            "divg_d": {},
        }
        self.out_vars = {
            "divg_d": {
                "istart": grid.isd,
                "iend": grid.ied + 1,
                "jstart": grid.jsd,
                "jend": grid.jed + 1,
            }
        }

    def compute(self, inputs):
        self.make_storage_data_input_vars(inputs)
        c_sw.divergence_corner(
            **inputs,
            dxc=self.grid.dxc,
            dyc=self.grid.dyc,
            sin_sg1=self.grid.sin_sg1,
            sin_sg2=self.grid.sin_sg2,
            sin_sg3=self.grid.sin_sg3,
            sin_sg4=self.grid.sin_sg4,
            cos_sg1=self.grid.cos_sg1,
            cos_sg2=self.grid.cos_sg2,
            cos_sg3=self.grid.cos_sg3,
            cos_sg4=self.grid.cos_sg4,
            rarea_c=self.grid.rarea_c,
            origin=self.grid.compute_origin(),
            domain=self.grid.domain_shape_compute_buffer_2d(add=(1, 1, 0)),
        )
        return self.slice_output({"divg_d": inputs["divg_d"]})


class TranslateCirculation_Cgrid(TranslateFortranData2Py):
    def __init__(self, grid):
        super().__init__(grid)
        self.in_vars["data_vars"] = {
            "uc": {},
            "vc": {},
            "vort_c": {
                "istart": grid.is_ - 1,
                "iend": grid.ie + 1,
                "jstart": grid.js - 1,
                "jend": grid.je + 1,
            },
        }
        self.out_vars = {
            "vort_c": {
                "istart": grid.is_ - 1,
                "iend": grid.ie + 1,
                "jstart": grid.js - 1,
                "jend": grid.je + 1,
            }
        }

    def compute(self, inputs):
        self.make_storage_data_input_vars(inputs)
        c_sw.circulation_cgrid(
            **inputs,
            dxc=self.grid.dxc,
            dyc=self.grid.dyc,
            origin=self.grid.compute_origin(),
            domain=self.grid.domain_shape_compute_buffer_2d(add=(1, 1, 0)),
        )
        return self.slice_output({"vort_c": inputs["vort_c"]})
