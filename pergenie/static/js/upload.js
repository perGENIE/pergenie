var updateStatus = function () {
    $.getJSON(window.upload_status_url, function (response) {
    var isAllFileImported = true;
    var importCompletedFiles = [];
    var importCompletedFilesStatus = {};

    $.each($(".genome_info"), function () {
        var row = $(this);
        var genome_id = $(".genome_id", row).text();

        if (genome_id in response.genome_info) {
            var status = parseInt(response.genome_info[genome_id]);
            var bar = $(".bar", row);

            bar.css("width", "" + status + "%");

            if (status >= 100 || status == -1) {
                var barContainer = bar.parent();

                if (barContainer.hasClass("active"))
                    importCompletedFiles.push(barContainer);
                    importCompletedFilesStatus[barContainer] = status;
            }

            else {
                isAllFileImported = false;
            }
        }
    }); // $.each

    //
    if (!isAllFileImported) setTimeout("updateStatus()", 1000);

    //
    setTimeout(function () {
        $.each(importCompletedFiles, function () {
            var barContainer = this;
            barContainer
                .removeClass("active")
                .removeClass("progress-striped")
                .removeClass("progress-info")
                .removeClass("progress")
            var bar = $(".bar", barContainer);
            var status = importCompletedFilesStatus[this];
            if (status == -1) {
                bar.replaceWith('<span class="badge badge-red">failed</span>');
            } else {
                bar.replaceWith('<span class="badge badge-green">ok</span>');
            }
        });
    }, 1000);
    }); // $.getJSON
};

$(document).ready(function () {
    updateStatus();
});
