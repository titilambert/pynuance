WD=$(shell pwd)
# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = PyNuance
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

update_dev_doc:
	rm -rf $(WD)/source/pynuance/
	sphinx-apidoc --implicit-namespaces -M -e -P -H "PyNuance developer documentation" -o $(WD)/source/pynuance ../pynuance
	#for folder in `find ../pynuance -type d |grep  -v __pycache__` ; \
    #do \
	#sphinx-apidoc -M -e -P -H "PyNuance developer documentation" -o $(WD)/source/pynuance $$folder ; \
    #done
