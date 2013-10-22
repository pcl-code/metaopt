from mock import Mock

from orges.framework.paramspec import ParamSpec
from orges.framework.args import ArgsCreator
from orges.invoker.simpleinvoker import SimpleInvoker

def f(a, b):
    return a + b

param_spec = ParamSpec()
param_spec.int("a").interval((1, 10))
param_spec.int("b").interval((1, 10))

args_creator = ArgsCreator(param_spec)
args = args_creator.args()


def test_invoke_calls_on_result():
    invoker = SimpleInvoker()

    caller = Mock()

    caller.on_result = Mock()
    caller.on_error = Mock()

    invoker.caller = caller
    invoker.invoke(f, args)

    caller.on_result.assert_called_with(args, 2)

def test_invoke_given_extra_args_calls_on_result_with_them():
    invoker = SimpleInvoker()

    caller = Mock()

    caller.on_result = Mock()
    caller.on_error = Mock()

    invoker.caller = caller

    data = object()
    invoker.invoke(f, args, data)

    caller.on_result.assert_called_with(args, 2, data)

if __name__ == '__main__':
    import nose
    nose.runmodule()

