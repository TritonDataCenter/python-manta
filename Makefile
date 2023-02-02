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

# Ensure json.js and package.json have the same version.
.PHONY: versioncheck
versioncheck:
	@echo manta/version.py ver is: $(shell python manta/version.py)
	@echo CHANGES.md ver is: $(shell grep '^## ' CHANGES.md | head -2 | tail -1 | awk '{print $$2}')
	@[[ $(shell python manta/version.py) == $(shell grep '^## ' CHANGES.md | head -2 | tail -1 | awk '{print $$2}') ]]

.PHONY: cutarelease
cutarelease: versioncheck
	[[ -z `git status --short` ]]  # If this fails, the working dir is dirty.
	@which json 2>/dev/null 1>/dev/null && \
	    name=$(shell python ./setup.py --name) && \
	    ver=$(shell python ./setup.py --version) && \
	    publishedInfo="$(shell curl -sS https://pypi.org/pypi/$(shell python setup.py --name)/json | json "releases['$(shell python setup.py --version)']")" && \
	    if [[ -n "$$publishedInfo" ]]; then \
		echo "cutarelease error: https://pypi.org/project/$$name/$$ver/ is already published to pypi"; \
		exit 1; \
	    fi && \
	    echo "** Are you sure you want to tag and publish $$name@$$ver to pypi?" && \
	    echo "** Enter to continue, Ctrl+C to abort." && \
	    read
	ver=$(shell python ./setup.py --version) && \
	    date=$(shell date -u "+%Y-%m-%d") && \
	    git tag -a "$$ver" -m "version $$ver ($$date)" && \
	    git push --tags origin && \
	    COPY_EXTENDED_ATTRIBUTES_DISABLE=1 python setup.py sdist --formats zip upload


# Only have this around to retry package uploads on a tag created by
# 'make cutarelease' because PyPI upload is super-flaky (at least for me).
.PHONY: pypi-upload
pypi-upload:
	COPY_EXTENDED_ATTRIBUTES_DISABLE=1 python setup.py sdist --formats zip upload
