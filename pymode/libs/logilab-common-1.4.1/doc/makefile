all: epydoc

epydoc:
	mkdir -p apidoc
	-epydoc --parse-only -o apidoc --html -v --no-private --exclude='test' --exclude="__pkginfo__" --exclude="setup" -n "Logilab's common library" $(shell dirname $(CURDIR))/build/lib/logilab/common >/dev/null

clean:
	rm -rf apidoc
