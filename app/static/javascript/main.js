/*
 * Javascript we want everywhere
*/
$( document ).ready(function() {
    FastClick.attach(document.body);

    var $sideslider = $('[data-toggle=collapse-side]');
    var $sel = $($sideslider.attr('data-target'));
    var $body = $(document.body);

    $sideslider.click(function(event){

        $sel.toggleClass('in');
        $body.toggleClass('modal-open');
        $body.append('<div class="slider-open modal-backdrop fade in"></div>');
        $('#main-header').append('<div class="slider-open modal-backdrop fade in"></div>');
        var $backdrop = $('.modal-backdrop');
        var $elements = $('.nav-button, .modal-backdrop');
        var $locationSelect = $('.header-location-select').select2();
        var collapse = function(event) {
            $locationSelect.off('select2:select', collapse);
            $elements.off();
            $backdrop.remove();
            $body.toggleClass('modal-open');
            $sel.toggleClass('in');
            $('#intercom-container').hide();
        };
        $locationSelect.on('select2:select', collapse);
        $('#intercom-container').show();
        $elements.click(collapse);
    });
});
