import os
import csv
import json
import re

# --- PATH CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATA_FILE = os.path.join(PROJECT_ROOT, "data", "02_interim", "openalex_records_deduped.csv")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "search_terms.csv")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "results", "sandbox", "explorer.html")

def build_regexes(query_string):
    """Translates boolean CSV terms into highly permissive JavaScript Regular Expressions."""
    if not query_string: return []
    base = query_string.split(' NOT ')[0].replace('(', '').replace(')', '')
    chunks = [c.strip().replace('"', '') for c in base.split(' OR ')]
    
    regex_list = []
    for c in chunks:
        # 1. Normalize any existing spaces or hyphens into a single space
        clean_c = re.sub(r'[\s\-]+', ' ', c)
        
        # 2. Replace that space with a wildcard that catches spaces, hyphens, en-dashes, em-dashes, or nothing
        # \u2010-\u2015 covers all standard academic typesetting dashes
        pattern = clean_c.replace(' ', r'[\s\-\u2010-\u2015]*')
        
        if pattern.endswith('*'):
            pattern = r"\b" + pattern[:-1] + r"\w*"
        else:
            pattern = r"\b" + pattern + r"\b"
        regex_list.append(pattern)
    return regex_list

def main():
    print("Reading dataset and configuration...")
    records = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    else:
        print(f"Error: Could not find {DATA_FILE}")
        return

    # Determine min/max years in the dataset for the UI placeholders
    all_years = [int(r['publication_year']) for r in records if r.get('publication_year')]
    min_yr = min(all_years) if all_years else 1900
    max_yr = max(all_years) if all_years else 2026

    context_terms = {}
    data_terms = {}
    with open(CONFIG_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'].strip().lower() in ['potential', 'active']:
                term_label = row['term'].strip()
                query_string = row.get('query_string', '') or term_label
                regex_array = build_regexes(query_string)
                if row['list'].strip().lower() == 'context':
                    context_terms[term_label] = regex_array
                else:
                    data_terms[term_label] = regex_array

    print(f"Generating HTML dashboard with Universal Hyphen Detection...")

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>IDS Scoping Review Explorer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/buttons/2.4.1/css/buttons.bootstrap5.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; padding: 20px 0 50px 0; }
        .modal-body { font-size: 1.1em; line-height: 1.6; }
        mark.context-term { background-color: #d4edda; padding: 0.1em; border-radius: 3px; border: 1px solid #c3e6cb; }
        mark.data-term { background-color: #cce5ff; padding: 0.1em; border-radius: 3px; border: 1px solid #b8daff; }
        mark.adhoc-term { background-color: #fff3cd; padding: 0.1em; border-radius: 3px; border: 1px solid #ffeeba; }
        .table-hover tbody tr:hover { cursor: pointer; }
        .count-highlight { font-size: 1.4rem; font-weight: bold; color: #0d6efd; }
    </style>
</head>
<body>

<div class="container-fluid px-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2>Scoping Review Explorer</h2>
        <div class="text-end">
            <span class="text-muted text-uppercase small fw-bold">Showing</span><br>
            <span id="topCounter" class="count-highlight">0</span> 
            <span class="text-muted small">/ RECORDS_COUNT Total</span>
        </div>
    </div>
    
    <div class="card shadow-sm mb-4">
        <div class="card-header bg-white fw-bold text-uppercase small text-muted">Filter Controls</div>
        <div class="card-body">
            <div class="row g-3 mb-3">
                <div class="col-md-3">
                    <label class="form-label text-success fw-bold small">Context Pillar (Title):</label>
                    <select id="contextFilter" class="form-select border-success shadow-sm">
                        <option value="">-- All Context --</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label text-primary fw-bold small">Data Pillar (Title):</label>
                    <select id="dataFilter" class="form-select border-primary shadow-sm">
                        <option value="">-- All Data --</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label fw-bold small">Document Type:</label>
                    <select id="typeFilter" class="form-select shadow-sm">
                        <option value="">-- All Types --</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label fw-bold small">Date Range (Start - End):</label>
                    <div class="input-group shadow-sm">
                        <input type="number" id="startYear" class="form-control" placeholder="MIN_YEAR" value="MIN_YEAR">
                        <span class="input-group-text">to</span>
                        <input type="number" id="endYear" class="form-control" placeholder="MAX_YEAR" value="MAX_YEAR">
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <label class="form-label fw-bold small text-dark">Ad-hoc Search (Title & Abstract):</label>
                    <div class="input-group">
                        <input type="text" id="adhocSearch" class="form-control shadow-sm" placeholder="Enter keywords (e.g., 'RDF ontology')...">
                        <button class="btn btn-outline-secondary" type="button" id="clearAdhoc">Clear</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="card shadow-sm">
        <div class="card-body">
            <table id="recordsTable" class="table table-hover table-striped w-100">
                <thead><tr><th>Year</th><th>Type</th><th>Title</th><th>Authors</th><th>Venue</th><th>Links</th></tr></thead>
            </table>
        </div>
    </div>
</div>

<div class="modal fade" id="abstractModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header bg-dark text-white"><h5 class="modal-title">Paper Details</h5><button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button></div>
      <div class="modal-body">
        <h4 id="mTitle" class="mb-3"></h4>
        <p><strong>Authors:</strong> <span id="mAuthors"></span></p>
        <p><strong>Source:</strong> <span id="mSource"></span> (<span id="mYear"></span>) | <span id="mType"></span></p>
        <hr><h5>Abstract</h5><div id="mAbstract"></div>
      </div>
      <div class="modal-footer">
        <a id="lOA" href="#" target="_blank" class="btn btn-secondary btn-sm">OpenAlex</a>
        <a id="lDOI" href="#" target="_blank" class="btn btn-primary btn-sm">DOI</a>
      </div>
    </div>
  </div>
</div>

<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
<script src="https://cdn.datatables.net/buttons/2.4.1/js/dataTables.buttons.min.js"></script>
<script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.bootstrap5.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.html5.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mark.js/8.11.1/jquery.mark.min.js"></script>

<script>
    const records = JSON_RECORDS;
    const contextTerms = JSON_CONTEXT;
    const dataTerms = JSON_DATA;

    $(document).ready(function() {
        
        [...new Set(records.map(r => r.type))].filter(Boolean).sort().forEach(t => {
            $('#typeFilter').append(new Option(t.toUpperCase(), t));
        });

        function applyHighlights(el, dict, cls) {
            Object.values(dict).forEach(arr => arr.forEach(s => {
                try {
                    el.markRegExp(new RegExp(s, 'gi'), { className: cls });
                } catch(e) {}
            }));
        }

        function applyAdhocHighlight(el) {
            const val = $('#adhocSearch').val().trim();
            if (val.length >= 2) el.mark(val, { className: 'adhoc-term' });
        }

        function updateFilterCounts(currentTable) {
            const filteredData = currentTable.rows({ search: 'applied' }).data().toArray();
            $('#topCounter').text(filteredData.length);

            const updateDropdown = (id, dict) => {
                const select = $(id);
                const currentVal = select.val();
                select.find('option:gt(0)').remove();
                Object.entries(dict).forEach(([label, regexes]) => {
                    const count = filteredData.filter(r => regexes.some(reg => {
                        try { return new RegExp(reg, 'i').test(r.title); } catch(e) { return false; }
                    })).length;
                    if(count > 0 || label === currentVal) select.append(new Option(`${label} (${count})`, label));
                });
                select.val(currentVal);
            };
            updateDropdown('#contextFilter', contextTerms);
            updateDropdown('#dataFilter', dataTerms);
        }

        const table = $('#recordsTable').DataTable({
            data: records,
            pageLength: 100,
            lengthMenu: [[25, 50, 100, -1], [25, 50, 100, "All"]],
            dom: "<'row'<'col-md-4'l><'col-md-4 text-center'B><'col-md-4'f>>t<'row'<'col-md-5'i><'col-md-7'p>>",
            buttons: [{ extend: 'csvHtml5', text: 'Export CSV', className: 'btn btn-sm btn-outline-dark' }],
            columns: [
                { data: 'publication_year', width: '5%' },
                { data: 'type', width: '10%', render: d => (d||"").toUpperCase() },
                { data: 'title', width: '45%' },
                { data: 'authors', width: '15%' },
                { data: 'source', width: '15%' },
                { data: null, width: '10%', render: (d,t,r) => {
                    let l = [];
                    if(r.openalex_id) l.push(`<a href="https://openalex.org/${r.openalex_id}" target="_blank" class="badge bg-secondary text-decoration-none mb-1" onclick="event.stopPropagation()">OpenAlex</a>`);
                    if(r.doi) l.push(`<a href="${r.doi}" target="_blank" class="badge bg-dark text-decoration-none" onclick="event.stopPropagation()">DOI</a>`);
                    return l.join('<br>');
                }}
            ],
            order: [[0, 'desc']],
            drawCallback: function() {
                const body = $('#recordsTable tbody');
                body.unmark();
                applyHighlights(body, contextTerms, 'context-term');
                applyHighlights(body, dataTerms, 'data-term');
                applyAdhocHighlight(body);
                if ($.fn.DataTable.isDataTable('#recordsTable')) {
                    updateFilterCounts($('#recordsTable').DataTable());
                }
            }
        });

        $.fn.dataTable.ext.search.push((settings, data, index, row) => {
            const c = $('#contextFilter').val();
            const d = $('#dataFilter').val();
            const t = $('#typeFilter').val();
            const startY = parseInt($('#startYear').val());
            const endY = parseInt($('#endYear').val());
            const adhoc = $('#adhocSearch').val().toLowerCase().trim();
            
            const yr = parseInt(row.publication_year);
            if (!isNaN(startY) && yr < startY) return false;
            if (!isNaN(endY) && yr > endY) return false;

            if(t && row.type !== t) return false;
            
            const title = (row.title || "").toLowerCase();
            const pillarMatch = (val, dict) => {
                if(!val) return true;
                return dict[val].some(r => {
                    try { return new RegExp(r, 'i').test(title); } catch(e) { return false; }
                });
            };
            if (!pillarMatch(c, contextTerms) || !pillarMatch(d, dataTerms)) return false;

            if (adhoc) {
                const abstract = (row.abstract || "").toLowerCase();
                if (!title.includes(adhoc) && !abstract.includes(adhoc)) return false;
            }
            return true;
        });

        $('#contextFilter, #dataFilter, #typeFilter, #startYear, #endYear').on('change keyup', () => table.draw());
        $('#adhocSearch').on('keyup', () => table.draw());
        $('#clearAdhoc').on('click', () => { $('#adhocSearch').val(''); table.draw(); });

        $('#recordsTable tbody').on('click', 'tr', function() {
            const d = table.row(this).data();
            if(!d) return;
            $('#mTitle').text(d.title); $('#mAuthors').text(d.authors); $('#mSource').text(d.source); $('#mYear').text(d.publication_year);
            $('#mType').text((d.type || "").toUpperCase()); $('#mAbstract').text(d.abstract || "No abstract.");
            d.doi ? $('#lDOI').attr('href', d.doi).show() : $('#lDOI').hide();
            $('#lOA').attr('href', "https://openalex.org/" + d.openalex_id);
            const abs = $('#mAbstract'), tit = $('#mTitle');
            abs.unmark(); tit.unmark();
            applyHighlights(abs, contextTerms, 'context-term'); applyHighlights(abs, dataTerms, 'data-term');
            applyAdhocHighlight(abs);
            applyHighlights(tit, contextTerms, 'context-term'); applyHighlights(tit, dataTerms, 'data-term');
            applyAdhocHighlight(tit);
            $('#abstractModal').modal('show');
        });
    });
</script>
</body>
</html>
"""

    final_html = html_template.replace('RECORDS_COUNT', str(len(records)))
    final_html = final_html.replace('JSON_RECORDS', json.dumps(records))
    final_html = final_html.replace('JSON_CONTEXT', json.dumps(context_terms))
    final_html = final_html.replace('JSON_DATA', json.dumps(data_terms))
    final_html = final_html.replace('MIN_YEAR', str(min_yr))
    final_html = final_html.replace('MAX_YEAR', str(max_yr))

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f"Dashboard updated with Universal Hyphen Support at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()