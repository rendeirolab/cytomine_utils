

clean_build:
	-rm -r build
	-rm -r *.egg-info

clean_docs:
	-rm -r docs/source/_autosummary
	-rm -r docs/build
	-rm -r ~/docs/

clean: clean_docs

install:
	pip install .

html: clean_docs
	mkdir -p docs/build/html
	sphinx-build -b html docs/source/ docs/build/html
	cp -r docs/build ~/docs/

docs: html
