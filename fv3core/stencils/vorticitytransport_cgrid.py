from gt4py.gtscript import __INLINED, PARALLEL, computation, interval, parallel, region

import fv3core._config as spec
import fv3core.utils.gt4py_utils as utils
from fv3core.decorators import gtstencil


sd = utils.sd
origin = utils.origin


@gtstencil()
def update_zonal_velocity(
    vorticity: sd,
    ke: sd,
    velocity: sd,
    velocity_c: sd,
    cosa: sd,
    sina: sd,
    rdxc: sd,
    dt2: float,
):
    from __externals__ import i_end, i_start, namelist

    with computation(PARALLEL), interval(...):
        assert __INLINED(namelist.grid_type < 3)
        # additional assumption: not __INLINED(spec.grid.nested)

        tmp_flux = dt2 * (velocity - velocity_c * cosa) / sina
        with parallel(region[i_start, :], region[i_end + 1, :]):
            tmp_flux = dt2 * velocity

        flux = vorticity[0, 0, 0] if tmp_flux > 0.0 else vorticity[0, 1, 0]
        velocity_c = velocity_c + tmp_flux * flux + rdxc * (ke[-1, 0, 0] - ke)


@gtstencil()
def update_meridional_velocity(
    vorticity: sd,
    ke: sd,
    velocity: sd,
    velocity_c: sd,
    cosa: sd,
    sina: sd,
    rdyc: sd,
    dt2: float,
):
    from __externals__ import j_end, j_start, namelist

    with computation(PARALLEL), interval(...):
        assert __INLINED(namelist.grid_type < 3)
        # additional assumption: not __INLINED(spec.grid.nested)

        tmp_flux = dt2 * (velocity - velocity_c * cosa) / sina
        with parallel(region[:, j_start], region[:, j_end + 1]):
            tmp_flux = dt2 * velocity

        flux = vorticity[0, 0, 0] if tmp_flux > 0.0 else vorticity[1, 0, 0]
        velocity_c = velocity_c - tmp_flux * flux + rdyc * (ke[0, -1, 0] - ke)


def compute(uc: sd, vc: sd, vort_c: sd, ke_c: sd, v: sd, u: sd, dt2: float):
    """Update the C-Grid zonal and meridional velocity fields.

    Args:
        uc: x-velocity on C-grid (input, output)
        vc: y-velocity on C-grid (input, output)
        vort_c: Vorticity on C-grid (input)
        ke_c: kinetic energy on C-grid (input)
        v: y-velocit on D-grid (input)
        u: x-velocity on D-grid (input)
        dt2: timestep (input)
    """
    grid = spec.grid
    update_meridional_velocity(
        vort_c,
        ke_c,
        u,
        vc,
        grid.cosa_v,
        grid.sina_v,
        grid.rdyc,
        dt2,
        origin=grid.compute_origin(),
        domain=grid.domain_shape_compute_buffer_2d(add=(0, 1, 0)),
    )
    update_zonal_velocity(
        vort_c,
        ke_c,
        v,
        uc,
        grid.cosa_u,
        grid.sina_u,
        grid.rdxc,
        dt2,
        origin=grid.compute_origin(),
        domain=grid.domain_shape_compute_buffer_2d(add=(1, 0, 0)),
    )
