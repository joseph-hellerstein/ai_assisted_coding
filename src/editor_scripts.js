// Per-question editor scripts for type changes and option management.
// These are injected as html.Script components in render_question_editor().
(function() {
    var el = document.getElementById("__FP__type");
    if (!el) return;
    el.addEventListener("change", function() {
        var n = this.value, f = "__FP__";
        // Clear dependent editor sections
        var oDiv = document.getElementById(f + "options_list");
        var sDiv = document.getElementById(f + "scale_editor_div");
        var mDiv = document.getElementById(f + "matrix_editor_div");
        if (oDiv) oDiv.innerHTML = '';
        if (sDiv) sDiv.innerHTML = '';
        if (mDiv) mDiv.innerHTML = '';

        // Show options editor for checkbox/multiselect/ranking types
        if (n === "checkbox" || n === "multiselect" || n === "ranking") {
            var opts = [];
            for (var i = 0; i < 15; i++) {
                var inp = document.getElementById(f + "opt_" + i);
                if (inp) opts.push(inp.value || '');
            }
            if (!opts.some(function(o) { return o.length > 0; })) opts = [''];

            var h = '';
            opts.forEach(function(opt, i) {
                h += '<div style="display:flex;align-items:center;marginBottom:4px">' +
                    '<input id="' + f + 'opt_' + i + '" type="text" value="' + opt +
                    '" placeholder="Option ' + (i+1) + '" style="width:70%;marginRight:5px">' +
                    '<button id="' + f + 'del_opt_' + i + '" class="qm-del-opt">\u2715</button></div>';
            });
            h += '<button id="' + f + 'add_opt" class="qm-add-opt">+ Add Option</button>';
            if (oDiv) oDiv.innerHTML = h;
        }
    });
})();
