// Per-question editor scripts for type changes and option management.
(function() {
    var lastTypeValues = {};
    var POLL_INTERVAL_MS = 500;

    function mapDisplayToType(text) {
        if (!text) return '';
        var t = text.toLowerCase();
        if (t.indexOf('checkbox') === 0 || t === 'checkall') return 'checkbox';
        if (t.indexOf('likert') === 0) return 'likert';
        if (t.indexOf('yes') === 0 || t.indexOf('no') === 0) return 'yesno';
        if (t.indexOf('numeric') === 0 || t.indexOf('nps') === 0) return 'numeric_scale';
        if (t.indexOf('text') === 0 || t.indexOf('open-ended') === 0) return 'text';
        if (t.indexOf('ranking') === 0) return 'ranking';
        if (t.indexOf('multi-select') === 0 || t.indexOf('multiselect') === 0) return 'multiselect';
        if (t.indexOf('matrix') === 0 || t.indexOf('grid') === 0) return 'matrix';
        return text.toLowerCase();
    }

    function handleTypeChange(fp, newType) {
        var scaleDiv = document.getElementById(fp + 'scale_editor_div');
        var matrixDiv = document.getElementById(fp + 'matrix_editor_div');
        if (scaleDiv) scaleDiv.innerHTML = '';
        if (matrixDiv) matrixDiv.innerHTML = '';

        if (newType === 'checkbox' || newType === 'multiselect' || newType === 'ranking') {
            var opts = [];
            for (var i = 0; i < 15; i++) {
                var inp = document.getElementById(fp + 'opt_' + i);
                if (inp) opts.push(inp.value || '');
            }
            if (!opts.some(function(o) { return o.length > 0; })) opts = [''];

            var h = '';
            opts.forEach(function(opt, i) {
                h += '<div style="display:flex;align-items:center;marginBottom:4px">' +
                    '<input id="' + fp + 'opt_' + i + '" type="text" value="' + opt.replace(/"/g, '&quot;') +
                    '" placeholder="Option ' + (i+1) + '" style="width:70%;marginRight:5px">' +
                    '<button class="qm-del-opt" id="' + fp + 'del_opt_' + i + '">\u2715</button></div>';
            });
            h += '<button id="' + fp + 'add_opt" class="qm-add-opt">+ Add Option</button>';

            var optsDiv = document.getElementById(fp + 'options_list');
            if (optsDiv) {
                optsDiv.innerHTML = h;
            }
        }
    }

    function readAllTypeDropdowns() {
        var dropdowns = document.querySelectorAll('[id^="q_"][id$="_type"]');
        for (var i = 0; i < dropdowns.length; i++) {
            var el = dropdowns[i];
            var idMatch = el.id.match(/^(q_\d+)_type$/);
            if (!idMatch) continue;
            var fp = idMatch[1] + '_';

            var valueEl = document.getElementById(el.id + '-value');
            var currentDisplay = '';
            if (valueEl) currentDisplay = valueEl.textContent.trim();
            var mappedType = mapDisplayToType(currentDisplay);

            if (lastTypeValues[fp] !== mappedType) {
                lastTypeValues[fp] = mappedType;
                handleTypeChange(fp, mappedType);
            }
        }
    }

    document.addEventListener('click', function(e) {
        var btn = e.target;
        if (!btn || !(btn.classList.contains('qm-add-opt') || btn.classList.contains('qm-del-opt'))) return;

        // Find the options_list container that contains this button
        var optsContainer = null;
        var allOptsLists = document.querySelectorAll('[id^="q_"][id$="_options_list"]');
        for (var i = 0; i < allOptsLists.length; i++) {
            if (allOptsLists[i].contains(btn)) {
                optsContainer = allOptsLists[i];
                break;
            }
        }

        // Fallback: walk up parent chain
        if (!optsContainer) {
            var cur = btn.parentElement;
            while (cur && cur !== document.body) {
                if (cur.id && /^q_\d+_options_list$/.test(cur.id)) {
                    optsContainer = cur;
                    break;
                }
                cur = cur.parentElement;
            }
        }

        if (!optsContainer) return;

        var fpMatch = optsContainer.id.match(/^(q_\d+)_options_list$/);
        if (!fpMatch) return;
        var fp = fpMatch[1] + '_';

        if (btn.classList.contains('qm-add-opt')) {
            // Read all current option values and append a new empty option
            var opts = [];
            for (var i = 0; i < 20; i++) {
                var inp = document.getElementById(fp + 'opt_' + i);
                if (inp) opts.push(inp.value || '');
            }
            opts.push('');

            var h = '';
            opts.forEach(function(opt, i) {
                h += '<div style="display:flex;align-items:center;marginBottom:4px">' +
                    '<input id="' + fp + 'opt_' + i + '" type="text" value="' + opt.replace(/"/g, '&quot;') +
                    '" placeholder="Option ' + (i+1) + '" style="width:70%;marginRight:5px">' +
                    '<button class="qm-del-opt" id="' + fp + 'del_opt_' + i + '">\u2715</button></div>';
            });
            h += '<button id="' + fp + 'add_opt" class="qm-add-opt">+ Add Option</button>';
            optsContainer.innerHTML = h;
        } else if (btn.classList.contains('qm-del-opt')) {
            var m = btn.id.match(/^q_\d+_del_opt_(\d+)$/);
            if (!m) return;
            var delIdx = parseInt(m[1]);

            var opts = [];
            for (var i = 0; i < 20; i++) {
                if (i === delIdx) continue;
                var inp = document.getElementById(fp + 'opt_' + i);
                if (inp) opts.push(inp.value || '');
            }

            var h = '';
            opts.forEach(function(opt, i) {
                h += '<div style="display:flex;align-items:center;marginBottom:4px">' +
                    '<input id="' + fp + 'opt_' + i + '" type="text" value="' + opt.replace(/"/g, '&quot;') +
                    '" placeholder="Option ' + (i+1) + '" style="width:70%;marginRight:5px">' +
                    '<button class="qm-del-opt" id="' + fp + 'del_opt_' + i + '">\u2715</button></div>';
            });
            h += '<button id="' + fp + 'add_opt" class="qm-add-opt">+ Add Option</button>';
            optsContainer.innerHTML = h;
        }
    });

    setTimeout(readAllTypeDropdowns, 1500);
    setInterval(readAllTypeDropdowns, POLL_INTERVAL_MS);
})();
