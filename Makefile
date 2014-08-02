# ex: set ts=8 noet:

doc: .force
	$(MAKE) -C doc

test: .force
	$(MAKE) -C test

.force:
