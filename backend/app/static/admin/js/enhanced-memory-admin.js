/* Enhanced Memory Admin JavaScript */

(function($) {
    'use strict';

    $(document).ready(function() {
        // Add enhanced class to admin body for scoped styling
        $('body.app-couplememory.model-memoryentry').addClass('admin-enhanced-memory-entry');

        // Enhanced action confirmation dialogs
        $('.ai-action-btn').on('click', function(e) {
            const action = $(this).text().trim();
            const entryId = $(this).attr('href').match(/entry_id=(\d+)/);
            
            if (entryId) {
                const confirmed = confirm(`Are you sure you want to ${action.toLowerCase()} for Entry #${entryId[1]}?`);
                if (!confirmed) {
                    e.preventDefault();
                    return false;
                }
            }
        });

        // Add loading state to action buttons
        $('.ai-action-btn').on('click', function() {
            const $btn = $(this);
            const originalText = $btn.text();
            
            $btn.addClass('loading')
                .text('Processing...')
                .prop('disabled', true);
            
            // Reset after 5 seconds in case of no response
            setTimeout(() => {
                $btn.removeClass('loading')
                    .text(originalText)
                    .prop('disabled', false);
            }, 5000);
        });

        // Enhanced tooltips for status indicators
        $('.status-badge').each(function() {
            const $badge = $(this);
            const text = $badge.text().trim();
            
            let tooltip = '';
            if (text.includes('Detailed')) {
                tooltip = 'Full AI analysis with detailed metrics available';
            } else if (text.includes('Basic')) {
                tooltip = 'Only basic AI score available, detailed analysis missing';
            } else if (text.includes('None')) {
                tooltip = 'No AI analysis performed yet';
            }
            
            if (tooltip) {
                $badge.attr('title', tooltip);
            }
        });

        // Auto-refresh functionality for admin actions
        if (window.location.search.includes('ai-action-complete')) {
            setTimeout(() => {
                window.location.replace(window.location.pathname);
            }, 2000);
        }

        // Enhanced search functionality
        const $searchInput = $('#searchbar');
        if ($searchInput.length) {
            $searchInput.attr('placeholder', 'Search by content, author, email, couple code, or recipe...');
        }

        // Collapsible fieldsets enhancement
        $('.collapse h2').on('click', function() {
            const $fieldset = $(this).closest('fieldset');
            const $content = $fieldset.find('.form-row');
            
            $content.slideToggle(200);
            $(this).toggleClass('collapsed');
        });

        // Initialize collapsed state for better UX
        $('.collapse').each(function() {
            const $fieldset = $(this);
            const $content = $fieldset.find('.form-row');
            const $header = $fieldset.find('h2');
            
            if (!$fieldset.hasClass('wide')) {
                $content.hide();
                $header.addClass('collapsed');
            }
        });

        // Enhanced media preview interactions
        $('.media-preview img').on('click', function() {
            const $img = $(this);
            const src = $img.attr('src');
            
            // Create lightbox for full-size viewing
            const $lightbox = $('<div class="image-lightbox">')
                .css({
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    zIndex: 10000,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer'
                })
                .append($('<img>').attr('src', src).css({
                    maxWidth: '90%',
                    maxHeight: '90%',
                    objectFit: 'contain'
                }));
            
            $('body').append($lightbox);
            
            $lightbox.on('click', function() {
                $lightbox.remove();
            });
        });

        // Progress bar animations
        $('.ai-score-fill').each(function() {
            const $fill = $(this);
            const width = $fill.css('width');
            
            $fill.css('width', '0');
            setTimeout(() => {
                $fill.css('width', width);
            }, 100);
        });

        // Form validation enhancements
        $('form').on('submit', function(e) {
            const $form = $(this);
            const $submitBtns = $form.find('input[type="submit"], button[type="submit"]');
            
            $submitBtns.prop('disabled', true).addClass('loading');
            
            // Re-enable after 10 seconds in case of issues
            setTimeout(() => {
                $submitBtns.prop('disabled', false).removeClass('loading');
            }, 10000);
        });

        // Add keyboard shortcuts
        $(document).on('keydown', function(e) {
            // Ctrl/Cmd + R for refresh
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                window.location.reload();
            }
            
            // Escape to close any modals
            if (e.key === 'Escape') {
                $('.image-lightbox').remove();
            }
        });

        // Console log for debugging
        console.log('Enhanced Memory Admin JavaScript initialized');
    });

})(django.jQuery);
