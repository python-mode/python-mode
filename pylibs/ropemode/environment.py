class Environment(object):

    def ask(self, prompt, default=None, starting=None):
        pass

    def ask_values(self, prompt, values, default=None, starting=None):
        pass

    def ask_directory(self, prompt, default=None, starting=None):
        pass

    def ask_completion(self, prompt, values, starting=None):
        pass

    def message(self, message):
        pass

    def yes_or_no(self, prompt):
        pass

    def y_or_n(self, prompt):
        pass

    def get(self, name, default=None):
        pass

    def get_offset(self):
        pass

    def get_text(self):
        pass

    def get_region(self):
        pass

    def filename(self):
        pass

    def is_modified(self):
        pass

    def goto_line(self, lineno):
        pass

    def insert_line(self, line, lineno):
        pass

    def insert(self, text):
        pass

    def delete(self, start, end):
        pass

    def filenames(self):
        pass

    def save_files(self, filenames):
        pass

    def reload_files(self, filenames, moves={}):
        pass

    def find_file(self, filename, readonly=False, other=False):
        pass

    def create_progress(self, name):
        pass

    def current_word(self):
        pass

    def push_mark(self):
        pass

    def pop_mark(self):
        pass

    def prefix_value(self, prefix):
        pass

    def show_occurrences(self, locations):
        pass

    def show_doc(self, docs, altview=False):
        pass

    def preview_changes(self, diffs):
        pass

    def local_command(self, name, callback, key=None, prefix=False):
        pass

    def global_command(self, name, callback, key=None, prefix=False):
        pass

    def add_hook(self, name, callback, hook):
        pass

    def _completion_text(self, proposal):
        return proposal.name

    def _completion_data(self, proposal):
        return self._completion_text(proposal)

