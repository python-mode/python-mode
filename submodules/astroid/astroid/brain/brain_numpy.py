# Copyright (c) 2015-2016 Claudiu Popa <pcmanticore@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER


"""Astroid hooks for numpy."""

import astroid


def numpy_random_mtrand_transform():
    return astroid.parse('''
    def beta(a, b, size=None): pass
    def binomial(n, p, size=None): pass
    def bytes(length): pass
    def chisquare(df, size=None): pass
    def choice(a, size=None, replace=True, p=None): pass
    def dirichlet(alpha, size=None): pass
    def exponential(scale=1.0, size=None): pass
    def f(dfnum, dfden, size=None): pass
    def gamma(shape, scale=1.0, size=None): pass
    def geometric(p, size=None): pass
    def get_state(): pass
    def gumbel(loc=0.0, scale=1.0, size=None): pass
    def hypergeometric(ngood, nbad, nsample, size=None): pass
    def laplace(loc=0.0, scale=1.0, size=None): pass
    def logistic(loc=0.0, scale=1.0, size=None): pass
    def lognormal(mean=0.0, sigma=1.0, size=None): pass
    def logseries(p, size=None): pass
    def multinomial(n, pvals, size=None): pass
    def multivariate_normal(mean, cov, size=None): pass
    def negative_binomial(n, p, size=None): pass
    def noncentral_chisquare(df, nonc, size=None): pass
    def noncentral_f(dfnum, dfden, nonc, size=None): pass
    def normal(loc=0.0, scale=1.0, size=None): pass
    def pareto(a, size=None): pass
    def permutation(x): pass
    def poisson(lam=1.0, size=None): pass
    def power(a, size=None): pass
    def rand(*args): pass
    def randint(low, high=None, size=None, dtype='l'): pass
    def randn(*args): pass
    def random_integers(low, high=None, size=None): pass
    def random_sample(size=None): pass
    def rayleigh(scale=1.0, size=None): pass
    def seed(seed=None): pass
    def set_state(state): pass
    def shuffle(x): pass
    def standard_cauchy(size=None): pass
    def standard_exponential(size=None): pass
    def standard_gamma(shape, size=None): pass
    def standard_normal(size=None): pass
    def standard_t(df, size=None): pass
    def triangular(left, mode, right, size=None): pass
    def uniform(low=0.0, high=1.0, size=None): pass
    def vonmises(mu, kappa, size=None): pass
    def wald(mean, scale, size=None): pass
    def weibull(a, size=None): pass
    def zipf(a, size=None): pass
    ''')


def numpy_core_umath_transform():
    ufunc_optional_keyword_arguments = ("""out=None, where=True, casting='same_kind', order='K', """
                                        """dtype=None, subok=True""")
    return astroid.parse('''
    # Constants
    e = 2.718281828459045
    euler_gamma = 0.5772156649015329

    # No arg functions
    def geterrobj(): pass

    # One arg functions
    def seterrobj(errobj): pass

    # One arg functions with optional kwargs
    def arccos(x, {opt_args:s}): pass
    def arccosh(x, {opt_args:s}): pass
    def arcsin(x, {opt_args:s}): pass
    def arcsinh(x, {opt_args:s}): pass
    def arctan(x, {opt_args:s}): pass
    def arctanh(x, {opt_args:s}): pass
    def cbrt(x, {opt_args:s}): pass
    def conj(x, {opt_args:s}): pass
    def conjugate(x, {opt_args:s}): pass
    def cosh(x, {opt_args:s}): pass
    def deg2rad(x, {opt_args:s}): pass
    def degrees(x, {opt_args:s}): pass
    def exp2(x, {opt_args:s}): pass
    def expm1(x, {opt_args:s}): pass
    def fabs(x, {opt_args:s}): pass
    def frexp(x, {opt_args:s}): pass
    def isfinite(x, {opt_args:s}): pass
    def isinf(x, {opt_args:s}): pass
    def log(x, {opt_args:s}): pass
    def log1p(x, {opt_args:s}): pass
    def log2(x, {opt_args:s}): pass
    def logical_not(x, {opt_args:s}): pass
    def modf(x, {opt_args:s}): pass
    def negative(x, {opt_args:s}): pass
    def rad2deg(x, {opt_args:s}): pass
    def radians(x, {opt_args:s}): pass
    def reciprocal(x, {opt_args:s}): pass
    def rint(x, {opt_args:s}): pass
    def sign(x, {opt_args:s}): pass
    def signbit(x, {opt_args:s}): pass
    def sinh(x, {opt_args:s}): pass
    def spacing(x, {opt_args:s}): pass
    def square(x, {opt_args:s}): pass
    def tan(x, {opt_args:s}): pass
    def tanh(x, {opt_args:s}): pass
    def trunc(x, {opt_args:s}): pass
    
    # Two args functions with optional kwargs
    def bitwise_and(x1, x2, {opt_args:s}): pass
    def bitwise_or(x1, x2, {opt_args:s}): pass
    def bitwise_xor(x1, x2, {opt_args:s}): pass
    def copysign(x1, x2, {opt_args:s}): pass
    def divide(x1, x2, {opt_args:s}): pass
    def equal(x1, x2, {opt_args:s}): pass
    def float_power(x1, x2, {opt_args:s}): pass
    def floor_divide(x1, x2, {opt_args:s}): pass
    def fmax(x1, x2, {opt_args:s}): pass
    def fmin(x1, x2, {opt_args:s}): pass
    def fmod(x1, x2, {opt_args:s}): pass
    def greater(x1, x2, {opt_args:s}): pass
    def hypot(x1, x2, {opt_args:s}): pass
    def ldexp(x1, x2, {opt_args:s}): pass
    def left_shift(x1, x2, {opt_args:s}): pass
    def less(x1, x2, {opt_args:s}): pass
    def logaddexp(x1, x2, {opt_args:s}): pass
    def logaddexp2(x1, x2, {opt_args:s}): pass
    def logical_and(x1, x2, {opt_args:s}): pass
    def logical_or(x1, x2, {opt_args:s}): pass
    def logical_xor(x1, x2, {opt_args:s}): pass
    def maximum(x1, x2, {opt_args:s}): pass
    def minimum(x1, x2, {opt_args:s}): pass
    def nextafter(x1, x2, {opt_args:s}): pass
    def not_equal(x1, x2, {opt_args:s}): pass
    def power(x1, x2, {opt_args:s}): pass
    def remainder(x1, x2, {opt_args:s}): pass
    def right_shift(x1, x2, {opt_args:s}): pass
    def subtract(x1, x2, {opt_args:s}): pass
    def true_divide(x1, x2, {opt_args:s}): pass
    '''.format(opt_args=ufunc_optional_keyword_arguments))


def numpy_core_numerictypes_transform():
    return astroid.parse('''
    # different types defined in numerictypes.py
    # np_type_common aggregates all public methods
    # that are common between numpy.uint* and numpy.float*
    class np_type_common(int):
        def all(self): pass
        def any(self): pass
        def argmax(self): pass
        def argmin(self): pass
        def argsort(self): pass
        def astype(self): pass
        def base(self): pass
        def byteswap(self): pass
        def choose(self): pass
        def clip(self): pass
        def compress(self): pass
        def conj(self): pass
        def conjugate(self): pass
        def copy(self): pass
        def cumprod(self): pass
        def cumsum(self): pass
        def data(self): pass
        def diagonal(self): pass
        def dtype(self): pass
        def dump(self): pass
        def dumps(self): pass
        def fill(self): pass
        def flags(self): pass
        def flat(self): pass
        def flatten(self): pass
        def getfield(self): pass
        def imag(self): pass
        def item(self): pass
        def itemset(self): pass
        def itemsize(self): pass
        def max(self): pass
        def mean(self): pass
        def min(self): pass
        def nbytes(self): pass
        def ndim(self): pass
        def newbyteorder(self): pass
        def nonzero(self): pass
        def prod(self): pass
        def ptp(self): pass
        def put(self): pass
        def ravel(self): pass
        def real(self): pass
        def repeat(self): pass
        def reshape(self): pass
        def resize(self): pass
        def round(self): pass
        def searchsorted(self): pass
        def setfield(self): pass
        def setflags(self): pass
        def shape(self): pass
        def size(self): pass
        def sort(self): pass
        def squeeze(self): pass
        def std(self): pass
        def strides(self): pass
        def sum(self): pass
        def swapaxes(self): pass
        def take(self): pass
        def tobytes(self): pass
        def tofile(self): pass
        def tolist(self): pass
        def tostring(self): pass
        def trace(self): pass
        def transpose(self): pass
        def var(self): pass
        def view(self): pass

    # uint_common contains all the public methods present
    # inside numpy.uint*
    class uint_common(np_type_common):
        def denominator(self): pass
        def numerator(self): pass

    # float_common contains all the public methods present
    # inside numpy.float*
    class float_common(np_type_common):
        def as_integer_ratio(self): pass
        def fromhex(self, val): pass
        def hex(self): pass
        def is_integer(self): pass

    class uint16(uint_common): pass
    class uint32(uint_common): pass
    class uint64(uint_common): pass
    class uint128(uint_common): pass
   
    class float16(float_common): pass
    class float32(float_common): pass
    class float64(float_common): pass
    class float80(float_common): pass
    class float96(float_common): pass
    class float128(float_common): pass
    class float256(float_common): pass

    class complex32(np_type_common): pass
    class complex64(np_type_common): pass
    class complex128(np_type_common): pass
    class complex160(np_type_common): pass
    class complex192(np_type_common): pass
    class complex256(np_type_common): pass
    class complex512(np_type_common): pass

    class int128(uint_common):
        def bit_length(self): pass

    class timedelta64(uint_common): pass
    
    class datetime64(np_type_common): pass

    class string_(np_type_common):
        def capitalize(self): pass
        def center(self, width, fillchar=' '): pass
        def count(self, sub, start=None, end=None): pass
        def decode(self, encoding='default', errors='strict'): pass
        def encode(self, encoding='default', errors='strict'): pass
        def endswith(self, suffix, start=None, end=None): pass
        def expandtabs(self, tabsize=8): pass
        def find(self, sub, start=None, end=None): pass
        def format(self, *args, **kwargs): pass
        def index(self, sub, start=None, end=None): pass
        def isalnum(self): pass
        def isalpha(self): pass
        def isdigit(self): pass
        def islower(self): pass
        def isspace(self): pass
        def istitle(self): pass
        def isupper(self): pass
        def join(self, iterable): pass
        def ljust(self, width, fillchar=' '): pass
        def lower(self): pass
        def lstrip(self, chars=None): pass
        def partition(self, sep): pass
        def replace(self, old, new, count=None): pass
        def rfind(self, sub, start=None, end=None): pass
        def rindex(self, sub, start=None, end=None): pass
        def rjust(self, width, fillchar=' '): pass
        def rpartition(self, sep): pass
        def rsplit(self, sep=None, maxsplit=None): pass
        def rstrip(self, chars=None): pass
        def split(self, sep=None, maxsplit=None): pass
        def splitlines(self, keepends=False): pass
        def startswith(self, prefix, start=None, end=None): pass
        def strip(self, chars=None): pass
        def swapcase(self): pass
        def title(self): pass
        def translate(self, table, deletechars=None): pass
        def upper(self): pass
        def zfill(self, width): pass

    class unicode_(string_):
        def isdecimal(self): pass
        def isnumeric(self): pass

    object_ = type('object_')
    ''')


def numpy_funcs():
    return astroid.parse('''
    import builtins
    def sum(a, axis=None, dtype=None, out=None, keepdims=None):
        return builtins.sum(a)
    ''')


astroid.register_module_extender(astroid.MANAGER, 'numpy.core.umath', numpy_core_umath_transform)
astroid.register_module_extender(astroid.MANAGER, 'numpy.random.mtrand',
                                 numpy_random_mtrand_transform)
astroid.register_module_extender(astroid.MANAGER, 'numpy.core.numerictypes',
                                 numpy_core_numerictypes_transform)
astroid.register_module_extender(astroid.MANAGER, 'numpy', numpy_funcs)
