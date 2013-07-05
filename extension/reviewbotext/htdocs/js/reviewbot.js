// Trigger the ReviewBot tools lightbox when clicking on the ReviewBot link
//  in the nav bar.

var dlg, dlgContentTable, dlgContentTBody, modal;

$("#reviewbot-link").click(function() {
    $.fetchReviewBotTools();
});

$.fetchReviewBotTools = function() {
    RB.apiCall({
        type: "GET",
        dataType: "json",
        data: {},
        url: "/api/extensions/reviewbotext.extension.ReviewBotExtension/review-bot-tools/",
        success: function(response) {
            if (!dlg) {
                $.createToolLightBox();
            }
            $.showToolLightBox(response);
        }
    });
}

$.createToolLightBox = function() {
    modal = {
        title: "Review Bot",
    };

    dlg = $("<div/>")
        .attr("id", "reviewbot-tool-dialog")
        .attr("class", "modalbox-contents")
        .appendTo("body")

    dlg.append(
        $("<p/>")
            .attr("id", "reviewbot-tool-description")
            .html("Select the static analysis tools you would like to run."));

    dlgContentTable = $("<table/>")
        .appendTo(dlg)
        .append($("<colgroup/>")
            .append('<col/>'));

    dlgContentTBody = $("<tbody/>")
        .appendTo(dlgContentTable);

    /*
     * Add all new content to the dialog here.
     */

    // Content of Installed Tools generated dynamically later.
    $.addSection("reviewbot-installed-tools", "Installed Tools");
}

/*
 * Add a section to the Review Bot tools dialog.
 *
 * Content to the section can be added elsewhere using the content_id.
 */
$.addSection = function(content_id, subtitle) {
    dlgContentTBody
        .append($("<tr/>")
            .append(
                $("<td/>")
                    .html(
                        $("<span class='reviewbot-tool-dialog-subtitle'/>")
                            .html(subtitle))))
        .append($("<tr/>")
            .append(
                $("<td/>")
                    .html($("<div/>")
                        .attr("id", content_id))));
}

$.showToolLightBox = function(response) {
    // Display list of installed tools.
    // Later on more data can be handled and displayed here.
    var tools = response["review_bot_tools"];
    var toolList = $("<ul/>")
        .attr("id", "reviewbot-tool-list");

    $.each(tools, function(index, tool){
        if (tool["enabled"] && tool["allow_run_manually"]) {
            toolList.append(
                $("<li/>")
                    .append($('<input type="checkbox"/>')
                        .attr("id", "reviewbot-tool-checkbox_" + index)
                        .attr("class", "toolCheckbox")
                        .attr("checked", "checked")
                        .prop("tool_id", tool["id"])
                        .change(function() {
                            var allChecked =
                                ($(".toolCheckbox:checked").length > 0);
                            $("#button_run").attr("disabled", !allChecked);
                        }))
                    .append($("<label/>")
                        .attr("for", "reviewbot-tool-checkbox_" + index)
                        .html(tool["name"] + " " + tool["version"]))
            );
        }
    });

    // Re-append dlg to body since closing the modalbox removes it.
    dlg.appendTo("body");

    if (toolList.children().length > 0) {
        $("#reviewbot-installed-tools").html(toolList);

        modal.buttons = [
            $('<input id="button_cancel" type="button" value="Cancel"/>'),
            $('<input id="button_run" type="button"/>')
                .val("Run Tools")
                .click(function(e){
                    $.runSelectedTools($(".toolCheckbox:checked"));
                }),
        ];
    } else {
        // If no tools were loaded, display message.
        $("#reviewbot-installed-tools")
            .html("No tools available to run manually.");

        modal.buttons = [
            $('<input id="button_ok" type="button" value="OK"/>'),
        ];
    }
    dlg.modalBox(modal);
}

$.runSelectedTools = function(selectedTools){
    var tools = [];

    $.each(selectedTools, function(index, selectedTool){
        tools.push(
            { id : $(selectedTool).prop("tool_id") }
        );
    });

    request_payload = {
        review_request_id: gReviewRequestId,
        tools : JSON.stringify(tools),
    }

    RB.apiCall({
        type: "POST",
        dataType: "json",
        data: request_payload,
        url: "/api/extensions/reviewbotext.extension.ReviewBotExtension/review-bot-trigger-reviews/",
        success: function(response) {
            alert(response);
        }
    });
}