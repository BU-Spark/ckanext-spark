ckan.module('index_navigation_tabs', function ($) {
  return {
    initialize: function () {
      // Hide all tab content
      var tabContents = $('.tab-content');
      tabContents.hide();

      // Remove active class from all tabs
      var tabs = $('.tab');
      tabs.removeClass('active');

      // Show the selected tab content and add active class
      var selectedTab = $('#' + this.el.attr('data-tab'));
      if (selectedTab.length) {
        selectedTab.show();
        selectedTab.addClass('active');
      }
    }
  };
});

