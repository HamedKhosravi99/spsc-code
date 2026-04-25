from .environment import LowRankLDSEnvironment
from .covertype_environment import CovtypeEnvironment
from .real_covtype_environment_v2 import RealCovtypeEnvironmentV2
from .real_pendigits_environment import RealPendigitsEnvironment
from .real_satimage_environment import RealSatimageEnvironment
from .warfarin_environment import WarfarinEnvironment
from .movielens_environment import MovieLensEnvironment
from .real_movielens_environment import RealMovieLensEnvironment
from .jester_environment import RealJesterEnvironment
from .lastfm_environment import RealLastfmEnvironment
from .fashion_mnist_environment import FashionMNISTEnvironment
from .mnist_environment import MNISTEnvironment
from .newsgroups_environment import NewsgroupsEnvironment

# OpenBandit Pipeline (real exploration logs).  Soft-imported because
# the `obp` package is an optional dependency.
try:
    from .openbandit_environment import OpenBanditEnvironment
except ImportError:
    OpenBanditEnvironment = None
