# A GNU Makefile to run various tasks - compatibility for us old-timers.

# Note: This makefile include remake-style target comments.
# These comments before the targets start with #:
# remake --tasks to shows the targets and the comments

GIT2CL ?= admin-tools/git2cl
PYTHON ?= python3
RM  ?= rm

.PHONY: \
    check clean dist distclean test rmChangeLog flake8

#: Clean up temporary files
clean:
	find . | grep -E '\.pyc' | xargs rm -rvf;
	find . | grep -E '\.pyo' | xargs rm -rvf;
	$(PYTHON) ./setup.py $@


#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@
	patch ChangeLog < ChangeLog-spell-corrected.diff

#: Remove ChangeLog
rmChangeLog:
	$(RM) ChangeLog || true
