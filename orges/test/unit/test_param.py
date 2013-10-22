import orges.param as param

from nose.tools import eq_

def test_int_first_param_creates_param_spec():
    @param.int("a", interval=(1, 10))
    def f():
        pass

    assert "a" in f.param_spec.params

def test_int_multiple_params_are_saved():
    @param.int("a", interval=(1, 10))
    @param.int("b", interval=(1, 10))
    def f():
        pass

    assert "a" in f.param_spec.params
    assert "b" in f.param_spec.params

def test_int_multiple_params_are_saved_in_order():
    @param.int("a", interval=(1, 10))
    @param.int("b", interval=(1, 10))
    def f():
        pass

    eq_(list(f.param_spec.params), ["a", "b"])

if __name__ == '__main__':
    import nose
    nose.runmodule()

