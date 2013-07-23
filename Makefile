# Copyright (c) 2012, Joyent, Inc. All rights reserved.
#
# Makefile for python-manta
#

TOP := $(shell pwd)
NAME		:= python-manta

ifeq ($(shell uname -s),Darwin)
	# http://superuser.com/questions/61185
	# http://forums.macosxhints.com/archive/index.php/t-43243.html
	# This is an Apple customization to `tar` to avoid creating
	# '._foo' files for extended-attributes for archived files.
	TAR := COPYFILE_DISABLE=true COPY_EXTENDED_ATTRIBUTES_DISABLE=true tar
else
	TAR := tar
endif


#
# Targets
#
.PHONY: all
all:

.PHONY: clean
clean:
	find lib test -name "*.pyc" | xargs rm
	find lib test -name "*.pyo" | xargs rm
	find lib test -name "__pycache__" | xargs rm -rf
	rm -rf dist
	rm -rf manta.egg-info

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

#.PHONY: tag
#tag:
#	git tag -a -m "$(VERSION) release" "$(VERSION)"

.PHONY: cutarelease
cutarelease:
	./tools/cutarelease.py -f manta/version.py
