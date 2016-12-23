"""Configuration file parsing and utilities."""

import copy
import itertools
import os
from collections import Set, namedtuple
from re import compile as re


try:  # Python 3.x
    from ConfigParser import RawConfigParser
except ImportError:  # Python 2.x
    from configparser import RawConfigParser


from .utils import __version__, log
from .violations import ErrorRegistry, conventions


def check_initialized(method):
    """Check that the configuration object was initialized."""
    def _decorator(self, *args, **kwargs):
        if self._arguments is None or self._options is None:
            raise RuntimeError('using an uninitialized configuration')
        return method(self, *args, **kwargs)
    return _decorator


class ConfigurationParser(object):
    """Responsible for parsing configuration from files and CLI.

    There are 2 types of configurations: Run configurations and Check
    configurations.

    Run Configurations:
    ------------------
    Responsible for deciding things that are related to the user interface,
    e.g. verbosity, debug options, etc.
    All run configurations default to `False` and are decided only by CLI.

    Check Configurations:
    --------------------
    Configurations that are related to which files and errors will be checked.
    These are configurable in 2 ways: using the CLI, and using configuration
    files.

    Configuration files are nested within the file system, meaning that the
    closer a configuration file is to a checked file, the more relevant it will
    be. For instance, imagine this directory structure:

    A
    +-- tox.ini: sets `select=D100`
    +-- B
        +-- foo.py
        +-- tox.ini: sets `add-ignore=D100`

    Then `foo.py` will not be checked for `D100`.
    The configuration build algorithm is described in `self._get_config`.

    Note: If any of `BASE_ERROR_SELECTION_OPTIONS` was selected in the CLI, all
    configuration files will be ignored and each file will be checked for
    the error codes supplied in the CLI.

    """

    CONFIG_FILE_OPTIONS = ('convention', 'select', 'ignore', 'add-select',
                           'add-ignore', 'match', 'match-dir')
    BASE_ERROR_SELECTION_OPTIONS = ('ignore', 'select', 'convention')

    DEFAULT_MATCH_RE = '(?!test_).*\.py'
    DEFAULT_MATCH_DIR_RE = '[^\.].*'
    DEFAULT_CONVENTION = conventions.pep257

    PROJECT_CONFIG_FILES = (
        'setup.cfg',
        'tox.ini',
        '.pydocstyle',
        '.pydocstylerc',
        # The following is deprecated, but remains for backwards compatibility.
        '.pep257',
    )

    POSSIBLE_SECTION_NAMES = ('pydocstyle', 'pep257')

    def __init__(self):
        """Create a configuration parser."""
        self._cache = {}
        self._override_by_cli = None
        self._options = self._arguments = self._run_conf = None
        self._parser = self._create_option_parser()

    # ---------------------------- Public Methods -----------------------------

    def get_default_run_configuration(self):
        """Return a `RunConfiguration` object set with default values."""
        options, _ = self._parse_args([])
        return self._create_run_config(options)

    def parse(self):
        """Parse the configuration.

        If one of `BASE_ERROR_SELECTION_OPTIONS` was selected, overrides all
        error codes to check and disregards any error code related
        configurations from the configuration files.

        """
        self._options, self._arguments = self._parse_args()
        self._arguments = self._arguments or ['.']

        if not self._validate_options(self._options):
            raise IllegalConfiguration()

        self._run_conf = self._create_run_config(self._options)

        config = self._create_check_config(self._options, use_dafaults=False)
        self._override_by_cli = config

    @check_initialized
    def get_user_run_configuration(self):
        """Return the run configuration for the script."""
        return self._run_conf

    @check_initialized
    def get_files_to_check(self):
        """Generate files and error codes to check on each one.

        Walk dir trees under `self._arguments` and generate yield filnames
        that `match` under each directory that `match_dir`.
        The method locates the configuration for each file name and yields a
        tuple of (filename, [error_codes]).

        With every discovery of a new configuration file `IllegalConfiguration`
        might be raised.

        """
        def _get_matches(config):
            """Return the `match` and `match_dir` functions for `config`."""
            match_func = re(config.match + '$').match
            match_dir_func = re(config.match_dir + '$').match
            return match_func, match_dir_func

        for name in self._arguments:
            if os.path.isdir(name):
                for root, dirs, filenames in os.walk(name):
                    config = self._get_config(root)
                    match, match_dir = _get_matches(config)

                    # Skip any dirs that do not match match_dir
                    dirs[:] = [dir for dir in dirs if match_dir(dir)]

                    for filename in filenames:
                        if match(filename):
                            full_path = os.path.join(root, filename)
                            yield full_path, list(config.checked_codes)
            else:
                config = self._get_config(name)
                match, _ = _get_matches(config)
                if match(name):
                    yield name, list(config.checked_codes)

    # --------------------------- Private Methods -----------------------------

    def _get_config(self, node):
        """Get and cache the run configuration for `node`.

        If no configuration exists (not local and not for the parend node),
        returns and caches a default configuration.

        The algorithm:
        -------------
        * If the current directory's configuration exists in
           `self._cache` - return it.
        * If a configuration file does not exist in this directory:
          * If the directory is not a root directory:
            * Cache its configuration as this directory's and return it.
          * Else:
            * Cache a default configuration and return it.
        * Else:
          * Read the configuration file.
          * If a parent directory exists AND the configuration file
            allows inheritance:
            * Read the parent configuration by calling this function with the
              parent directory as `node`.
            * Merge the parent configuration with the current one and
              cache it.
        * If the user has specified one of `BASE_ERROR_SELECTION_OPTIONS` in
          the CLI - return the CLI configuration with the configuration match
          clauses
        * Set the `--add-select` and `--add-ignore` CLI configurations.

        """
        path = os.path.abspath(node)
        path = path if os.path.isdir(path) else os.path.dirname(path)

        if path in self._cache:
            return self._cache[path]

        config_file = self._get_config_file_in_folder(path)

        if config_file is None:
            parent_dir, tail = os.path.split(path)
            if tail:
                # No configuration file, simply take the parent's.
                config = self._get_config(parent_dir)
            else:
                # There's no configuration file and no parent directory.
                # Use the default configuration or the one given in the CLI.
                config = self._create_check_config(self._options)
        else:
            # There's a config file! Read it and merge if necessary.
            options, inherit = self._read_configuration_file(config_file)

            parent_dir, tail = os.path.split(path)
            if tail and inherit:
                # There is a parent dir and we should try to merge.
                parent_config = self._get_config(parent_dir)
                config = self._merge_configuration(parent_config, options)
            else:
                # No need to merge or parent dir does not exist.
                config = self._create_check_config(options)

        # Make the CLI always win
        final_config = {}
        for attr in CheckConfiguration._fields:
            cli_val = getattr(self._override_by_cli, attr)
            conf_val = getattr(config, attr)
            final_config[attr] = cli_val if cli_val is not None else conf_val

        config = CheckConfiguration(**final_config)

        self._set_add_options(config.checked_codes, self._options)
        self._cache[path] = config
        return self._cache[path]

    def _read_configuration_file(self, path):
        """Try to read and parse `path` as a configuration file.

        If the configurations were illegal (checked with
        `self._validate_options`), raises `IllegalConfiguration`.

        Returns (options, should_inherit).

        """
        parser = RawConfigParser()
        options = None
        should_inherit = True

        if parser.read(path) and self._get_section_name(parser):
            option_list = dict([(o.dest, o.type or o.action)
                                for o in self._parser.option_list])

            # First, read the default values
            new_options, _ = self._parse_args([])

            # Second, parse the configuration
            section_name = self._get_section_name(parser)
            for opt in parser.options(section_name):
                if opt == 'inherit':
                    should_inherit = parser.getboolean(section_name, opt)
                    continue

                if opt.replace('_', '-') not in self.CONFIG_FILE_OPTIONS:
                    log.warning("Unknown option '{0}' ignored".format(opt))
                    continue

                normalized_opt = opt.replace('-', '_')
                opt_type = option_list[normalized_opt]
                if opt_type in ('int', 'count'):
                    value = parser.getint(section_name, opt)
                elif opt_type == 'string':
                    value = parser.get(section_name, opt)
                else:
                    assert opt_type in ('store_true', 'store_false')
                    value = parser.getboolean(section_name, opt)
                setattr(new_options, normalized_opt, value)

            # Third, fix the set-options
            options = self._fix_set_options(new_options)

        if options is not None:
            if not self._validate_options(options):
                raise IllegalConfiguration('in file: {0}'.format(path))

        return options, should_inherit

    def _merge_configuration(self, parent_config, child_options):
        """Merge parent config into the child options.

        The migration process requires an `options` object for the child in
        order to distinguish between mutually exclusive codes, add-select and
        add-ignore error codes.

        """
        # Copy the parent error codes so we won't override them
        error_codes = copy.deepcopy(parent_config.checked_codes)
        if self._has_exclusive_option(child_options):
            error_codes = self._get_exclusive_error_codes(child_options)

        self._set_add_options(error_codes, child_options)

        match = child_options.match \
            if child_options.match is not None else parent_config.match
        match_dir = child_options.match_dir \
            if child_options.match_dir is not None else parent_config.match_dir

        return CheckConfiguration(checked_codes=error_codes,
                                  match=match,
                                  match_dir=match_dir)

    def _parse_args(self, args=None, values=None):
        """Parse the options using `self._parser` and reformat the options."""
        options, arguments = self._parser.parse_args(args, values)
        return self._fix_set_options(options), arguments

    @staticmethod
    def _create_run_config(options):
        """Create a `RunConfiguration` object from `options`."""
        values = dict([(opt, getattr(options, opt)) for opt in
                       RunConfiguration._fields])
        return RunConfiguration(**values)

    @classmethod
    def _create_check_config(cls, options, use_dafaults=True):
        """Create a `CheckConfiguration` object from `options`.

        If `use_dafaults`, any of the match options that are `None` will
        be replaced with their default value and the default convention will be
        set for the checked codes.

        """
        match = cls.DEFAULT_MATCH_RE \
            if options.match is None and use_dafaults \
            else options.match

        match_dir = cls.DEFAULT_MATCH_DIR_RE \
            if options.match_dir is None and use_dafaults \
            else options.match_dir

        checked_codes = None

        if cls._has_exclusive_option(options) or use_dafaults:
            checked_codes = cls._get_checked_errors(options)

        return CheckConfiguration(checked_codes=checked_codes,
                                  match=match, match_dir=match_dir)

    @classmethod
    def _get_section_name(cls, parser):
        """Parse options from relevant section."""
        for section_name in cls.POSSIBLE_SECTION_NAMES:
            if parser.has_section(section_name):
                return section_name

        return None

    @classmethod
    def _get_config_file_in_folder(cls, path):
        """Look for a configuration file in `path`.

        If exists return it's full path, otherwise None.

        """
        if os.path.isfile(path):
            path = os.path.dirname(path)

        for fn in cls.PROJECT_CONFIG_FILES:
            config = RawConfigParser()
            full_path = os.path.join(path, fn)
            if config.read(full_path) and cls._get_section_name(config):
                return full_path

    @staticmethod
    def _get_exclusive_error_codes(options):
        """Extract the error codes from the selected exclusive option."""
        codes = set(ErrorRegistry.get_error_codes())
        checked_codes = None

        if options.ignore is not None:
            checked_codes = codes - options.ignore
        elif options.select is not None:
            checked_codes = options.select
        elif options.convention is not None:
            checked_codes = getattr(conventions, options.convention)

        # To not override the conventions nor the options - copy them.
        return copy.deepcopy(checked_codes)

    @staticmethod
    def _set_add_options(checked_codes, options):
        """Set `checked_codes` by the `add_ignore` or `add_select` options."""
        checked_codes |= options.add_select
        checked_codes -= options.add_ignore

    @classmethod
    def _get_checked_errors(cls, options):
        """Extract the codes needed to be checked from `options`."""
        checked_codes = cls._get_exclusive_error_codes(options)
        if checked_codes is None:
            checked_codes = cls.DEFAULT_CONVENTION

        cls._set_add_options(checked_codes, options)

        return checked_codes

    @classmethod
    def _validate_options(cls, options):
        """Validate the mutually exclusive options.

        Return `True` iff only zero or one of `BASE_ERROR_SELECTION_OPTIONS`
        was selected.

        """
        for opt1, opt2 in \
                itertools.permutations(cls.BASE_ERROR_SELECTION_OPTIONS, 2):
            if getattr(options, opt1) and getattr(options, opt2):
                log.error('Cannot pass both {0} and {1}. They are '
                          'mutually exclusive.'.format(opt1, opt2))
                return False

        if options.convention and options.convention not in conventions:
            log.error("Illegal convention '{0}'. Possible conventions: {1}"
                      .format(options.convention,
                              ', '.join(conventions.keys())))
            return False
        return True

    @classmethod
    def _has_exclusive_option(cls, options):
        """Return `True` iff one or more exclusive options were selected."""
        return any([getattr(options, opt) is not None for opt in
                    cls.BASE_ERROR_SELECTION_OPTIONS])

    @staticmethod
    def _fix_set_options(options):
        """Alter the set options from None/strings to sets in place."""
        optional_set_options = ('ignore', 'select')
        mandatory_set_options = ('add_ignore', 'add_select')

        def _get_set(value_str):
            """Split `value_str` by the delimiter `,` and return a set.

            Removes any occurrences of '' in the set.

            """
            return set(value_str.split(',')) - set([''])

        for opt in optional_set_options:
            value = getattr(options, opt)
            if value is not None:
                setattr(options, opt, _get_set(value))

        for opt in mandatory_set_options:
            value = getattr(options, opt)
            if value is None:
                value = ''

            if not isinstance(value, Set):
                value = _get_set(value)

            setattr(options, opt, value)

        return options

    @classmethod
    def _create_option_parser(cls):
        """Return an option parser to parse the command line arguments."""
        from optparse import OptionParser

        parser = OptionParser(
            version=__version__,
            usage='Usage: pydocstyle [options] [<file|dir>...]')

        option = parser.add_option

        # Run configuration options
        option('-e', '--explain', action='store_true', default=False,
               help='show explanation of each error')
        option('-s', '--source', action='store_true', default=False,
               help='show source for each error')
        option('-d', '--debug', action='store_true', default=False,
               help='print debug information')
        option('-v', '--verbose', action='store_true', default=False,
               help='print status information')
        option('--count', action='store_true', default=False,
               help='print total number of errors to stdout')

        # Error check options
        option('--select', metavar='<codes>', default=None,
               help='choose the basic list of checked errors by '
                    'specifying which errors to check for (with a list of '
                    'comma-separated error codes). '
                    'for example: --select=D101,D202')
        option('--ignore', metavar='<codes>', default=None,
               help='choose the basic list of checked errors by '
                    'specifying which errors to ignore (with a list of '
                    'comma-separated error codes). '
                    'for example: --ignore=D101,D202')
        option('--convention', metavar='<name>', default=None,
               help='choose the basic list of checked errors by specifying an '
                    'existing convention. Possible conventions: {0}'
                    .format(', '.join(conventions)))
        option('--add-select', metavar='<codes>', default=None,
               help='amend the list of errors to check for by specifying '
                    'more error codes to check.')
        option('--add-ignore', metavar='<codes>', default=None,
               help='amend the list of errors to check for by specifying '
                    'more error codes to ignore.')

        # Match clauses
        option('--match', metavar='<pattern>', default=None,
               help=("check only files that exactly match <pattern> regular "
                     "expression; default is --match='{0}' which matches "
                     "files that don't start with 'test_' but end with "
                     "'.py'").format(cls.DEFAULT_MATCH_RE))
        option('--match-dir', metavar='<pattern>', default=None,
               help=("search only dirs that exactly match <pattern> regular "
                     "expression; default is --match-dir='{0}', which "
                     "matches all dirs that don't start with "
                     "a dot").format(cls.DEFAULT_MATCH_DIR_RE))

        return parser


# Check configuration - used by the ConfigurationParser class.
CheckConfiguration = namedtuple('CheckConfiguration',
                                ('checked_codes', 'match', 'match_dir'))


class IllegalConfiguration(Exception):
    """An exception for illegal configurations."""

    pass


# General configurations for pydocstyle run.
RunConfiguration = namedtuple('RunConfiguration',
                              ('explain', 'source', 'debug',
                               'verbose', 'count'))
