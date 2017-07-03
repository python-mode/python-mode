PYMODE = $(CURDIR)/pymode
LIBS = $(PYMODE)/libs
PYLAMA = $(LIBS)/pylama

.PHONY: clean
clean:
	find $(CURDIR) -name "*.pyc" -delete
	rm -rf $(CURDIR)/build
	rm -rf *.deb

VERSION?=minor
# target: release - Bump version
release:
	git fetch origin
	git checkout master
	git rebase
	git merge develop
	bumpversion $(VERSION)
	git checkout develop
	git rebase
	git merge master
	git push origin develop master
	git push --tags

.PHONY: minor
minor: release

.PHONY: patch
patch:
	make release VERSION=patch

.PHONY: major
major:
	make release VERSION=major

# Temporary disable rope tests on Travis
.PHONY: travis
travis:
	rake test

.PHONY: test t
test:
	bundle install
	rm -rf $(CURDIR)/.ropeproject
	rake test
t: test

.PHONY: pylama
pylama:
	rm -rf $(PYLAMA)
	make $(PYLAMA)
	make $(PYLAMA)/lint/pylama_pylint
	@pip install --upgrade --force-reinstall --target=$(LIBS) pydocstyle
	@pip install --upgrade --force-reinstall --target=$(LIBS) pycodestyle
	@pip install --upgrade --force-reinstall --target=$(LIBS) pyflakes
	@pip install --upgrade --force-reinstall --target=$(LIBS) mccabe
	@pip install --upgrade --force-reinstall --target=$(LIBS) pylint
	@find $(LIBS) -name *.dist-info -type d | xargs rm -rf
	@find $(LIBS) -name *.egg-info  -type d | xargs rm -rf
	@find $(LIBS) -name test*  -type d | xargs rm -rf

.PHONY: rope
rope:
	@git clone https://github.com/python-rope/rope.git $(CURDIR)/_/rope
	@rm -rf $(CURDIR)/pymode/libs/rope
	@cp -r $(CURDIR)/_/rope/rope $(CURDIR)/pymode/libs/.

$(PYLAMA):
	cp -r $$PRJDIR/pylama/pylama $(PYLAMA)

$(PYLAMA)/lint/pylama_pylint:
	cp -r $$PRJDIR/pylama/plugins/pylama_pylint/pylama_pylint/ $(PYLAMA)/lint/pylama_pylint

$(CURDIR)/build:
	mkdir -p $(CURDIR)/build/usr/share/vim/addons
	mkdir -p $(CURDIR)/build/usr/share/vim/registry
	cp -r after autoload doc ftplugin plugin pymode syntax $(CURDIR)/build/usr/share/vim/addons/.
	cp -r python-mode.yaml $(CURDIR)/build/usr/share/vim/registry/.

PACKAGE_VERSION?=$(shell git describe --tags `git rev-list master --tags --max-count=1`) 
PACKAGE_NAME="vim-python-mode"
PACKAGE_MAINTAINER="Kirill Klenov <horneds@gmail.com>"
PACKAGE_URL=http://github.com/klen/python-mode
deb: clean $(CURDIR)/build
	@fpm -s dir -t deb -a all \
	    -n $(PACKAGE_NAME) \
	    -v $(PACKAGE_VERSION) \
	    -m $(PACKAGE_MAINTAINER) \
	    --url $(PACKAGE_URL) \
	    --license "GNU lesser general public license" \
	    --description "Vim-Swissknife for python" \
	    --deb-user root \
	    --deb-group root \
	    -C $(CURDIR)/build \
	    -d "python2.7" \
	    -d "vim-addon-manager" \
	    usr
	@mv *.deb ~/Dropbox/projects/deb/load
