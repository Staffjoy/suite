(function(root) {

    "use strict";

    var Util = {
        setupICH: function() {
            $.ajaxSetup({
                async: false
            });
            $.getJSON("/" + BLUEPRINT + "/templates.json", function(templates) {
                _.each(templates, function(template, name) {
                    ich.addTemplate(name, template);
                });
            });
            $.ajaxSetup({
                async: true
            });
        },
        getDateForWeekStart: function(momentJSDate, weekStartStr) {
            // given a MomentJS Date Object and a string for week stats on
            // returns the MomentJS Date object for the start of that week

            var weekStartInt = this.convertDayStrToInt(weekStartStr),
                currentDayInt = momentJSDate.day(),
                adjustment
            ;

            if (_.isNaN(weekStartInt) || !_.isNumber(weekStartInt)) {
                console.log("invalid week start string supplied");
                return false;
            }

            adjustment = weekStartInt - currentDayInt;

            // offset 1 week back if we are ahead of ourselves
            // adjustment should always be a negative number
            if (adjustment > 0) {
                adjustment -= 7;
            }

            return momentJSDate.add(adjustment, "days");
        },
        convertDayStrToInt: function(weekStartStr) {
            var lookup = weekStartStr.toLowerCase(),
                lookupDict = {
                    sunday: 0,
                    monday: 1,
                    tuesday: 2,
                    wednesday: 3,
                    thursday: 4,
                    friday: 5,
                    saturday: 6
                }
            ;

            if (_.has(lookupDict, lookup)) {
                return lookupDict[lookup];
            } else {
                return false;
            }
        },
        getOrderedWeekArray: function(startDay) {
            // given a start day e.g. 'monday', return an array
            // of the next 7 weekdays

            var days = [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday"
                ],
                startIndex = days.indexOf(startDay)
            ;

            if (startIndex < 0) {
                return false;
            }

            return [].concat(days.splice(startIndex, days.length), days);
        },
        getAdjustedDemandOffset: function(weekStart, previousOffset, newOffset, previousDemand) {
            weekStart = weekStart.toLowerCase();

            var self = this,
                offsetAmount = previousOffset - newOffset,
                orderedWeek = self.getOrderedWeekArray(weekStart),
                newDemand = {},
                weekLength = previousDemand[weekStart].length,
                today,
                yesterday,
                i
            ;

            // can only do 1 way | e.g. 4 -> 0
            if (offsetAmount < 0) {
                console.log("getAdjustedDemandOffset can only adjust where newOffset is smaller");
                return false;

            } else if (offsetAmount === 0) {
                return previousDemand;

            } else {
                // deliberately don't deal with the starting day at this point
                for (i=1; i < orderedWeek.length - 1; i++) {
                    today = orderedWeek[i];
                    yesterday = orderedWeek[i-1];

                    newDemand[today] = previousDemand[yesterday].slice(weekLength - offsetAmount).concat(
                        previousDemand[today].slice(0, weekLength - offsetAmount)
                    );
                }

                // 1st day doesn't have a prior week, so it's handled slightly differently
                newDemand[weekStart] = self.arrayOfValues(offsetAmount, 0).concat(
                    previousDemand[weekStart].slice(0, weekLength - offsetAmount)
                );
            }

            return newDemand;
        },
        convertMomentObjToDateStr: function(momentObj) {
            // returns moment object in MM-DD-YYYY
            return momentObj.format("YYYY-MM-DD");
        },
        chooseColor: function(index) {
            var colors = [
                "#48B7AB",  // primary brand
                "#A9CE42",  // a slightly darker logo green
                "#255872",  // a blue
                "#493E45",  // brown
            ];

            return Util.adjustColor(colors[index % colors.length], Math.floor(index / colors.length));
        },
        adjustColor: function(hexColor, magnitude, darken) {
            // magnitude is a factor by which the color code is changed
            // magnitude of 0 produces no change
            // lightens by default, otherwise darkens

            darken = !!darken;

            // must be hex color with a #
            if (hexColor.length != 7) {
                console.log("invalid hex color supplied");
                return false;
            }

            if (magnitude < 1) {
                return hexColor
            }

            var rgb = [
                    parseInt(hexColor.slice(1,3), 16),
                    parseInt(hexColor.slice(3,5), 16),
                    parseInt(hexColor.slice(5,7), 16),
                ],
                scaler,
                i
            ;

            if (darken) {
                scaler = 0.8;
            } else {
                scaler = 1.2;
            }

            for (i=0; i < magnitude; i++) {
                rgb = rgb.map(function(x) {
                    return Math.floor(x * scaler);
                });
            }

            rgb = rgb.map(function(x) {
                if (x > 255) {
                    return 255;
                } else if (x < 0) {
                    return 0;
                } else {
                    return x;
                }
            });

            return "#" + rgb[0].toString(16) + rgb[1].toString(16) + rgb[2].toString(16);
        },
        greyscaleColor: function(hexColor) {
            // converts color to greyscale

            // must be hex color with a #
            if (hexColor.length != 7) {
                console.log("invalid hex color supplied");
                return false;
            }

            var rgb = [
                    parseInt(hexColor.slice(1,3), 16),
                    parseInt(hexColor.slice(3,5), 16),
                    parseInt(hexColor.slice(5,7), 16),
                ],
                average = Math.floor((rgb[0] + rgb[1] + rgb[2])/3),
                hex = average.toString(16)
            ;

            return "#" + hex + hex + hex;
        },
        isEven: function(number) {
            // true if even, false if odd
            return number % 2 == 0;
        },
        formatIntIn12HourTime: function(timeInt, minutes, compact) {
            // takes an int such 13 and returns '1:00 PM'
            // compact mode copies style on Google Calendar. e.g. 7:30 PM is 7:30p

            minutes = minutes || "00";
            compact = !!compact;

            var value = timeInt % 12,
                meridiem,
                compactMeridiem
            ;

            // it's 12, not 0
            if (value == 0) {
                value = 12;
            }

            // AM if int divisor is even
            if (Util.isEven(Math.floor(timeInt / 12))) {
                meridiem = "AM";
                compactMeridiem = "a";
            } else {
                meridiem = "PM";
                compactMeridiem = "p";
            }

            if (compact) {
                if (minutes === "00") {
                    return value + compactMeridiem;
                } else {
                    return value + ":" + minutes + compactMeridiem;
                }
            } else {
                return value + ":" + minutes + " " + meridiem;
            }

        },
        generateFullDayAvailability: function(val) {
            if (!_.isNumber(val)) {
                val = 1;
            }
            var slotsPerDay = 24;

            return {
                "monday": Util.arrayOfValues(slotsPerDay, val),
                "tuesday": Util.arrayOfValues(slotsPerDay, val),
                "wednesday": Util.arrayOfValues(slotsPerDay, val),
                "thursday": Util.arrayOfValues(slotsPerDay, val),
                "friday": Util.arrayOfValues(slotsPerDay, val),
                "saturday": Util.arrayOfValues(slotsPerDay, val),
                "sunday": Util.arrayOfValues(slotsPerDay, val),
            };
        },
        arrayOfValues: function(size, value) {
            // must be numbers
            if (!_.isNumber(size) || _.isNaN(size) || size < 0 ||
                !_.isNumber(value) || _.isNaN(value)) {
                return false;
            }

            // check this out yo
            return Array.apply(null, Array(size)).map(Number.prototype.valueOf, value);
        },
        checkIfArrayOfZeroes: function(list) {
            // true if all 0's (strict type), otherwise false

            for (var i=0; i < list.length; i++) {
                if (list[i] !== 0) {
                    return false;
                }
            }

            return true;
        },
        adjustToDecimalPoint: function(number, decimalPoints, requirePositive, ceiling) {
            if (!_.isNumber(number) || _.isNaN(number)) {
                return 0;
            }

            if (requirePositive && number < 0) {
                return 0;
            }

            if (_.isNumber(ceiling) && !_.isNaN(ceiling)) {
                if (number > ceiling) {
                    return ceiling;
                }
            }

            return parseFloat(number.toFixed(decimalPoints));

        },
        formatMinutesDuration: function(minutes, verbose) {
            if (verbose) {
                var wordTree = {
                    minute: " minutes",
                    hour: " hours",
                }
            } else {
                var wordTree = {
                    minute: "m",
                    hour: "hr",
                }
            }

            if (!_.isNumber(minutes) || _.isNaN(minutes)) {
                return 0;
            }

            var hours = Math.floor(minutes/60),
                result = [];
            minutes = minutes - (hours * 60);

            result.push(hours + wordTree.hour);
            result.push(minutes + wordTree.minute);

            return result.join(" ");
        },
        capitalize: function(string) {
            return string.charAt(0).toUpperCase() + string.slice(1);
        },
        generateConfirmationEmailModalText: function(email) {
            return "<p><strong>" + email + "</strong> has not yet activated their account. You can resend a link by clicking below.</p>";
        },
        momentMobileDisplay: function(momentObj) {
            var hour = momentObj.format("h"),
                minute = momentObj.minute(),
                meridiem = momentObj.format("a"),
                result = hour
            ;

            if (minute > 0) {
                result += ":" + (minute >= 10 ? minute : "0" + minute);
            }

            return result += meridiem;
        }
    };

    root.App.Util = Util;

})(this);
