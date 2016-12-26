Home-page:  http://github.com/klen/pylama
Author: Kirill Klenov
Author-email: horneds@gmail.com
License: GNU LGPL
Description: |logo| Pylama
        #############
        
        .. _description:
        
        Code audit tool for Python and JavaScript. Pylama wraps these tools:
        
        * pycodestyle_ (formerly pep8) © 2012-2013, Florent Xicluna;
        * pydocstyle_ (formerly pep257 by Vladimir Keleshev) © 2014, Amir Rachum;
        * PyFlakes_ © 2005-2013, Kevin Watters;
        * Mccabe_ © Ned Batchelder;
        * Pylint_ © 2013, Logilab (should be installed 'pylama_pylint' module);
        * Radon_ © Michele Lacchia
        * gjslint_ © The Closure Linter Authors (should be installed 'pylama_gjslint' module);
        
        .. _badges:
        
        .. image:: http://img.shields.io/travis/klen/pylama.svg?style=flat-square
            :target: http://travis-ci.org/klen/pylama
            :alt: Build Status
        
        .. image:: http://img.shields.io/coveralls/klen/pylama.svg?style=flat-square
            :target: https://coveralls.io/r/klen/pylama
            :alt: Coverals
        
        .. image:: http://img.shields.io/pypi/v/pylama.svg?style=flat-square
            :target: https://crate.io/packages/pylama
            :alt: Version
        
        .. image:: http://img.shields.io/gratipay/klen.svg?style=flat-square
            :target: https://www.gratipay.com/klen/
            :alt: Donate
        
        
        .. _documentation:
        
        Docs are available at https://pylama.readthedocs.org/. Pull requests with documentation enhancements and/or fixes are awesome and most welcome.
        
        
        .. _contents:
        
        .. contents::
        
        .. _requirements:
        
        Requirements:
        =============
        
        - Python (2.6, 2.7, 3.2, 3.3)
        - To use JavaScript checker (``gjslint``) you need to install ``python-gflags`` with ``pip install python-gflags``.
        - If your tests are failing on Win platform you are missing: ``curses`` - http://www.lfd.uci.edu/~gohlke/pythonlibs/
          (The curses library supplies a terminal-independent screen-painting and keyboard-handling facility for text-based terminals)
        
        
        .. _installation:
        
        Installation:
        =============
        **Pylama** could be installed using pip: ::
        ::
        
            $ pip install pylama
        
        
        .. _quickstart:
        
        Quickstart
        ==========
        
        **Pylama** is easy to use and really fun for checking code quality.
        Just run `pylama` and get common output from all pylama plugins (pycodestyle_, PyFlakes_ and etc)
        
        Recursive check the current directory. ::
        
            $ pylama
        
        Recursive check a path. ::
        
            $ pylama <path_to_directory_or_file>
        
        Ignore errors ::
        
            $ pylama -i W,E501
        
        .. note:: You could choose a group erros `D`,`E1` and etc or special errors `C0312`
        
        Choose code checkers ::
        
            $ pylama -l "pycodestyle,mccabe"
        
        Choose code checkers for JavaScript::
        
            $ pylama --linters=gjslint --ignore=E:0010 <path_to_directory_or_file>
        
        .. _options:
        
        Set Pylama (checkers) options
        =============================
        
        Command line options
        --------------------
        
        ::
        
            $ pylama --help
        
            usage: pylama [-h] [--verbose] [--version] [--format {pycodestyle,pylint}]
                          [--select SELECT] [--sort SORT] [--linters LINTERS]
                          [--ignore IGNORE] [--skip SKIP] [--report REPORT] [--hook]
                          [--async] [--options OPTIONS] [--force] [--abspath]
                          [paths [paths ...]]
        
            Code audit tool for python.
        
            positional arguments:
              paths                 Paths to files or directories for code check.
        
            optional arguments:
              -h, --help            show this help message and exit
              --verbose, -v         Verbose mode.
              --version             show program's version number and exit
              --format {pycodestyle,pylint}, -f {pycodestyle,pylint}
                                    Choose errors format (pycodestyle, pylint).
              --select SELECT, -s SELECT
                                    Select errors and warnings. (comma-separated list)
              --sort SORT           Sort result by error types. Ex. E,W,D
              --linters LINTERS, -l LINTERS
                                    Select linters. (comma-separated). Choices are
                                    mccabe,pycodestyle,pyflakes,pydocstyle.
              --ignore IGNORE, -i IGNORE
                                    Ignore errors and warnings. (comma-separated)
              --skip SKIP           Skip files by masks (comma-separated, Ex.
                                    */messages.py)
              --report REPORT, -r REPORT
                                    Send report to file [REPORT]
              --hook                Install Git (Mercurial) hook.
              --async               Enable async mode. Usefull for checking a lot of
                                    files. Dont supported with pylint.
              --options OPTIONS, -o OPTIONS
                                    Select configuration file. By default is
                                    '<CURDIR>/pylama.ini'
              --force, -F           Force code checking (if linter doesnt allow)
              --abspath, -a         Use absolute paths in output.
        
        
        .. _modeline:
        
        File modelines
        --------------
        
        You can set options for **Pylama** inside a source files. Use
        pylama *modeline* for this.
        
        Format: ::
        
            # pylama:{name1}={value1}:{name2}={value2}:...
        
        
        ::
        
             .. Somethere in code
             # pylama:ignore=W:select=W301
        
        
        Disable code checking for current file: ::
        
             .. Somethere in code
             # pylama:skip=1
        
        The options have a must higher priority.
        
        .. _skiplines:
        
        Skip lines (noqa)
        -----------------
        
        Just add `# noqa` in end of line for ignore.
        
        ::
        
            def urgent_fuction():
                unused_var = 'No errors here' # noqa
        
        
        .. _config:
        
        Configuration files
        -------------------
        
        When starting **Pylama** try loading configuration file.
        
        The programm searches for the first matching ini-style configuration file in
        the directories of command line argument. Pylama looks for the configuration
        in this order: ::
        
            pylama.ini
            setup.cfg
            tox.ini
            pytest.ini
        
        You could set configuration file manually by "-o" option.
        
        Pylama search sections with name starts `pylama`.
        
        Section `pylama` contains a global options, like `linters` and `skip`.
        
        ::
        
            [pylama]
            format = pylint
            skip = */.tox/*,*/.env/*
            linters = pylint,mccabe
            ignore = F0401,C0111,E731
        
        Set Code-checkers' options
        --------------------------
        
        You could set options for special code checker with pylama configurations.
        
        ::
        
            [pylama:pyflakes]
            builtins = _
        
            [pylama:pycodestyle]
            max_line_length = 100
        
            [pylama:pylint]
            max_line_length = 100
            disable = R
        
        See code checkers documentation for more info.
        
        
        Set options for file (group of files)
        -------------------------------------
        
        You could set options for special file (group of files)
        with sections:
        
        The options have a higher priority than in the `pylama` section.
        
        ::
        
            [pylama:*/pylama/main.py]
            ignore = C901,R0914,W0212
            select = R
        
            [pylama:*/tests.py]
            ignore = C0110
        
            [pylama:*/setup.py]
            skip = 1
        
        
        Pytest integration
        ==================
        
        Pylama have Pytest_ support. The package automatically register self as pytest
        plugin when during installation. Also pylama suports `pytest_cache` plugin.
        
        Check files with pylama ::
        
            pytest --pylama ...
        
        Recomended way to settings pylama options when using pytest — configuration
        files (see below).
        
        
        Writing a linter
        ================
        
        You can write a custom extension for Pylama.
        Custom linter should be a python module. Name should be like 'pylama_<name>'.
        
        In 'setup.py' should be defined 'pylama.linter' entry point. ::
        
            setup(
                # ...
                entry_points={
                    'pylama.linter': ['lintername = pylama_lintername.main:Linter'],
                }
                # ...
            )
        
        'Linter' should be instance of 'pylama.lint.Linter' class.
        Must implemented two methods:
        
        'allow' take a path and returned true if linter could check this file for errors.
        'run' take a path and meta keywords params and return list of errors.
        
        Example:
        --------
        
        Just virtual 'WOW' checker.
        
        setup.py: ::
        
            setup(
                name='pylama_wow',
                install_requires=[ 'setuptools' ],
                entry_points={
                    'pylama.linter': ['wow = pylama_wow.main:Linter'],
                }
                # ...
            )
        
        pylama_wow.py: ::
        
            from pylama.lint import Linter as BaseLinter
        
            class Linter(BaseLinter):
        
                def allow(self, path):
                    return 'wow' in path
        
                def run(self, path, **meta):
                    with open(path) as f:
                        if 'wow' in f.read():
                            return [{
                                lnum: 0,
                                col: 0,
                                text: 'Wow has been finded.',
                                type: 'WOW'
                            }]
        
        
        Run pylama from python code
        ---------------------------
        ::
        
            from pylama.main import check_path, parse_options
        
            my_redefined_options = {...}
            my_path = '...'
            options = parse_options([my_path], **my_redefined_options)
            errors = check_path(options)
        
        
        .. _bagtracker:
        
        Bug tracker
        -----------
        
        If you have any suggestions, bug reports or annoyances please report them to the issue tracker at https://github.com/klen/pylama/issues
        
        
        .. _contributing:
        
        Contributing
        ------------
        
        Development of adrest happens at GitHub: https://github.com/klen/pylama
        
        
        .. _contributors:
        
        Contributors
        ^^^^^^^^^^^^
        
        See AUTHORS_.
        
        
        .. _license:
        
        License
        -------
        
        Licensed under a `BSD license`_.
        
        
        .. _links:
        
        .. _AUTHORS: https://github.com/klen/pylama/blob/develop/AUTHORS
        .. _BSD license: http://www.linfo.org/bsdlicense.html
        .. _Mccabe: http://nedbatchelder.com/blog/200803/python_code_complexity_microtool.html
        .. _pydocstyle: https://github.com/PyCQA/pydocstyle/
        .. _pycodestyle: https://github.com/PyCQA/pycodestyle
        .. _PyFlakes: https://github.com/pyflakes/pyflakes
        .. _Pylint: http://pylint.org
        .. _Pytest: http://pytest.org
        .. _gjslint: https://developers.google.com/closure/utilities
        .. _klen: http://klen.github.io/
        .. _Radon: https://github.com/rubik/radon
        .. |logo| image:: https://raw.github.com/klen/pylama/develop/docs/_static/logo.png
                          :width: 100
        
Keywords: pylint,pep8,pycodestyle,pyflakes,mccabe,linter,qa,pep257,pydocstyle
Platform: Any
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Classifier: Topic :: Software Development :: Quality Assurance
Classifier: Development Status :: 4 - Beta
Classifier: Environment :: Console
Classifier: Intended Audience :: Developers
Classifier: Intended Audience :: System Administrators
Classifier: License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)
Classifier: Natural Language :: English
Classifier: Natural Language :: Russian
Classifier: Programming Language :: Python :: 2
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python
Classifier: Topic :: Software Development :: Code Generators
