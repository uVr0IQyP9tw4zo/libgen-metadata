"use strict";

const options = {}

function loadOptions() {
    options.fields = []
    for (const x in corpus.data) options.fields.push(x);
    options.fields.sort();

    options.searchFields = corpus.options.searchFields || options.fields;
    options.searchFieldsDefault = corpus.options.searchFieldsDefault || options.searchFields;
    options.filterFields = corpus.options.filterFields || [];
    options.displayFields = corpus.options.displayFields || options.fields;
    options.batchedData = !!corpus.options.batchedData;
    options.batchSize = corpus.options.batchSize || (options.batchedData && corpus.data.id && corpus.data.id[0].length) || -999;

    options.displayFieldsVisible = {};
    options.searchFieldsVisible = {};
    options.filterFieldsVisible = {};
    for (const field of options.fields) {
        const display = (corpus.options.fieldsVisible && corpus.options.fieldsVisible[field]) || field;
        options.displayFieldsVisible[field] = (corpus.options.displayFieldsVisible && corpus.options.displayFieldsVisible[field]) || display;
        options.searchFieldsVisible[field] = (corpus.options.searchFieldsVisible && corpus.options.searchFieldsVisible[field]) || display;
        options.filterFieldsVisible[field] = (corpus.options.filterFieldsVisible && corpus.options.filterFieldsVisible[field]) || display;
    }

    options.filters = {};
    options.filtersVisible = {};
    options.defaultFilter = {};
    for (const filterField of options.filterFields) {
        options.filters[filterField] = (corpus.options.filters && corpus.options.filters[filterField]) || [];
        options.filtersVisible[filterField] = {};
        for (const filterOption of options.filters[filterField]) {
            options.filtersVisible[filterField][filterOption] = (corpus.options.filtersVisible && corpus.options.filtersVisible[filterField] && corpus.options.filtersVisible[filterField][filterOption]) || filterOption;
        }
        options.defaultFilter[filterField] = (corpus.options.defaultFilters && corpus.options.defaultFilters[filterField]);
    }
}

function getData(field, i) {
    if (options.batchedData) {
        return corpus.data[field][Math.floor(i/options.batchSize)][i % options.batchSize];
    } else {
        return corpus.data[field][i];
    }
}

// TODO: Show loading bar while searching
// TODO: Allow ordering search results
// TODO: Load all search results, not just 1000, but do it gradually
function search() {
    const loadSearchResults = startLoad("searching");
    const computeResults = startLoad("computing results");
    const form = document.getElementById("search");
    const searchTerm = document.getElementById("q").value; // allow wildcard, regex search
    const formField = document.getElementById("field").value;
    const searchFields = formField == "*" ? options.searchFieldsDefault : [formField];
    const max_results = 1000;
    const searchRegex = RegExp("\\b"+searchTerm+"\\b", 'i');
    let filters = {};
    for (const filterField of options.filterFields) {
        const e = document.getElementById("filter-" + filterField);
        if (e && e.value != "*") filters[filterField] = e.value;
    }

    let results = [];
    for (let i=0; i<corpus.dataLength && results.length<max_results; i++) {
        let found = false;
        let matchFilter = true;
        for (const [filterField, filterValue] of Object.entries(filters)) {
            if (getData(filterField, i) != filterValue) matchFilter = false;
        }
        if (!matchFilter) continue;
        for (const searchField of searchFields) {
            if (searchRegex.test(getData(searchField, i))) {
                found = true;
            }
        }
        if (!found) continue;
        results.push(i);
    }

    stopLoad(computeResults, "computed results");
    const taskDisplayResults = startLoad("displaying results");
    displayResults(results);
    stopLoad(taskDisplayResults, "displayed results");
    stopLoad(loadSearchResults, "search", true);
    return false;
}

function dropdown(id, class_, displayName, selectValues, selectText, defaultValue) {
    const selectLabel = document.createElement("label");
    selectLabel.setAttribute("for", id);
    selectLabel.setAttribute("class", class_);
    selectLabel.appendChild(document.createTextNode(displayName));

    const select = document.createElement("select");
    select.setAttribute("name", id);
    select.setAttribute("id", id);
    select.setAttribute("class", class_);
    const wildcard = document.createElement("option");
    wildcard.setAttribute("value", "*");
    if (typeof defaultValue == 'undefined') wildcard.setAttribute("selected", "true");
    wildcard.appendChild(document.createTextNode("-all-"));
    select.appendChild(wildcard);
    for (const selectValue of selectValues) {
        const displayValue = selectText[selectValue];

        const option = document.createElement("option");
        option.setAttribute("value", selectValue);
        if (defaultValue === selectValue) option.setAttribute("selected", "true");
        option.appendChild(document.createTextNode(displayValue));
        select.appendChild(option);
    }
    return [selectLabel, select];
}

function setupForm() {
    const search_options = document.getElementById("options");
    search_options.innerHTML = '';
    const filter_options = document.getElementById("options");
    filter_options.innerHTML = '';

    // Search fields
    const fieldSelect = dropdown("field", "search-option", "Search in", options.searchFields, options.searchFieldsVisible);
    for (const x of fieldSelect) search_options.appendChild(x);

    // Filters
    for (const filterField of options.filterFields) {
        const filterSelect = dropdown(
            "filter-"+filterField,
            "filter-option",
            options.filterFieldsVisible[filterField],
            options.filters[filterField],
            options.filtersVisible[filterField],
            options.defaultFilter[filterField],
        );
        for (const x of filterSelect) filter_options.appendChild(x);
    }
}

function displayResults(results) {
    const table = document.getElementById("results");
    table.innerHTML = '';
    const header = document.createElement("tr");
    header.setAttribute("class", "header");
    for (const displayField of options.displayFields) {
        const displayFieldText = options.displayFieldsVisible[displayField];

        const colHeader = document.createElement("th");
        colHeader.appendChild(document.createTextNode(displayFieldText));
        header.appendChild(colHeader);
    }
    table.appendChild(header);
    for (const i of results) {
        const row = document.createElement("tr");
        for (const displayField of options.displayFields) {
            const data = getData(displayField, i);

            const cell = document.createElement("td");
            cell.appendChild(document.createTextNode(data));
            row.appendChild(cell);
        }
        table.appendChild(row);
    }
}

function startLoad(part, topLevel) {
    const loadPart = {
        name: part,
        time: Date.now(),
    };
    //const log = document.getElementById("loading-log");
    const active = document.getElementById("loading-active");
    active.innerHTML = part;
    if (topLevel) active.className = "loading";
    return loadPart;
}

function stopLoad(loadPart, name, topLevel) {
    //const log = document.getElementById("loading-log");
    const active = document.getElementById("loading-active");
    const duration = Date.now() - loadPart.time;
    const message = name + " in " + duration + "ms";
    active.innerHTML = message;
    if (topLevel) {
        active.className = "loaded";
        //log.className = "loaded";
        //log.innerHTML += "";
    } else {
        //log.innerHTML += message + "<br/>"
    }
}

const loadAll = startLoad("loading search index");
const loadStrings = startLoad("reading string data");
window.onload = function() {
    stopLoad(loadStrings, "read all string data");
    const parseJSON = startLoad("parsing JSON");
    if (corpus.options.batchedData) {
        for (const field in corpus.data) {
            const loadParse = startLoad('parsing json for: ' + field);
            for (const index in corpus.data[field]) {
                if (typeof corpus.data[field][index] == "string") {
                    corpus.data[field][index] = JSON.parse(corpus.data[field][index]);
                }
            }
            stopLoad(loadParse, "parsed json for: " + field);
            if (corpus.data[field].length == 1) corpus.dataLength = corpus.data[field][0].length;
            else corpus.dataLength = corpus.data[field][0].length * (corpus.data[field].length-1) + corpus.data[field][corpus.data[field].length-1].length;
        }
    } else {
        for (const field in corpus.data) {
            if (typeof corpus.data[field] == "string") {
                const loadParse = startLoad('parsing json for: ' + field);
                corpus.data[field] = JSON.parse(corpus.data[field]);
                stopLoad(loadParse, "parsed json for: " + field);
            }
        }
        corpus.dataLength = corpus.data[field].length;
    }
    stopLoad(parseJSON, "parsed JSON")
    loadOptions();
    stopLoad(loadAll, "loaded search index", true);
    setupForm();
}
