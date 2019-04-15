"""Integration with Rope library."""

from __future__ import absolute_import, print_function

import os.path
import re
import site
import sys

from rope.base import project, libutils, exceptions, change, worder, pycore
from rope.base.fscommands import FileSystemCommands # noqa
from rope.base.taskhandle import TaskHandle # noqa
from rope.contrib import autoimport as rope_autoimport, codeassist, findit, generate # noqa
from rope.refactor import ModuleToPackage, ImportOrganizer, rename, extract, inline, usefunction, move, change_signature, importutils # noqa

from .environment import env


def look_ropeproject(path):
    """Search for ropeproject in current and parent dirs.

    :return str|None: A finded path

    """
    env.debug('Look project', path)
    p = os.path.abspath(path)

    while True:
        if '.ropeproject' in os.listdir(p):
            return p

        new_p = os.path.abspath(os.path.join(p, ".."))
        if new_p == p:
            return path

        p = new_p


@env.catch_exceptions
def completions():
    """ Search completions.

    :return None:

    """
    row, col = env.cursor
    if env.var('a:findstart', True):
        count = 0
        for char in reversed(env.current.line[:col]):
            if not re.match(r'[\w\d]', char):
                break
            count += 1
        env.debug('Complete find start', (col - count))
        return env.stop(col - count)

    base = env.var('a:base')
    source, offset = env.get_offset_params((row, col), base)
    proposals = get_proporsals(source, offset, base)
    return env.stop(proposals)


FROM_RE = re.compile(r'^\s*from\s+[\.\w\d_]+$')


@env.catch_exceptions
def complete(dot=False):
    """ Ctrl+Space completion.

    :return bool: success

    """
    row, col = env.cursor
    source, offset = env.get_offset_params()

    cline = env.current.line[:col]
    env.debug('dot completion', cline)
    if FROM_RE.match(cline) or cline.endswith('..') or cline.endswith('\.'):  # noqa
        return env.stop("")

    proposals = get_proporsals(source, offset, dot=dot)
    if not proposals:
        return False

    prefix = proposals[0]['word']

    # Find common part
    for p in proposals:
        common = len([
            c1 for c1, c2 in zip(prefix, p['word']) if c1 == c2 and c1 != ' '
        ])
        prefix = prefix[:common]
    s_offset = codeassist.starting_offset(source, offset)
    p_prefix = prefix[offset - s_offset:]
    line = env.lines[row - 1]
    cline = line[:col] + p_prefix + line[col:]
    if cline != line:
        if 'noinsert' not in env.var('&completeopt'):
            env.curbuf[row - 1] = env.prepare_value(cline, dumps=False)
    env.current.window.cursor = (row, col + len(p_prefix))
    env.run('complete', col - len(prefix) + len(p_prefix) + 1, proposals)
    return True


def get_proporsals(source, offset, base='', dot=False):
    """ Code assist.

    :return str:

    """
    with RopeContext() as ctx:  # noqa

        try:
            proposals = codeassist.code_assist(
                ctx.project, source, offset, ctx.resource, maxfixes=3,
                later_locals=False)

        except exceptions.ModuleSyntaxError:
            proposals = []

        proposals = sorted(proposals, key=_sort_proporsals)

        out = []
        preview = 'preview' in ctx.options.get('completeopt')
        for p in proposals:
            out.append(dict(
                word=p.name,
                menu=p.type,
                kind=p.scope + ':',
                info=p.get_doc() or "No docs." if preview else "",
            ))

        out = _get_autoimport_proposals(out, ctx, source, offset, dot=dot)

    return out


@env.catch_exceptions
def goto():
    """ Goto definition. """
    with RopeContext() as ctx:
        source, offset = env.get_offset_params()

        found_resource, line = codeassist.get_definition_location(
            ctx.project, source, offset, ctx.resource, maxfixes=3)

        if not found_resource:
            env.error('Definition not found')
            return

        env.goto_file(
            found_resource.real_path,
            cmd=ctx.options.get('goto_definition_cmd'))
        env.goto_line(line)


@env.catch_exceptions
def show_doc():
    """ Show documentation. """
    with RopeContext() as ctx:
        source, offset = env.get_offset_params()
        try:
            doc = codeassist.get_doc(
                ctx.project, source, offset, ctx.resource, maxfixes=3)
            if not doc:
                raise exceptions.BadIdentifierError
            env.let('l:output', doc.split('\n'))
        except exceptions.BadIdentifierError:
            env.error("No documentation found.")


def find_it():
    """ Find occurrences. """
    with RopeContext() as ctx:
        _, offset = env.get_offset_params()
        try:
            occurrences = findit.find_occurrences(
                ctx.project, ctx.resource, offset)
        except exceptions.BadIdentifierError:
            occurrences = []

    lst = []
    for oc in occurrences:
        lst.append(dict(
            filename=oc.resource.path,
            text=env.lines[oc.lineno - 1] if oc.resource.real_path == env.curbuf.name else "", # noqa
            lnum=oc.lineno,
            type=''
        ))
    env.run('g:PymodeLocList.current().extend', lst)


def update_python_path(paths):
    """ Update sys.path and make sure the new items come first. """
    old_sys_path_items = list(sys.path)

    for path in paths:
        # see if it is a site dir
        if path.find('site-packages') != -1:
            site.addsitedir(path)

        else:
            sys.path.insert(0, path)

    # Reorder sys.path so new directories at the front.
    new_sys_path_items = set(sys.path) - set(old_sys_path_items)
    sys.path = list(new_sys_path_items) + old_sys_path_items


def organize_imports():
    """ Organize imports in current file. """
    with RopeContext() as ctx:
        organizer = ImportOrganizer(ctx.project)
        changes = organizer.organize_imports(ctx.resource)
        if changes is not None:
            progress = ProgressHandler('Organize imports')
            ctx.project.do(changes, task_handle=progress.handle)
            reload_changes(changes)


@env.catch_exceptions
def regenerate():
    """ Clear cache. """
    with RopeContext() as ctx:
        ctx.project.pycore._invalidate_resource_cache(ctx.resource) # noqa
        ctx.importer.generate_cache()
        ctx.project.sync()


def new():
    """ Create a new project. """
    root = None
    if env.var('a:0') != '0':
        root = env.var('a:1')
    else:
        default = env.var('g:pymode_rope_project_root')
        if not default:
            default = env.var('getcwd()')
        if sys.platform.startswith('win32'):
            default = default.replace('\\', '/')
        root = env.var('input("Enter project root: ", "%s")' % default)
    ropefolder = env.var('g:pymode_rope_ropefolder')
    prj = project.Project(projectroot=root, ropefolder=ropefolder)
    prj.close()
    env.message("Project is opened: %s" % root)


def undo():
    """ Undo last changes.

    :return bool:

    """
    with RopeContext() as ctx:
        changes = ctx.project.history.tobe_undone
        if changes is None:
            env.error('Nothing to undo!')
            return False

        if env.user_confirm('Undo [%s]?' % str(changes)):
            progress = ProgressHandler('Undo %s' % str(changes))
            for c in ctx.project.history.undo(task_handle=progress.handle):
                reload_changes(c)


def redo():
    """ Redo last changes.

    :return bool:

    """
    with RopeContext() as ctx:
        changes = ctx.project.history.tobe_redone
        if changes is None:
            env.error('Nothing to redo!')
            return False

        if env.user_confirm('Redo [%s]?' % str(changes)):
            progress = ProgressHandler('Redo %s' % str(changes))
            for c in ctx.project.history.redo(task_handle=progress.handle):
                reload_changes(c)


def cache_project(cls):
    """ Cache projects.

    :return func:

    """
    projects = dict()
    resources = dict()

    def get_ctx(*args, **kwargs):
        path = env.curbuf.name
        if resources.get(path):
            return resources.get(path)

        project_path = env.var('g:pymode_rope_project_root')
        if not project_path:
            project_path = env.curdir
            env.debug('Look ctx', project_path)
            if env.var('g:pymode_rope_lookup_project', True):
                project_path = look_ropeproject(project_path)

        if not os.path.exists(project_path):
            env.error("Rope project root not exist: %s" % project_path)
            ctx = None

        else:
            ctx = projects.get(project_path)

        if not ctx:
            projects[project_path] = ctx = cls(path, project_path)

        resources[path] = ctx
        return ctx
    return get_ctx


def autoimport():
    """ Autoimport modules.

    :return bool:

    """
    word = env.var('a:word')
    if not word:
        env.error("Should be word under cursor.")
        return False

    with RopeContext() as ctx:
        if not ctx.importer.names:
            ctx.generate_autoimport_cache()
        modules = ctx.importer.get_modules(word)
        if not modules:
            env.message('Global name %s not found.' % word)
            return False

        if len(modules) == 1:
            _insert_import(word, modules[0], ctx)

        else:
            module = env.user_input_choices(
                'Which module to import:', *modules)
            _insert_import(word, module, ctx)

        return True


@cache_project
class RopeContext(object):

    """ A context manager to have a rope project context. """

    projects = {}
    resource = {}

    def __init__(self, path=None, project_path=None):
        """ Init Rope context. """
        self.path = path

        self.project = project.Project(project_path, fscommands=FileSystemCommands())

        self.importer = rope_autoimport.AutoImport(
            project=self.project, observe=False)

        update_python_path(self.project.prefs.get('python_path', []))

        self.resource = None
        self.current = None
        self.options = dict(
            completeopt=env.var('&completeopt'),
            autoimport=env.var('g:pymode_rope_autoimport', True),
            autoimport_modules=env.var('g:pymode_rope_autoimport_modules'),
            goto_definition_cmd=env.var('g:pymode_rope_goto_definition_cmd'),
        )

        if os.path.exists("%s/__init__.py" % project_path):
            sys.path.append(project_path)

        if self.options.get('autoimport'):
            self.generate_autoimport_cache()

        env.debug('Context init', project_path)
        env.message('Init Rope project: %s' % project_path)

    def __enter__(self):
        """ Enter to Rope ctx. """
        env.let('g:pymode_rope_current', self.project.root.real_path)
        self.project.validate(self.project.root)
        self.resource = libutils.path_to_resource(
            self.project, env.curbuf.name, 'file')

        if not self.resource.exists() or os.path.isdir(
                self.resource.real_path):
            self.resource = None
        else:
            env.debug('Found resource', self.resource.path)

        return self

    def __exit__(self, t, value, traceback):
        """ Exit from Rope ctx. """
        if t is None:
            self.project.close()

    def generate_autoimport_cache(self):
        """ Update autoimport cache. """
        env.message('Regenerate autoimport cache.')
        modules = self.options.get('autoimport_modules', [])

        def _update_cache(importer, modules=None):
            importer.generate_cache()
            if modules:
                importer.generate_modules_cache(modules)
            importer.project.sync()

        _update_cache(self.importer, modules)


class ProgressHandler(object):

    """ Handle task progress. """

    def __init__(self, msg):
        """ Init progress handler. """
        self.handle = TaskHandle(name="refactoring_handle")
        self.handle.add_observer(self)
        self.message = msg

    def __call__(self):
        """ Show current progress. """
        percent_done = self.handle.current_jobset().get_percent_done()
        env.message('%s - done %s%%' % (self.message, percent_done))


_scope_weight = {
    'local': 10, 'attribute': 20, 'global': 30, 'imported': 40, 'builtin': 50}


def _sort_proporsals(p):
    return (
        _scope_weight.get(p.scope, 100), int(p.name.startswith('_')), p.name)


class Refactoring(object): # noqa

    """ Base class for refactor operations. """

    def run(self):
        """ Run refactoring.

        :return bool:

        """
        with RopeContext() as ctx:

            if not ctx.resource:
                env.error("You should save the file before refactoring.")
                return None

            try:
                env.message(self.__doc__)
                refactor = self.get_refactor(ctx)
                input_str = self.get_input_str(refactor, ctx)
                if not input_str:
                    return False

                action = env.user_input_choices(
                    'Choose what to do:', 'perform', 'preview',
                    'perform in class hierarchy',
                    'preview in class hierarchy')

                in_hierarchy = action.endswith("in class hierarchy")

                changes = self.get_changes(refactor, input_str, in_hierarchy)

                if not action:
                    return False

                if action.startswith('preview'):
                    print("\n   ")
                    print("-------------------------------")
                    print("\n%s\n" % changes.get_description())
                    print("-------------------------------\n\n")
                    if not env.user_confirm('Do the changes?'):
                        return False

                progress = ProgressHandler('Apply changes ...')
                ctx.project.do(changes, task_handle=progress.handle)
                reload_changes(changes)
            except exceptions.RefactoringError as e:
                env.error(str(e))

            except Exception as e: # noqa
                env.error('Unhandled exception in Pymode: %s' % e)

    @staticmethod
    def get_refactor(ctx):
        """ Get refactor object. """
        raise NotImplementedError

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Get user input. Skip by default.

        :return bool: True

        """
        return True

    @staticmethod
    def get_changes(refactor, input_str, in_hierarchy=False):
        return refactor.get_changes(input_str)


class RenameRefactoring(Refactoring):

    """ Rename var/function/method/class. """

    def __init__(self, module=False):
        self.module = module
        super(RenameRefactoring, self).__init__()

    def get_refactor(self, ctx):
        """ Function description.

        :return Rename:

        """
        offset = None
        if not self.module:
            _, offset = env.get_offset_params()
        env.debug('Prepare rename', offset)
        return rename.Rename(ctx.project, ctx.resource, offset)

    def get_input_str(self, refactor, ctx):
        """ Return user input. """

        oldname = str(refactor.get_old_name())
        msg = 'Renaming method/variable. New name:'
        if self.module:
            msg = 'Renaming module. New name:'
        newname = env.user_input(msg, oldname)

        if newname == oldname:
            env.message("Nothing to do.")
            return False

        return newname

    @staticmethod
    def get_changes(refactor, input_str, in_hierarchy=False):
        """ Get changes.

        :return Changes:

        """
        return refactor.get_changes(input_str, in_hierarchy=in_hierarchy)


class ExtractMethodRefactoring(Refactoring):

    """ Extract method. """

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Return user input. """

        return env.user_input('New method name:')

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        cursor1, cursor2 = env.curbuf.mark('<'), env.curbuf.mark('>')
        _, offset1 = env.get_offset_params(cursor1)
        _, offset2 = env.get_offset_params(cursor2)
        return extract.ExtractMethod(
            ctx.project, ctx.resource, offset1, offset2 + 1)


class ExtractVariableRefactoring(Refactoring):

    """ Extract variable. """

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Return user input. """

        return env.user_input('New variable name:')

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        cursor1, cursor2 = env.curbuf.mark('<'), env.curbuf.mark('>')
        _, offset1 = env.get_offset_params(cursor1)
        _, offset2 = env.get_offset_params(cursor2)
        return extract.ExtractVariable(
            ctx.project, ctx.resource, offset1, offset2 + 1)


class InlineRefactoring(Refactoring):

    """ Inline variable/method. """

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        _, offset = env.get_offset_params()
        return inline.create_inline(ctx.project, ctx.resource, offset)

    @staticmethod
    def get_changes(refactor, input_str, in_hierarchy=False):
        """ Get changes.

        :return Changes:

        """
        return refactor.get_changes()


class UseFunctionRefactoring(Refactoring):

    """ Use selected function as possible. """

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        _, offset = env.get_offset_params()
        return usefunction.UseFunction(ctx.project, ctx.resource, offset)

    @staticmethod
    def get_changes(refactor, input_str, in_hierarchy=False):
        """ Get changes.

        :return Changes:

        """
        return refactor.get_changes()


class ModuleToPackageRefactoring(Refactoring):

    """ Convert module to package. """

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        return ModuleToPackage(ctx.project, ctx.resource)

    @staticmethod
    def get_changes(refactor, input_str, in_hierarchy=False):
        """ Get changes.

        :return Changes:

        """
        return refactor.get_changes()


class MoveRefactoring(Refactoring):

    """ Move method/module to other class/global. """

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Get destination.

        :return str:

        """

        return env.user_input('Enter destination:')

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        _, offset = env.get_offset_params()
        if offset == 0:
            offset = None
        return move.create_move(ctx.project, ctx.resource, offset)


class ChangeSignatureRefactoring(Refactoring):

    """ Change function signature (add/remove/sort arguments). """

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Get destination.

        :return str:

        """
        args = refactor.get_args()
        default = ', '.join(a[0] for a in args)
        return env.user_input('Change the signature:', default)

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        _, offset = env.get_offset_params()
        return change_signature.ChangeSignature(
            ctx.project, ctx.resource, offset)

    def get_changes(self, refactor, input_string, in_hierarchy=False):
        """ Function description.

        :return Rope.changes:

        """
        args = re.sub(r'[\s\(\)]+', '', input_string).split(',')
        olds = [arg[0] for arg in refactor.get_args()]

        changers = []
        for arg in [a for a in olds if a not in args]:
            changers.append(change_signature.ArgumentRemover(olds.index(arg)))
            olds.remove(arg)

        order = []
        for index, arg in enumerate(args):
            if arg not in olds:
                changers.append(change_signature.ArgumentAdder(index, arg))
                olds.insert(index, arg)
            order.append(olds.index(arg))

        changers.append(change_signature.ArgumentReorderer(
            order, autodef='None'))

        return refactor.get_changes(changers, in_hierarchy=in_hierarchy)


class GenerateElementRefactoring(Refactoring):

    """ Class description. """

    def __init__(self, kind, *args, **kwargs):
        """ Function description. """
        self.kind = kind
        super(GenerateElementRefactoring, self).__init__(*args, **kwargs)

    def get_refactor(self, ctx):
        """ Function description.

        :return Rename:

        """
        _, offset = env.get_offset_params()
        return generate.create_generate(
            self.kind, ctx.project, ctx.resource, offset)

    def get_changes(self, refactor, input_str, in_hierarchy=False):
        """ Function description.

        :return Rope.changes:

        """

        return refactor.get_changes()


@env.catch_exceptions
def reload_changes(changes):
    """ Reload changed buffers. """

    resources = changes.get_changed_resources()
    moved = _get_moved_resources(changes) # noqa
    current = env.curbuf.number

    for f in resources:
        bufnr = env.var('bufnr("%s")' % f.real_path)
        env.goto_buffer(bufnr)

        path = env.curbuf.name
        if f in moved:
            path = moved[f].real_path

        env.debug('Reload', f.real_path, path, bufnr)
        env.goto_file(path, 'e!', force=True)
        env.message("%s has been changed." % f.real_path, history=True)

    env.goto_buffer(current)


def _get_moved_resources(changes):

    moved = dict()

    if isinstance(changes, change.ChangeSet):
        for c in changes.changes:
            moved.update(_get_moved_resources(c))

    if isinstance(changes, change.MoveResource):
        moved[changes.resource] = changes.new_resource

    return moved


def _get_autoimport_proposals(out, ctx, source, offset, dot=False):

    if not ctx.options.get('autoimport') or dot:
        return out

    if '.' in codeassist.starting_expression(source, offset):
        return out

    current_offset = offset - 1
    while current_offset > 0 and (
            source[current_offset].isalnum() or source[current_offset] == '_'):
        current_offset -= 1
    starting = source[current_offset:offset]
    starting = starting.strip()

    if not starting:
        return out

    for assist in ctx.importer.import_assist(starting):
        out.append(dict(
            abbr=' : '.join(assist),
            word=assist[0],
            kind='autoimport:',
        ))

    return out


@env.catch_exceptions
def complete_check():
    """ Function description.

    :return bool:

    """

    row, column = env.cursor
    line = env.lines[row - 1]
    word_finder = worder.Worder(line, True)
    parent, name, _ = word_finder.get_splitted_primary_before(column - 1)
    if parent:
        return False

    with RopeContext() as ctx:
        modules = ctx.importer.get_modules(name)

        if not modules:
            return False

        if name in ctx.project.pycore.resource_to_pyobject(ctx.resource):
            return False

        if not env.user_confirm("Import %s?" % name, True):
            return False

        if len(modules) == 1:
            _insert_import(name, modules[0], ctx)

        else:
            module = env.user_input_choices('With module to import:', *modules)
            if module:
                _insert_import(name, module, ctx)


def _insert_import(name, module, ctx):
    if not ctx.resource:
        source, _ = env.get_offset_params()
        lineno = ctx.importer.find_insertion_line(source)
        line = 'from %s import %s' % (module, name)
        env.curbuf[lineno - 1:lineno - 1] = [
            env.prepare_value(line, dumps=False)]
        return True

    pyobject = ctx.project.pycore.resource_to_pyobject(ctx.resource)
    import_tools = importutils.ImportTools(ctx.project)
    module_imports = import_tools.module_imports(pyobject)
    new_import = importutils.FromImport(module, 0, [[name, None]])
    module_imports.add_import(new_import)
    changes = change.ChangeContents(
        ctx.resource, module_imports.get_changed_source())

    action = env.user_input_choices(
        'Choose what to do:', 'perform', 'preview')

    if not action:
        return False

    if action == 'preview':
        print("\n   ")
        print("-------------------------------")
        print("\n%s\n" % changes.get_description())
        print("-------------------------------\n\n")
        if not env.user_confirm('Do the changes?'):
            return False

    progress = ProgressHandler('Apply changes ...')
    ctx.project.do(changes, task_handle=progress.handle)
    reload_changes(changes)


# Monkey patch Rope
def find_source_folders(self, folder):
    """Look only python files an packages."""
    for resource in folder.get_folders():
        if self._is_package(resource):  # noqa
            return [folder]

    for resource in folder.get_files():
        if resource.name.endswith('.py'):
            return [folder]

    return []

pycore.PyCore._find_source_folders = find_source_folders  # noqa
