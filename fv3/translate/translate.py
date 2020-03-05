import fv3.utils.gt4py_utils as utils
from fv3.utils.grid import Grid
import numpy as np

debug = False


class TranslateFortranData2Py:
    def __init__(self, grid, origin=utils.origin):
        self.origin = origin
        self.in_vars = {"data_vars": {}, "parameters": []}
        self.out_vars = []
        self.max_error = 1e-14
        self.grid = grid
        self.maxshape = grid.domain_shape_buffer_1cell()
        self.data_backend = utils.data_backend
        self.ordered_input_vars = None
        self.compute_func = None

    def compute(self, inputs):
        self.make_storage_data_input_vars(inputs)
        outputs = self.compute_func(**inputs)
        if outputs is not None:
            raise Exception("Implement a child class compute method")
        return self.slice_output(inputs)

    def make_storage_data(self, array, istart=0, jstart=0, kstart=0):
        return utils.make_storage_data(
            array,
            self.maxshape,
            istart,
            jstart,
            kstart,
            origin=(istart, jstart, kstart),
            backend=self.data_backend,
        )

    def storage_vars(self):
        return self.in_vars["data_vars"]

    # TODO: delete this when ready to let it go
    """
    def ordered_stencil_arg_values(self, data):
        if self.ordered_input_vars is not None:
            return [data[key] for key in self.ordered_input_vars]
        data_vars = [data[key] for key in self.in_vars['data_vars'].keys()]
        parameters = [data[key] for key in self.in_vars['parameters']]
        return data_vars + parameters

    #[data[key] for parent_key in ['data_vars', 'parameters'] for key in self.in_vars[parent_key]]
  
    def make_storage_data_input_vars(self, inputs, storage_vars=None):
        from fv3._config import grid
        if storage_vars is None:
            storage_vars = self.storage_vars()
        storage = {}
        for d in storage_vars:
            istart, jstart = grid.horizontal_starts_from_shape(inputs[d].shape)
            storage[d] = self.make_storage_data(np.squeeze(inputs[d]), istart=istart, jstart=jstart)
        for p in self.in_vars['parameters'] + self.in_vars['grid_parameters']:
            storage[p] = inputs[p]
            if type(inputs[p]) == np.int64:
                storage[p] = int(storage[p])
        return storage
    
    """

    def get_index_from_info(self, varinfo, index_name, initial_index):
        index = initial_index
        if index_name in varinfo:
            index = varinfo[index_name]
        return index

    def update_info(self, info, inputs):
        for k, v in info.items():
            if k == "serialname":
                continue
            if v in inputs.keys():
                info[k] = inputs[v]

    def collect_start_indices(self, datashape, varinfo):
        istart, jstart = self.grid.horizontal_starts_from_shape(datashape)
        istart = self.get_index_from_info(varinfo, "istart", istart)
        jstart = self.get_index_from_info(varinfo, "jstart", jstart)
        kstart = self.get_index_from_info(varinfo, "kstart", 0)
        return istart, jstart, kstart

    def make_storage_data_input_vars(self, inputs, storage_vars=None):
        if storage_vars is None:
            storage_vars = self.storage_vars()
        for p in self.in_vars["parameters"]:
            if type(inputs[p]) in [np.int64, np.int32]:
                inputs[p] = int(inputs[p])
        for d, info in storage_vars.items():
            serialname = info["serialname"] if "serialname" in info else d
            self.update_info(info, inputs)
            istart, jstart, kstart = self.collect_start_indices(
                inputs[serialname].shape, info
            )
            if debug:
                print(
                    "Making storage for ",
                    d,
                    "with istart = ",
                    istart,
                    " jstart = ",
                    jstart,
                )
            inputs[d] = self.make_storage_data(
                np.squeeze(inputs[serialname]),
                istart=istart,
                jstart=jstart,
                kstart=kstart,
            )
            if d != serialname:
                del inputs[serialname]

    def slice_output(self, inputs, out_data=None):
        if out_data is None:
            out_data = inputs
        else:
            out_data.update(inputs)
        out = {}
        for var in self.out_vars.keys():
            info = self.out_vars[var]
            self.update_info(info, inputs)
            serialname = info["serialname"] if "serialname" in info else var
            ds = self.grid.default_domain_dict()
            ds.update(info)
            out[serialname] = np.squeeze(out_data[var].data[self.grid.slice_dict(ds)])
        return out

    def serialnames(self, dict):
        return [
            info["serialname"] if "serialname" in info else d
            for d, info in dict.items()
        ]

    def column_namelist_vals(self, varname, inputs):
        info = self.in_vars["data_vars"][varname]
        name = info["serialname"] if "serialname" in info else varname
        return [i for i in inputs[name][0, 0, :]]


class TranslateGrid:
    fpy_model_index_offset = 2
    fpy_index_offset = -1
    composite_grid_vars = ["sin_sg", "cos_sg"]
    edge_var_axis = {"edge_w": 1, "edge_e": 1, "edge_s": 0, "edge_n": 0}
    # Super (composite) grid
    #     9---4---8
    #     |       |
    #     1   5   3
    #     |       |
    #     6---2---7

    def __init__(self, inputs):
        self.indices = {}
        self.shape_params = {}
        self.data = {}
        for i in Grid.indices:
            self.indices[i] = inputs[i] + self.fpy_model_index_offset
            del inputs[i]
        for s in Grid.shape_params:
            self.shape_params[s] = inputs[s]
            del inputs[s]
        self.data = inputs

    def make_composite_var_storage(self, varname, data3d, shape):
        for s in range(9):
            self.data[varname + str(s + 1)] = utils.make_storage_data(
                np.squeeze(data3d[:, :, s]),
                shape,
                origin=(0, 0, 0),
                backend=utils.data_backend,
            )

    def make_grid_storage(self, pygrid):
        shape = pygrid.domain_shape_buffer_1cell()
        for k in TranslateGrid.composite_grid_vars:
            if k in self.data:
                self.make_composite_var_storage(k, self.data[k], shape)
                del self.data[k]
        for k, axis in TranslateGrid.edge_var_axis.items():
            if k in self.data:
                self.data[k] = utils.make_storage_data_from_1d(
                    self.data[k], shape, kstart=pygrid.halo, axis=axis
                )
        for k, v in self.data.items():
            if type(v) is np.ndarray:
                # TODO: when grid initialization model exists, may want to use it to inform this
                istart, jstart = pygrid.horizontal_starts_from_shape(v.shape)
                if debug:
                    print("Storage for Grid variable", k, istart, jstart, v.shape)
                self.data[k] = utils.make_storage_data(
                    v,
                    shape,
                    origin=(istart, jstart, 0),
                    istart=istart,
                    jstart=jstart,
                    backend=utils.data_backend,
                )

    def python_grid(self):
        pygrid = Grid(self.indices, self.shape_params)
        self.make_grid_storage(pygrid)
        pygrid.add_data(self.data)
        return pygrid
