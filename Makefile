# ex: set ts=8 noet:

doc: .force
	$(MAKE) -C doc

data: .force
	$(MAKE) -C data

test: .force
	$(MAKE) -C test

.force:
