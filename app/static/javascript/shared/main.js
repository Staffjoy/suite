$(document).ready(function(){
    App.Util.setupICH();

    console.log(App);

    Array.prototype.firstNonZeroIndex = function() {
        for (var i = 0; i < this.length; i++) {
            if (this[i] > 0) {
                return i;
            }
        }
    }

    Array.prototype.lastNonZeroIndex = function() {
        for (var i = this.length - 1; i >= 0; i--) {
            if (this[i] > 0) {
                return i;
            }
        }
    }

    Array.prototype.getIndexBy = function(object, value) {
        for (var i = 0; i < this.length; i++) {
            if (this[i][object] == value) {
                return i;
            }
        }

        return -1;
    };

    Backbone.Collection.prototype.getIndexBy = function(object, value) {
        for (var i = 0; i < this.models.length; i++) {
            if (this.models[i].get(object) === value) {
                return i;
            }
        }

        return -1;
    };

    Backbone.View.prototype.addDelegateView = function(key, view, opts) {
        this.delegateViews[key] = view;
        this.delegateViews[key].render(opts);
    };

    Backbone.View.prototype.removeAllDelegateViews = function() {
        _.each(this.delegateViews, function(delegateView, key, list) {
            delegateView.close(delegateView);
        });
        this.delegateViews = {};
    };

    Backbone.View.prototype.close = function(delegateView) {

        delegateView = delegateView || this;

        _.each(delegateView.delegateViews, function(delegateView, key, list) {
            delegateView.close(delegateView);
        });

        $(delegateView.el).empty();
        delegateView.unbind();
        delegateView.undelegateEvents();
    };

    String.prototype.capitalizeFirstLetter = function() {
        return this.charAt(0).toUpperCase() + this.slice(1);
    }

    appView = function AppView(navViews) {
        this.navViews = navViews || [];

        this.showView = function(view, opts) {

            if (this.currentView) {
                this.currentView.close();
            }

            this.currentView = view;
            this.currentView.render(opts);

            _.each(this.navViews, function(navView) {
                navView.setCurrentView(view);
            });
        };


        this.registerView = function(view) {
            this.navViews.push(view);
        };
    };

    App.appView = new appView();

    router = new App.Router({appView: App.appView});
    Backbone.history.start();

    setTimeout(function() {
        document.location.reload(true);
    }, 21600000);

    var headerCollapse = _.throttle(function(event) {
        var body = document.body,
            $body = $(body),
            scrollHeight = body.scrollHeight,
            height = $body.height(),
            $header,
            $headerContent,
            $navbar,
            headerHeight,
            scrollTop,
            collapseHeader
        ;

        // no scrollbar
        if (scrollHeight <= height) {
            return
        }

        $headerContent = $('#main-header-content');

        // #main-header-content is empty
        if (!$.trim($headerContent.html())) {
            return;
        }

        $header = $('#main-header');
        headerHeight = $header.hasClass('mini-navbar') ? window.headerHeight : $header.height();
        scrollTop = $body.scrollTop();
        collapseHeader = scrollTop > headerHeight;
        $navbar = $('#main-header-nav');

        if (collapseHeader) {
            window.headerHeight = headerHeight;
            $header.addClass('mini-navbar');
        } else {
            $header.removeClass('mini-navbar');
        }
    }, 100);

    window.addEventListener('scroll', headerCollapse);
});
