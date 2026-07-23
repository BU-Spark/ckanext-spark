"use strict";

ckan.module('spark_theme', function ($) {
  return {
    initialize: function () {
      var tabs = $('.tab');
      var tabContents = $('.tab-content');

      var defaultTabContentId = 'tab-datasets';
      $('#' + defaultTabContentId).show();

      tabs.on('click', function () {
        var tab = $(this);
        var tabContentId = tab.data('tab-content');

        tabContents.hide();
        tabs.removeClass('active');

        $('#' + tabContentId).show();
        tab.addClass('active');
      });
    }
  };
});
