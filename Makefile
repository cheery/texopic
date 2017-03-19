all: index.html guide.html

# This is for updating the page. You shouldn't have to do it.
# http://lea.verou.me/2011/10/easily-keep-gh-pages-in-sync-with-master/
sync:
	git checkout gh-pages
	git rebase master
	git push origin gh-pages
	git checkout master

guide.html: guide.text LICENSE.md texopic2html.py

%.html: %.text
	python texopic2html.py $< > $@
