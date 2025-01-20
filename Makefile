PYTHON ?= python3
PHONY=check clean dist distclean test rmChangeLog flake8
#: Clean up temporary files
clean:
	find . | grep -E '\.pyc' | xargs rm -rvf;
	find . | grep -E '\.pyo' | xargs rm -rvf;
	$(PYTHON) ./setup.py $@


#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@

.PHONY: $(PHONY)
