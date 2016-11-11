all: index.html guide.html

guide.html: guide.text LICENSE.md texopic2html.py Makefile
	python texopic2html.py $< > $@

%.html: %.text
	python texopic2html.py $< > $@
