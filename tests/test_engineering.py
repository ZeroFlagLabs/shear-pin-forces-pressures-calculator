from pathlib import Path
import sys,random,math,unittest
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from calculator import evaluate,calculate_shear_pin
class EngineeringTests(unittest.TestCase):
    def test_legacy_and_factor_scaling(self):
        rng=random.Random(20261126)
        for _ in range(1000):
            u=rng.randint(30000,180000);v=u+rng.randint(0,40000)
            d=rng.randint(100,1000)/1000;t=rng.randint(0,15)/1000
            od=rng.randint(2000,12000)/1000;ot=rng.randint(0,15)/1000
            inner=od*.4;it=rng.randint(0,15)/1000
            qty=rng.randint(1,20);planes=rng.randint(1,4);factor=rng.choice((.5,.55,.577,.6,.8,1.))
            bounds=((D(str(u)),D(str(v))),(D(str(d))-D(str(t)),D(str(d))+D(str(t))))
            ann=(D(str(od))-D(str(ot)),D(str(od))+D(str(ot)))
            ids=(D(str(inner))-D(str(it)),D(str(inner))+D(str(it)))
            legacy=calculate_shear_pin(u,v,d,t,qty,od,ot,inner,it)
            actual=evaluate(*bounds,qty,planes,ann,ids,factor=factor)
            for a,b in zip(actual,legacy):self.assertTrue(math.isclose(a,b*planes*factor/.6,rel_tol=1e-12))
    def test_force_only_solid_and_invalid(self):
        u=(75000,85000);d=(.248,.252)
        f=evaluate(u,d,4,2)
        self.assertEqual(f[2:],(None,None))
        solid=evaluate(u,d,4,2,(3,3),(0,0))
        self.assertAlmostEqual(solid[2],f[0]/(math.pi*9/4))
        for factor in (0,-1,1.01,float("nan"),float("inf")):
            with self.assertRaises(ValueError):evaluate(u,d,4,2,factor=factor)
        for od,idd in (((2,3),(1,2)),((2,3),(2.5,2.6))):
            with self.assertRaises(ValueError):evaluate(u,d,4,2,od,idd)
if __name__=="__main__":unittest.main()
