.PHONY: clean
clean:
	find . -name "*.pyc" -delete

.PHONY: test
test:
	bundle install
	rake test

.PHONY: pylama
pylama:
	rm -rf pylibs/pylama
	cp -r ~/Dropbox/projects/pylama/pylama pylibs/pylama
	cp -r ~/Dropbox/projects/pylama/plugins/pylama_pylint/pylama_pylint/ pylibs/pylama/lint/pylama_pylint
