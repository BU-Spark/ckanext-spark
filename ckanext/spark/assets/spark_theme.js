"use strict";

ckan.module('spark_theme', function ($) {
  return {
    initialize: function () {
      var tabs = $('.tab');
      var tabContents = $('.tab-content');

      // Event listener for tab clicks
      tabs.on('click', function () {
        var tab = $(this);
        var tabContentId = tab.data('tab-content');

        // Hide all tab contents and remove active class from all tabs
        tabContents.hide();
        tabs.removeClass('active');

        // Show the selected tab content and add active class to the clicked tab
        $('#' + tabContentId).show();
        tab.addClass('active');

        console.log('Selected tab:', tabContentId);
      });
    }
  };
});

