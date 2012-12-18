# Copyright (c) 2012, Joyent, Inc. All rights reserved.
#
# Makefile for python-manta
#

#
# Dirs
#
TOP := $(shell pwd)

#
# Mountain Gorilla-spec'd versioning (MG is a Joyent engineering thing).
#
# Need GNU awk for multi-char arg to "-F".
_AWK := $(shell (which gawk >/dev/null && echo gawk) \
	|| (which nawk >/dev/null && echo nawk) \
	|| echo awk)
VERSION := $(shell grep __version__ lib/manta/version.py  | cut -d'"' -f2)
_GITDESCRIBE := g$(shell git describe --all --long | $(_AWK) -F'-g' '{print $$NF}')
#STAMP := $(VERSION)-$(_GITDESCRIBE)
STAMP := $(VERSION)

#
# Vars, Tools, Files, Flags
#
NAME		:= python-manta
RELEASE_TARBALL	:= $(NAME)-$(STAMP).tgz
TMPDIR          := /var/tmp/$(STAMP)

ifeq ($(shell uname -s),Darwin)
	# http://superuser.com/questions/61185
	# http://forums.macosxhints.com/archive/index.php/t-43243.html
	# This is an Apple customization to `tar` to avoid creating
	# '._foo' files for extended-attributes for archived files.
	TAR := COPYFILE_DISABLE=true COPY_EXTENDED_ATTRIBUTES_DISABLE=true tar
else
	TAR := tar
endif

# TODO: restdown docs
#DOC_FILES	 = index.restdown
#RESTDOWN_EXEC	?= deps/restdown/bin/restdown
#RESTDOWN	?= python $(RESTDOWN_EXEC)
#$(RESTDOWN_EXEC): | deps/restdown/.git


#
# Targets
#
.PHONY: all
all:

.PHONY: clean
clean:
	rm -f python-manta*.tgz
	rm -f README.html

.PHONY: test
test:
	python test/test.py $(TAGS)
.PHONY: test-kvm6
test-kvm6:
	make test MANTA_URL=https://10.2.126.200 MANTA_INSECURE=1 MANTA_USER=trent

.PHONY: testall
testall:
	python test/testall.py


#.PHONY: package
#package: all
#	rm -rf MANIFEST dist
#	python setup.py sdist --no-defaults
#	@echo "Created '$(shell ls dist/manta-*.tar.gz)'."

README.html: README.md tools/README.html.head tools/README.html.foot
	cat tools/README.html.head > README.html
	python $(HOME)/tm/python-markdown2/lib/markdown2.py README.md >> README.html
	cat tools/README.html.foot >> README.html

.PHONY: release
release: README.html all
	@echo "Building $(RELEASE_TARBALL)"
	mkdir -p $(TMPDIR)/python-manta-$(STAMP)
	cp -r \
		$(TOP)/*.txt \
		$(TOP)/*.md \
		$(TOP)/bin \
		$(TOP)/lib \
		$(TOP)/test \
		$(TMPDIR)/python-manta-$(STAMP)
	(cd $(TMPDIR) && $(TAR) -v --exclude-from=$(TOP)/tools/release.exclude \
		-czf $(TOP)/$(RELEASE_TARBALL) python-manta-$(STAMP))
	@rm -rf $(TMPDIR)
	@echo "Created $(RELEASE_TARBALL)"

.PHONY: publish
publish: release
	@echo '#'
	@echo '# Are you sure you want to publish'
	@echo '#      $(RELEASE_TARBALL)'
	@echo '# et al to manta-beta?'
	@echo '#'
	@echo '# Press <Enter> to continue, <Ctrl+C> to cancel.'
	@echo '#'
	@read
	./bin/mantash -u trent.mick -U https://manta-beta.joyentcloud.com \
		put $(RELEASE_TARBALL) /manta/public/sdk/python/
	./bin/mantash -u trent.mick -U https://manta-beta.joyentcloud.com \
		put $(RELEASE_TARBALL) /manta/public/sdk/python/python-manta-latest.tgz
	./bin/mantash -u trent.mick -U https://manta-beta.joyentcloud.com \
		put -t text/plain CHANGES.md /manta/public/sdk/python/
	./bin/mantash -u trent.mick -U https://manta-beta.joyentcloud.com \
		put -t text/plain README.md /manta/public/sdk/python/
	./bin/mantash -u trent.mick -U https://manta-beta.joyentcloud.com \
		put -t text/html README.html /manta/public/sdk/python/
	@echo "See https://manta-beta.joyentcloud.com/manta/public/sdk/python/README.md"

.PHONY: tag
tag:
	git tag -a -m "$(VERSION) release" "$(VERSION)"
