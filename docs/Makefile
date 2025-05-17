.PHONY: all html latex pdf clean

all: html

html:
	doxygen Doxyfile

latex:
	doxygen Doxyfile
	cd latex && make

pdf: latex
	cd latex && make pdf

clean:
	rm -rf html latex

website-docs:
	cd website && npm run build
	cp -r website/dist/assets docs/html/
	cp website/dist/index.html docs/html/website.html