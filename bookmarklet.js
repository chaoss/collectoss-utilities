// Usage: 
// 1. Copy everything below this comment
// 2. paste into https://caiorss.github.io/bookmarklet-maker/
// 3. copy the contents of the "output" box
// 4. create a new bookmark in your browser, named whatever you want, and paste that output in the url box
// to use: view a task page in flower and click your bookmark to open a new issue on the target repo
(function () {
    // Helper to find text within table rows or definition lists dynamically
    function getVal(labels) {
        var rows = document.querySelectorAll('tr');
        for (var i = 0; i < rows.length; i++) {
            var r = rows[i];
            if (r.cells && r.cells.length >= 2) {
                var lbl = r.cells[0].textContent.trim().toLowerCase();
                for (var j = 0; j < labels.length; j++) {
                    if (lbl.indexOf(labels[j]) !== -1) return r.cells[1].textContent.trim();
                }
            }
        }
        var dts = document.querySelectorAll('dt');
        for (var k = 0; k < dts.length; k++) {
            var dt = dts[k];
            var dtLbl = dt.textContent.trim().toLowerCase();
            for (var m = 0; m < labels.length; m++) {
                if (dtLbl.indexOf(labels[m]) !== -1 && dt.nextElementSibling) {
                    return dt.nextElementSibling.textContent.trim();
                }
            }
        }
        return '';
    }

    // Extract fields
    var name = getVal(['name', 'task name']);
    var uuid = getVal(['uuid', 'task id', 'id']);
    var args = getVal(['args', 'arguments']);
    var kwargs = getVal(['kwargs', 'keyword arguments']);
    var exception = getVal(['exception', 'error']);

    // Attempt to grab traceback from text matching or fallback to pre tags
    var traceback = getVal(['traceback', 'stacktrace', 'stack trace']);
    if (!traceback) {
        var preTags = document.querySelectorAll('pre');
        for (var p = 0; p < preTags.length; p++) {
            if (preTags[p].textContent.toLowerCase().indexOf('traceback (most recent call last)') !== -1) {
                traceback = preTags[p].textContent.trim();
                break;
            }
        }
    }

    // Stop if no valid data was found
    if (!name && !exception && !traceback) {
        alert("Could not detect any Flower task data. Please make sure you click into an individual task's details page (e.g., /task/<uuid>).");
        return;
    }

    // Persist your GitHub repo path
    var repo = localStorage.getItem('flower_github_repo') || 'your-organization/your-repo';
    repo = prompt('Enter target GitHub repository (owner/repository):', repo);
    if (!repo || repo === 'your-organization/your-repo') {
        alert('A valid GitHub repository path is required.');
        return;
    }
    localStorage.setItem('flower_github_repo', repo);

    // Formulate the full Markdown payload for clipboard copy
    var fullMarkdown = [

        "### Task Details",
        "- **Task Name:** `" + (name || 'N/A') + "`",
        "- **Task ID:** `" + (uuid || 'N/A') + "`",
        "- **Arguments:** `" + (args || 'N/A') + "`",
        "- **Keyword Args:** `" + (kwargs || 'N/A') + "`",
        "",
        "### Exception",
        "```",
        exception || 'No exception message found.',
        "```",
        "",
        "<details>",
        "<summary>Stack Trace</summary>",
        "",
        "```python",
        traceback || 'No traceback found.',
        "```",
        "",
        "</details>"
    ].join('\n');

    // Copy to clipboard execution
    try {
        navigator.clipboard.writeText(fullMarkdown);
    } catch (e) { }

    // Safeguard URL truncation limit (~4000 characters to prevent 414 Request-URI Too Long errors)
    var urlTraceback = traceback || 'No traceback found.';
    var limitNote = '';
    var baseUrl = "https://github.com/" + repo + "/issues/new";
    var issueTitle = "[Celery Failure] " + (name || 'Task Error') + ": " + (exception ? exception.split('\n')[0] : 'Unknown error');

    var baseStructureLength = 1000; // rough character buffer for structural texts
    if (baseStructureLength + urlTraceback.length > 4000) {
        limitNote = "\n\n⚠️ **Note:** The traceback was truncated due to browser URL length limits. The COMPLETE logs have been copied to your clipboard! Paste (Ctrl+V / Cmd+V) to overwrite this section.";
        var safeLength = 4000 - baseStructureLength - limitNote.length;
        urlTraceback = urlTraceback.substring(0, Math.max(0, safeLength)) + "\n... [Truncated for URL size] ...";
    }

    var finalUrlBody = [
        "### Task Details",
        "- **Task Name:** `" + (name || 'N/A') + "`",
        "- **Task ID:** `" + (uuid || 'N/A') + "`",
        "- **Arguments:** `" + (args || 'N/A') + "`",
        "- **Keyword Args:** `" + (kwargs || 'N/A') + "`",
        "",
        "```",
        exception || 'No exception message found.',
        "```",
        "",
        "<details>",
        "<summary>Stack Trace</summary>",
        "",
        "```python",
        urlTraceback,
        "```",
        "",
        "</details>",
        limitNote
    ].join('\n');

    window.open(baseUrl + "?title=" + encodeURIComponent(issueTitle) + "&body=" + encodeURIComponent(finalUrlBody), '_blank');
})();