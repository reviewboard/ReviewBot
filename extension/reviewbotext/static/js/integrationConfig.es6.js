$(function() {
    const $tool = $('#id_tool');
    const $toolOptions = $('#row-tool_options');

    /*
     * Until we can update to use the subform support in Review Board 4.0, turn
     * off all client-side validation for the form. This is required because
     * Chrome will still attempt to validate hidden tool options inputs, and
     * fail the form submission.
     *
     * For some reason, using jquery's .prop() doesn't work, so just use the
     * bare DOM API.
     */
    $('#integrationconfig_form')[0].noValidate = true;

    if ($tool.length === 1 && $toolOptions.length === 1) {
        const $itemAboveOptions = $toolOptions.prev();

        function changeToolVisibility() {
            const selectedTool = parseInt($tool.val(), 10);
            let $lastVisibleChild = null;

            $toolOptions.find('.form-row').each((i, el) => {
                const $el = $(el);

                if ($el.data('tool-id') === selectedTool) {
                    $el.show();
                    $lastVisibleChild = $el;
                } else {
                    $el.hide();
                }
            });

            /*
             * Normally, the :last-child rule would hide this border. Instead,
             * we have to override it because the parent has a bunch of other
             * children after the last one that happen to be hidden.
             */
            if ($lastVisibleChild !== null) {
                $lastVisibleChild.css('border-bottom', 0);
                $itemAboveOptions.css('border-bottom', '');
            } else {
                $itemAboveOptions.css('border-bottom', 0);
            }
        }

        $tool.change(() => changeToolVisibility());
        changeToolVisibility();
    }
});
