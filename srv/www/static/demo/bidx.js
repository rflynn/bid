
var bidx = {

    init: function()
    {
        return true;
    },

    bid_url: function(price, gtin, site)
    {
        return (
            'http://bidx.co/bid/'
            + '?gtin='  + encodeURIComponent(gtin)
            + '&price=' + encodeURIComponent(price)
            + '&site='  + encodeURIComponent(site)
            + '&t='     + encodeURIComponent(+Date.now())
        );
    },

    on_bid_response: function(span, msg)
    {
        if (msg.hasOwnProperty('id')) {
            var price = msg['price'];
            var vendor = msg['id'];
            var link = 'http://www.' + msg['id'] + '/';
            console.log(span, price, msg, link);
            $('span#'+span+' span.price').text('$'+Math.round(price));
            $('span#'+span+' span.site a').attr('href', link);
            $('span#'+span+' span.site a').text(vendor);
        }
    },

    bid: function(span)
    {
        var price = $('span#'+span+' > span.price').text().substr(1);
        var gtin  = $('span#'+span+'').attr('gtin') || 'unknown';
        var site  = $('span#'+span+' > span.site > a').attr('href') || 'unknown';
        var jqxhr = $.ajax({
            url: bidx.bid_url(price, gtin, site),
            dataType: 'json',
            timeout: 3000
        })
        .done(function(msg) { bidx.on_bid_response(span, msg); })
        .fail(function() { console.log("error"); })
        .always(function() { $('span#'+span).show('slow'); });
    },

    run: function()
    {
        var biddable = document.getElementsByClassName('bidx');
        for (var i = 0; i < biddable.length; i++) {
            var span = biddable[i].attributes["id"].value;
            console.log(span);
            $('span#'+span).hide() // TODO: remove dependence on jQuery
            setTimeout(function(span) {
                return function() {
                    bidx.bid(span)
                }
            }(span), 500*i);
        }
    }
};

