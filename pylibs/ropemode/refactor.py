import re

import rope.base.change
import rope.contrib.generate
import rope.refactor.change_signature
import rope.refactor.extract
import rope.refactor.inline
import rope.refactor.introduce_factory
import rope.refactor.method_object
import rope.refactor.move
import rope.refactor.rename
import rope.refactor.restructure
import rope.refactor.usefunction
from rope.base import taskhandle

from ropemode import dialog, filter as file_filter


class Refactoring(object):
    key = None
    confs = {}
    optionals = {}
    saveall = True

    def __init__(self, interface, env):
        self.interface = interface
        self.env = env

    def show(self, initial_asking=True):
        self.interface._check_project()
        self.interface._save_buffers(only_current=not self.saveall)
        self._create_refactoring()
        action, result = dialog.show_dialog(
            self.interface._askdata, ['perform', 'preview', 'cancel'],
            self._get_confs(), self._get_optionals(),
            initial_asking=initial_asking)
        if action == 'cancel':
            self.env.message('Cancelled!')
            return
        def calculate(handle):
            return self._calculate_changes(result, handle)
        name = 'Calculating %s changes' % self.name
        changes = runtask(self.env, calculate, name=name)
        if action == 'perform':
            self._perform(changes)
        if action == 'preview':
            if changes is not None:
                diffs = changes.get_description()
                if self.env.preview_changes(diffs):
                    self._perform(changes)
                else:
                    self.env.message('Thrown away!')
            else:
                self.env.message('No changes!')

    @property
    def project(self):
        return self.interface.project

    @property
    def resource(self):
        return self.interface._get_resource()

    @property
    def offset(self):
        return self.env.get_offset()

    @property
    def region(self):
        return self.env.get_region()

    @property
    def name(self):
        return refactoring_name(self.__class__)

    def _calculate_changes(self, option_values, task_handle):
        pass

    def _create_refactoring(self):
        pass

    def _done(self):
        pass

    def _perform(self, changes):
        if changes is None:
            self.env.message('No changes!')
            return
        def perform(handle, self=self, changes=changes):
            self.project.do(changes, task_handle=handle)
            self.interface._reload_buffers(changes)
            self._done()
        runtask(self.env, perform, 'Making %s changes' % self.name,
                interrupts=False)
        self.env.message(str(changes.description) + ' finished')

    def _get_confs(self):
        return self.confs

    def _get_optionals(self):
        return self.optionals

    @property
    def resources_option(self):
        return dialog.Data('Files to apply this refactoring on: ',
                           decode=self._decode_resources)

    def _decode_resources(self, value):
        return _resources(self.project, value)


class Rename(Refactoring):
    key = 'r'
    saveall = True

    def _create_refactoring(self):
        self.renamer = rope.refactor.rename.Rename(
            self.project, self.resource, self.offset)

    def _calculate_changes(self, values, task_handle):
        return self.renamer.get_changes(task_handle=task_handle, **values)

    def _get_optionals(self):
        opts = {}
        opts['docs'] = dialog.Boolean('Search comments and docs: ', True)
        if self.renamer.is_method():
            opts['in_hierarchy'] = dialog.Boolean('Rename methods in '
                                                  'class hierarchy: ')
        opts['resources'] = self.resources_option
        opts['unsure'] = dialog.Data('Unsure occurrences: ',
                                     decode=self._decode_unsure,
                                     values=['ignore', 'match'],
                                     default='ignore')
        return opts

    def _get_confs(self):
        oldname = str(self.renamer.get_old_name())
        return {'new_name': dialog.Data('New name: ', default=oldname)}

    def _decode_unsure(self, value):
        unsure = value == 'match'
        return lambda occurrence: unsure


class RenameCurrentModule(Rename):
    key = '1 r'
    offset = None


class Restructure(Refactoring):
    key = 'x'
    confs = {'pattern': dialog.Data('Restructuring pattern: '),
             'goal': dialog.Data('Restructuring goal: ')}

    def _calculate_changes(self, values, task_handle):
        restructuring = rope.refactor.restructure.Restructure(
            self.project, values['pattern'], values['goal'],
            args=values['args'], imports=values['imports'])
        return restructuring.get_changes(resources=values['resources'],
                                         task_handle=task_handle)

    def _get_optionals(self):
        return {
            'args': dialog.Data('Arguments: ', decode=self._decode_args),
            'imports': dialog.Data('Imports: ', decode=self._decode_imports),
            'resources': self.resources_option}

    def _decode_args(self, value):
        if value:
            args = {}
            for raw_check in value.split('\n'):
                if raw_check:
                    key, value = raw_check.split(':', 1)
                    args[key.strip()] = value.strip()
            return args

    def _decode_imports(self, value):
        if value:
            return [line.strip() for line in value.split('\n')]


class UseFunction(Refactoring):
    key = 'u'

    def _create_refactoring(self):
        self.user = rope.refactor.usefunction.UseFunction(
            self.project, self.resource, self.offset)

    def _calculate_changes(self, values, task_handle):
        return self.user.get_changes(task_handle=task_handle, **values)

    def _get_optionals(self):
        return {'resources': self.resources_option}


class Move(Refactoring):
    key = 'v'

    def _create_refactoring(self):
        self.mover = rope.refactor.move.create_move(self.project,
                                                    self.resource,
                                                    self.offset)

    def _calculate_changes(self, values, task_handle):
        destination = values['destination']
        resources = values.get('resources', None)
        if isinstance(self.mover, rope.refactor.move.MoveGlobal):
            return self._move_global(destination, resources, task_handle)
        if isinstance(self.mover, rope.refactor.move.MoveModule):
            return self._move_module(destination, resources, task_handle)
        if isinstance(self.mover, rope.refactor.move.MoveMethod):
            return self._move_method(destination, resources, task_handle)

    def _move_global(self, dest, resources, handle):
        destination = self.project.pycore.find_module(dest)
        return self.mover.get_changes(
            destination, resources=resources, task_handle=handle)

    def _move_method(self, dest, resources, handle):
        return self.mover.get_changes(
            dest, self.mover.get_method_name(),
            resources=resources, task_handle=handle)

    def _move_module(self, dest, resources, handle):
        destination = self.project.pycore.find_module(dest)
        return self.mover.get_changes(
            destination, resources=resources, task_handle=handle)

    def _get_confs(self):
        if isinstance(self.mover, rope.refactor.move.MoveGlobal):
            prompt = 'Destination module: '
        if isinstance(self.mover, rope.refactor.move.MoveModule):
            prompt = 'Destination package: '
        if isinstance(self.mover, rope.refactor.move.MoveMethod):
            prompt = 'Destination attribute: '
        return {'destination': dialog.Data(prompt)}

    def _get_optionals(self):
        return {'resources': self.resources_option}


class MoveCurrentModule(Move):
    key = '1 v'
    offset = None


class ModuleToPackage(Refactoring):
    key = '1 p'
    saveall = False

    def _create_refactoring(self):
        self.packager = rope.refactor.ModuleToPackage(
            self.project, self.resource)

    def _calculate_changes(self, values, task_handle):
        return self.packager.get_changes()


class Inline(Refactoring):
    key = 'i'

    def _create_refactoring(self):
        self.inliner = rope.refactor.inline.create_inline(
            self.project, self.resource, self.offset)

    def _calculate_changes(self, values, task_handle):
        return self.inliner.get_changes(task_handle=task_handle, **values)

    def _get_optionals(self):
        opts = {'resources': self.resources_option}
        if self.inliner.get_kind() == 'parameter':
            opts['in_hierarchy'] = dialog.Boolean(
                'Apply on all matching methods in class hierarchy: ', False)
        else:
            opts['remove'] = dialog.Boolean('Remove the definition: ', True)
            opts['only_current'] = dialog.Boolean('Inline this '
                                                  'occurrence only: ')
        return opts


class _Extract(Refactoring):
    saveall = False
    optionals = {'similar': dialog.Boolean('Extract similar pieces: ', True),
                 'global_': dialog.Boolean('Make global: ')}
    kind = None
    constructor = rope.refactor.extract.ExtractVariable

    def __init__(self, *args):
        super(_Extract, self).__init__(*args)
        self.extractor = None

    def _create_refactoring(self):
        start, end = self.region
        self.extractor = self.constructor(self.project,
                                          self.resource, start, end)

    def _calculate_changes(self, values, task_handle):
        similar = values.get('similar')
        global_ = values.get('global_')
        return self.extractor.get_changes(values['name'], similar=similar,
                                          global_=global_)

    def _get_confs(self):
        return {'name': dialog.Data('Extracted %s name: ' % self.kind)}


class ExtractVariable(_Extract):
    key = 'l'
    kind = 'variable'
    constructor = rope.refactor.extract.ExtractVariable


class ExtractMethod(_Extract):
    key = 'm'
    kind = 'method'
    constructor = rope.refactor.extract.ExtractMethod


class OrganizeImports(Refactoring):
    key = 'o'
    saveall = False

    def _create_refactoring(self):
        self.organizer = rope.refactor.ImportOrganizer(self.project)

    def _calculate_changes(self, values, task_handle):
        return self.organizer.organize_imports(self.resource)


class MethodObject(Refactoring):
    saveall = False
    confs = {'classname': dialog.Data('New class name: ',
                                      default='_ExtractedClass')}

    def _create_refactoring(self):
        self.objecter = rope.refactor.method_object.MethodObject(
            self.project, self.resource, self.offset)

    def _calculate_changes(self, values, task_handle):
        classname = values.get('classname')
        return self.objecter.get_changes(classname)


class IntroduceFactory(Refactoring):
    saveall = True
    key = 'f'

    def _create_refactoring(self):
        self.factory = rope.refactor.introduce_factory.IntroduceFactory(
            self.project, self.resource, self.offset)

    def _calculate_changes(self, values, task_handle):
        return self.factory.get_changes(task_handle=task_handle, **values)

    def _get_confs(self):
        default = 'create_%s' % self.factory.old_name.lower()
        return {'factory_name': dialog.Data('Factory name: ', default)}

    def _get_optionals(self):
        return {'global_factory': dialog.Boolean('Make global: ', True),
                'resources': self.resources_option}


class ChangeSignature(Refactoring):
    saveall = True
    key = 's'

    def _create_refactoring(self):
        self.changer = rope.refactor.change_signature.ChangeSignature(
            self.project, self.resource, self.offset)

    def _calculate_changes(self, values, task_handle):
        signature = values.get('signature')
        args = re.sub(r'[\s\(\)]+', '', signature).split(',')
        olds = [arg[0] for arg in self._get_args()]

        changers = []
        for arg in list(olds):
            if arg in args:
                continue
            changers.append(rope.refactor.change_signature.
                            ArgumentRemover(olds.index(arg)))
            olds.remove(arg)

        order = []
        for index, arg in enumerate(args):
            if arg not in olds:
                changers.append(rope.refactor.change_signature.
                                ArgumentAdder(index, arg))
                olds.insert(index, arg)
            order.append(olds.index(arg))
        changers.append(rope.refactor.change_signature.
                        ArgumentReorderer(order, autodef='None'))

        del values['signature']
        return self.changer.get_changes(changers, task_handle=task_handle,
                                        **values)

    def _get_args(self):
        if hasattr(self.changer, 'get_args'):
            return self.changer.get_args()
        return self.changer.get_definition_info().args_with_defaults

    def _get_confs(self):
        args = []
        for arg, default in self._get_args():
            args.append(arg)
        signature = '(' + ', '.join(args) + ')'
        return {'signature': dialog.Data('Change the signature: ',
                                         default=signature)}

    def _get_optionals(self):
        opts = {'resources': self.resources_option}
        if self.changer.is_method():
            opts['in_hierarchy'] = dialog.Boolean('Rename methods in '
                                                  'class hierarchy: ')
        return opts


class _GenerateElement(Refactoring):

    def _create_refactoring(self):
        kind = self.name.split('_')[-1]
        self.generator = rope.contrib.generate.create_generate(
            kind, self.project, self.resource, self.offset)

    def _calculate_changes(self, values, task_handle):
        return self.generator.get_changes()

    def _done(self):
        resource, lineno = self.generator.get_location()
        self.interface._goto_location(resource, lineno)


class GenerateVariable(_GenerateElement):
    key = 'n v'


class GenerateFunction(_GenerateElement):
    key = 'n f'


class GenerateClass(_GenerateElement):
    key = 'n c'


class GenerateModule(_GenerateElement):
    key = 'n m'


class GeneratePackage(_GenerateElement):
    key = 'n p'


def refactoring_name(refactoring):
    classname = refactoring.__name__
    result = []
    for c in classname:
        if result and c.isupper():
            result.append('_')
        result.append(c.lower())
    name = ''.join(result)
    return name

def _resources(project, text):
    if text is None or text.strip() == '':
        return None
    return file_filter.resources(project, text)


def runtask(env, command, name, interrupts=True):
    return RunTask(env, command, name, interrupts)()

class RunTask(object):

    def __init__(self, env, task, name, interrupts=True):
        self.env = env
        self.task = task
        self.name = name
        self.interrupts = interrupts

    def __call__(self):
        handle = taskhandle.TaskHandle(name=self.name)
        progress = self.env.create_progress(self.name)
        def update_progress():
            jobset = handle.current_jobset()
            if jobset:
                percent = jobset.get_percent_done()
                if percent is not None:
                    progress.update(percent)
        handle.add_observer(update_progress)
        result = self.task(handle)
        progress.done()
        return result
