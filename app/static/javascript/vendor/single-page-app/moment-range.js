(function(moment) {
    var STRINGS = {
        nodiff: '',
        day: 'd',
        hour: 'h',
        minute: 'm',
        second: 's',
        delimiter: ' '
    }, VERBOSE_STRINGS = _.extend({}, STRINGS, {
        day: ' days',
        hour: ' hours',
        minute: ' minutes',
        second: ' seconds',
    });
    moment.fn.preciseDiff = function(d2, includeSeconds, verbose, showDays) {
        return moment.preciseDiff(this, d2, includeSeconds, verbose, showDays);
    };
    moment.preciseDiff = function(d1, d2, includeSeconds, verbose, showDays) {
        var m1 = moment(d1), m2 = moment(d2);
        if (m1.isAfter(m2)) {
            var tmp = m1;
            m1 = m2;
            m2 = tmp;
        }

        var seconds = Math.floor((m2 - m1) / 1000),
            hours = Math.floor(seconds/3600),
            days = Math.floor(hours/24),
            minutes,
            seconds,
            result = [],
            strings = !!verbose ? VERBOSE_STRINGS : STRINGS;
        ;

        seconds = seconds - (hours * 3600);
        minutes = Math.floor(seconds/60);
        seconds = seconds - (minutes * 60);


        if (!!showDays) {
            hours = hours - (days * 24);
            result.push(days + strings.day);
        }

        result.push(hours + strings.hour);
        result.push(minutes + strings.minute);
        if (!!includeSeconds) {
            result.push(seconds + strings.second);
        }

        return result.join(strings.delimiter);
    };
}(moment));
