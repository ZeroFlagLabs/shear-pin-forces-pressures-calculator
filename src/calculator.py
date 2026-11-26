import math


def calculate_shear_pin(
    uts_min,
    uts_max,
    pin_od,
    pin_od_tol,
    qty,
    annulus_od,
    annulus_od_tol,
    annulus_id,
    annulus_id_tol,
):
    # -------------------------
    # Shear pin geometry
    # -------------------------
    pin_d_min = max(0, pin_od - pin_od_tol)
    pin_d_max = max(0, pin_od + pin_od_tol)

    area_min = math.pi / 4 * pin_d_min**2
    area_max = math.pi / 4 * pin_d_max**2

    # -------------------------
    # Material (shear strength)
    # -------------------------
    tau_min = 0.6 * uts_min
    tau_max = 0.6 * uts_max

    # -------------------------
    # Shear force
    # -------------------------
    force_min = qty * tau_min * area_min
    force_max = qty * tau_max * area_max

    # -------------------------
    # Default pressure outputs
    # -------------------------
    pressure_min = 0
    pressure_max = 0

    # -------------------------
    # Annulus + pressure (only if valid)
    # -------------------------
    if annulus_od > 0:
        id_min = max(0, annulus_id - annulus_id_tol)
        id_max = max(0, annulus_id + annulus_id_tol)

        od_min = max(0, annulus_od - annulus_od_tol)
        od_max = max(0, annulus_od + annulus_od_tol)

        area_annulus_max = math.pi / 4 * (od_max**2 - id_min**2)
        area_annulus_min = math.pi / 4 * (od_min**2 - id_max**2)

        # Protect against invalid geometry
        if area_annulus_max > 0:
            pressure_min = force_min / area_annulus_max

        if area_annulus_min > 0:
            pressure_max = force_max / area_annulus_min

    # -------------------------
    # Return results
    # -------------------------
    return force_min, force_max, pressure_min, pressure_max

"""Exploratory extension of the legacy worst-case equations."""
import math
def evaluate(uts,pin,qty,planes,od=None,id_=None,*,factor=0.6):
    if not math.isfinite(factor) or not 0<factor<=1:raise ValueError("Shear strength factor must be greater than zero and no greater than one.")
    if not (0<uts[0]<=uts[1] and 0<pin[0]<=pin[1] and isinstance(qty,int) and qty>0 and isinstance(planes,int) and planes>0):
        raise ValueError("Invalid shear pin inputs.")
    fmin=qty*planes*factor*float(uts[0])*math.pi/4*float(pin[0])**2
    fmax=qty*planes*factor*float(uts[1])*math.pi/4*float(pin[1])**2
    if od is None or id_ is None:return fmin,fmax,None,None
    if not (0<=id_[0]<=id_[1]<od[0]<=od[1]):
        raise ValueError("Minimum annulus OD must exceed maximum ID.")
    amax=math.pi/4*(float(od[1])**2-float(id_[0])**2)
    amin=math.pi/4*(float(od[0])**2-float(id_[1])**2)
    return fmin,fmax,fmin/amax,fmax/amin
