# ex: set ts=8 noet

DOM=bidx.co
WWW=www.$(DOM)

all: .force dns bid

dns:
	eval dig $(DOM) | egrep "^$(DOM).*IN.*A.*" >/dev/null

bid:
	eval which curl
	eval curl -D - "http://$(DOM)/"                   2>/dev/null | head -n 1 | grep '^HTTP/1.1 200'
	eval curl -D - "http://$(DOM)?price=1"            2>/dev/null | head -n 1 | grep '^HTTP/1.1 200'
	eval curl -D - "http://$(DOM)/bid/t?wrong=params" 2>/dev/null | head -n 1 | grep '^HTTP/1.1 400'
	eval curl -D - --insecure "https://$(DOM)/api/v0/merchant-product/gtin/00012345678905" 2>/dev/null | head -n 1 | grep '^HTTP/1.1 200'

.force:
