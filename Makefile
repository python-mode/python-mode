PYMODE = $(CURDIR)/pymode
LIBS = $(PYMODE)/libs
PYLAMA = $(LIBS)/pylama

.PHONY: clean
clean:
	find . -name "*.pyc" -delete

# Temporary disable rope tests on Travis
.PHONY: travis
travis:
	rm -rf t/rope.vim
	rake test

.PHONY: test
test:
	bundle install
	rm -rf $(CURDIR)/.ropeproject
	rake test

.PHONY: pylama
pylama:
	rm -rf $(PYLAMA)
	make $(PYLAMA)
	make $(PYLAMA)/lint/pylama_pylint

$(PYLAMA):
	cp -r ~/Dropbox/projects/pylama/pylama $(PYLAMA)

$(PYLAMA)/lint/pylama_pylint:
	cp -r ~/Dropbox/projects/pylama/plugins/pylama_pylint/pylama_pylint/ $(PYLAMA)/lint/pylama_pylint
