(function ($) {

    $.anchorButton = function (element, options) {

        var defaults = {
            activeColors: '#fff',
            titles: [],
            data: [],
            goals: [],
            types: []
        }

        var activeTextColor = '#EBEBEB'; 
        var activeTextColorHover = '#FFF';

        var inactiveColor = '#FAFAFA';
        var inactiveTextColor = '#888';
        var inactiveTextColorHover = '#000';
        var plugin = this;

        plugin.settings = {}

        var $element = $(element),
             element = element;

        plugin.init = function () {
            plugin.settings = $.extend({}, defaults, options);

            $.each(plugin.settings.titles, function (index, value) {
                var btn = document.createElement('a');
                //$(btn).attr('id', value + "." + plugin.settings.activeColors[index].substring(1, 7));
                $(btn).html(value).addClass('list-group-item inactive');
                $(btn).css('background-color', inactiveColor);
                $(btn).css('color', inactiveTextColor);
                $(btn).attr('title', 'Click to see your graph');
                $(btn).click(function () {
                    if ($(this).hasClass('active')) {
                        $(this).html(value).removeClass('active').addClass('inactive');
                        $(this).css('color', inactiveTextColor);
                        btn.style.backgroundColor = inactiveColor;
                        eraseGraph(value, plugin.settings.data[index]);  
                    } else {
                        $(this).html(value).removeClass('inactive').addClass('active');
                        $(this).css('color', activeTextColor);
                        btn.style.backgroundColor = plugin.settings.activeColors[index];
                        drawGraph(value, 
                        		  plugin.settings.activeColors[index], 
                        		  plugin.settings.data[index],
                        		  plugin.settings.goals[index],
                        		  plugin.settings.types[index]);
                    }
                });

                $(btn).mouseover(function () {
                    $(this).css('cursor', 'pointer');
                    if ($(this).hasClass('active')) {
                        $(this).css('color', activeTextColorHover);
                    } else {
                        $(this).css('color', inactiveTextColorHover);
                    }
                });
                $(btn).mouseout(function () {
                    $(this).css('cursor', 'default');
                    if ($(this).hasClass('active')) {
                        $(this).css('color', activeTextColor);
                    } else {
                        $(this).css('color', inactiveTextColor);
                        $(this).css('background-color', inactiveColor);
                    }
                });
                $element.append(btn);
            });
        }
        plugin.init();

    }

    $.fn.anchorButton = function (options) {

        return this.each(function () {
            if (undefined == $(this).data('anchorButton')) {
                var plugin = new $.anchorButton(this, options);
                $(this).data('anchorButton', plugin);
            }
        });

    }

})(jQuery);

