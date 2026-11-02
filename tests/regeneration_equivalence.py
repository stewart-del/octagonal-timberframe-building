"""Strict structure/topology equality plus unit-aware float roundoff bounds.

Native BLAS CPU dispatch changes last-bit reductions even with identical Python,
NumPy and Manifold versions. This is NOT a geometric validity test replacement.
The caller still runs independent stock/contact/intersection/volume checks.
"""
import math

def tolerance(path):
    fields=[part for part in path if isinstance(part,str)]
    if any(field.endswith('_m3') for field in fields):
        return 1e-13  # <6.2e-9 in^3, stricter than the 1e-6 in^3 overlap limit.
    if any(field.endswith('_in3') for field in fields):
        return 1e-9   # Numerical zero/isometry residual: 1/1000 overlap limit.
    if any(field.endswith('_in2') for field in fields):
        return 1e-9   # Square inches, not a relative or percentage tolerance.
    return 1e-11      # Metre coordinates: 0.01 nanometre; inch values still tiny.

def assert_equivalent(actual,expected,path=(),stats=None):
    if stats is None:stats={'float_differences':0,'max_fraction_of_tolerance':0.0,'worst_path':None}
    location='/'.join(map(str,path)) or '<root>'
    # In particular bool and integer IDs/index arrays never use float tolerance.
    assert type(actual) is type(expected),(location,'type',type(actual),type(expected))
    if isinstance(actual,dict):
        assert actual.keys()==expected.keys(),(location,'keys',actual.keys(),expected.keys())
        for key in actual:assert_equivalent(actual[key],expected[key],path+(key,),stats)
    elif isinstance(actual,list):
        assert len(actual)==len(expected),(location,'length',len(actual),len(expected))
        for i,(a,b) in enumerate(zip(actual,expected)):assert_equivalent(a,b,path+(i,),stats)
    elif isinstance(actual,float):
        assert math.isfinite(actual) and math.isfinite(expected),(location,'non-finite')
        error=abs(actual-expected);limit=tolerance(path)
        assert error<=limit,(location,'float drift',actual,expected,error,'absolute limit',limit)
        if error:
            stats['float_differences']+=1
            if error/limit>stats['max_fraction_of_tolerance']:
                stats.update(max_fraction_of_tolerance=error/limit,worst_path=location)
    else:
        assert actual==expected,(location,'exact value',actual,expected)
    return stats

def test_guard():
    # Allow only sub-tolerance roundoff, not changed topology, data shape, claims,
    # nonfinite values, or a real geometric drift. Exercise the guard itself.
    base={'id':'J0-0','vertices':[[1.0,2.0,3.0]],'triangles':[[0,1,2]],'volume_m3':0.1,'residual_in3':0.0,'capacity_checked':False}
    import copy
    okay=copy.deepcopy(base);okay['vertices'][0][0]+=1e-12;okay['residual_in3']=7e-11
    assert_equivalent(okay,base)
    mutations=[lambda d:d.update(id='J0-2'),lambda d:d['triangles'][0].__setitem__(1,2),lambda d:d['vertices'].append([0.,0.,0.]),lambda d:d['vertices'][0].__setitem__(0,1.+1e-8),lambda d:d.update(volume_m3=.1+1e-11),lambda d:d.update(residual_in3=1e-7),lambda d:d.update(capacity_checked=True),lambda d:d['vertices'][0].__setitem__(0,float('nan')),lambda d:d.update(extra='changed')]
    for mutate in mutations:
        bad=copy.deepcopy(base);mutate(bad)
        try:assert_equivalent(bad,base)
        except AssertionError:continue
        raise AssertionError('Equivalence guard accepted a deliberate invalid change')
