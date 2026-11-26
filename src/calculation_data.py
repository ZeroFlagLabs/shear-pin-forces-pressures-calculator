"""Build trace/report data from the validated live calculation."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import math

@dataclass(frozen=True)
class InputRange:
    name:str
    unit:str
    mode:str
    a:str
    b:str
    bounds:tuple|None

    def display(self):
        # Report dimensions using exact midpoint/half-range independently
        # of UI mode; retain the selected material-property representation.
        def fmt(v):
            places=max(3 if self.unit=="in" else 0,-v.normalize().as_tuple().exponent)
            return f"{v:.{places}f}"
        if self.unit=="in" and self.bounds is not None:
            lo,hi=self.bounds
            nominal,tolerance=(lo+hi)/2,(hi-lo)/2
            return f"{fmt(nominal)} {self.unit}" if tolerance==0 else f"{fmt(nominal)} \u00b1 {fmt(tolerance)} {self.unit}"
        # For unset/invalid/incomplete inputs preserve what was entered,
        # rather than inferring valid bounds. Explicit all-zero optional
        # OD is shown as zero; the report identifies unavailable pressure.
        a,b=self.a or "-",self.b or "-"
        def zero(value):
            try:return bool(value) and Decimal(value)==0
            except InvalidOperation:return False
        if zero(self.a) and zero(self.b) and self.unit=="in":
            return f"{fmt(Decimal(0))} {self.unit}"
        if self.mode=="pm":
            if self.bounds is not None and zero(self.b):return f"{a} {self.unit}"
            return f"{a} \u00b1 {b} {self.unit}"
        return f"{a} to {b} {self.unit}"

@dataclass(frozen=True)
class Case:
    uts:float
    diameter:float
    strength:float
    pin_area:float
    shear_area:float
    force:float
    od:float|None
    id:float|None
    annulus:float|None
    pressure:float|None

@dataclass(frozen=True)
class Calculation:
    pins:int
    planes:int
    factor:float
    inputs:tuple
    minimum:Case
    maximum:Case
    pressure_note:str

def capture(pins,planes,ranges,forces,pressures,pressure_note,*,factor=0.6):
    """Use engine outputs; check intermediates independently, without rounding."""
    uts,pin,od,idd=ranges
    cases=[]
    for i in (0,1):
        u=float(uts.bounds[i]);d=float(pin.bounds[i])
        strength=factor*u
        area=math.pi*d*d/4
        total=area*pins*planes
        force=forces[i]
        if not math.isclose(total*strength,force,rel_tol=1e-12,abs_tol=1e-8):
            raise ValueError("Force trace does not match engine.")
        pressure=pressures[i]
        if pressure is not None:
            outer=float(od.bounds[1-i]);inner=float(idd.bounds[i])
            annulus=math.pi/4*(outer**2-inner**2)
            if not math.isclose(force/annulus,pressure,rel_tol=1e-12,abs_tol=1e-8):
                raise ValueError("Pressure trace does not match engine.")
        else:outer=inner=annulus=None
        cases.append(Case(u,d,strength,area,total,force,outer,inner,annulus,pressure))
    return Calculation(pins,planes,factor,tuple(ranges),*cases,pressure_note)

def result_text(value,unit):
    if value is None:return "-"
    return (f"{value:.1f}" if value<10 else f"{round(value):,}")+" "+unit
