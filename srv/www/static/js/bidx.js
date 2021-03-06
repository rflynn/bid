
var bidx = {

    init: function(opts)
    {
        return true;
    },

    bid_url: function(price, gtin, site)
    {
        // NOTE: browsers limit concurrent connections by domain, so consider implementing subdomains
        // a better alternative is to batch all bids into a single request!
        var ts = +Date.now();
        return (
            'http://bidx.co/bid/'
                + '?gtin='  + encodeURIComponent(gtin)
                + '&price=' + encodeURIComponent(price)
                + '&site='  + encodeURIComponent(site)
                + '&t='     + encodeURIComponent(ts)
        );
    },

    on_bid_response: function(span, msg)
    {
        if (msg.hasOwnProperty('id') && msg.id) {
            var price = msg.price;
            var vendor = msg.id;
            var link = 'http://www.' + vendor + '/';
            console.log(span, price, msg, link);
            $('span#'+span+' span.price').text('$'+Math.round(price));
            $('span#'+span+' span.site a').attr('href', link);
            $('span#'+span+' span.site a').text(vendor);
        }
    },

    bid: function(span)
    {
        var price = $('span#'+span+' span.price').text().substr(1);
        var gtin  = $('span#'+span+'').attr('gtin') || 'unknown';
        var site  = $('span#'+span+' span.site > a').attr('href') || 'unknown';
        var jqxhr = $.ajax({
            url: bidx.bid_url(price, gtin, site),
            dataType: 'json',
            timeout: 3000
        })
        .done(function(msg) { bidx.on_bid_response(span, msg); })
        .fail(function() { console.log("error"); })
        .always(function() { $('span#'+span+' > .biddable').show('slow'); });
    },

    run: function()
    {
        var biddable = document.getElementsByClassName('bidx');
        for (var i = 0; i < biddable.length; i++) {
            var span = biddable[i].attributes["id"].value;
            console.log(span);
            //$('span#'+span+' > .biddable').hide() // TODO: remove dependence on jQuery
            bidx.bid(span)
            /*
            setTimeout(function(span) {
                return function() {
                    bidx.bid(span)
                }
            }(span), 0*i);
            */
        }
    }
};

