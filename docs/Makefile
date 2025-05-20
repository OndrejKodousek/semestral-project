.PHONY: all html latex pdf clean

all: html

html:
	doxygen Doxyfile

clean:
	rm -rf html latex

website-docs:
	cd ../website && npm run build
	cd ../docs
	cp -r ../website/dist/assets docs/html/
	cp ../website/dist/index.html docs/html/website.html