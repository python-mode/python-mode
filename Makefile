PYMODE = $(CURDIR)/pymode
LIBS = $(PYMODE)/libs
PYLAMA = $(LIBS)/pylama

.PHONY: clean
clean:
	find $(CURDIR) -name "*.pyc" -delete
	rm -rf $(CURDIR)/build
	rm -rf *.deb

# Temporary disable rope tests on Travis
.PHONY: travis
travis:
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

$(CURDIR)/build:
	mkdir -p $(CURDIR)/build/usr/share/vim/addons
	mkdir -p $(CURDIR)/build/usr/share/vim/registry
	cp -r after autoload doc ftplugin plugin pymode syntax $(CURDIR)/build/usr/share/vim/addons/.
	cp -r python-mode.yaml $(CURDIR)/build/usr/share/vim/registry/.

TARGET?=$(CURDIR)/deb
PACKAGE_VERSION?=$(shell git describe --tags `git rev-list master --tags --max-count=1`) 
PACKAGE_NAME="vim-python-mode"
PACKAGE_MAINTAINER="Kirill Klenov <horneds@gmail.com>"
PACKAGE_URL=http://github.com/klen/python-mode
deb: clean $(CURDIR)/build
	@git co gh-pages
	@rm -rf deb
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
	@mkdir -p $(TARGET)
	@prm --type deb --path $(TARGET) \
	    --release precise,quantal,raring,saucy \
	    --arch amd64,i386,all \
	    --component main \
	    --directory $(CURDIR) \
	    --gpg horneds@gmail.com
